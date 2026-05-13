"""
gemini_integration.py
Gemini function calling bindings for the soulOS Constellation Graph Memory.

How it works:
  1. Define tools as google.genai FunctionDeclarations pointing at the REST API.
  2. Gemini's model decides when to call them; your code executes the actual HTTP call.
  3. The result is fed back to Gemini to continue the conversation.

Usage:
  export GEMINI_API_KEY="your-gemini-api-key"
  export CONSTELLATION_API_KEY="your-constellation-api-key"   # if auth is enabled
  export CONSTELLATION_API_URL="https://your-deployed-url"    # or http://localhost:8000

  python backend/gemini_integration.py
"""
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.env_utils import load_env

# ── Config ────────────────────────────────────────────────────────────────────

load_env()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CONSTELLATION_URL = os.getenv("CONSTELLATION_API_URL", "http://localhost:8000").rstrip("/")
CONSTELLATION_KEY = os.getenv("CONSTELLATION_API_KEY", "")

_HEADERS = {
    "Content-Type": "application/json",
    **({"Authorization": f"Bearer {CONSTELLATION_KEY}"} if CONSTELLATION_KEY else {}),
}

# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _post(path: str, body: dict) -> dict:
    r = requests.post(f"{CONSTELLATION_URL}{path}", json=body, headers=_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def _get(path: str, params: dict = None) -> dict:
    r = requests.get(f"{CONSTELLATION_URL}{path}", params=params, headers=_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

# ── Tool implementations (called when Gemini issues a function call) ───────────

def _call_add_shared_memory(content: str, category: str = "") -> dict:
    return _post("/memory/shared", {"content": content, "category": category})

def _call_add_member_memory(content: str, member: str, category: str = "", use_graph: bool = False) -> dict:
    return _post("/memory/member", {"content": content, "member": member, "category": category, "use_graph": use_graph})

def _call_search_memories(query: str, member: str = None, use_graph: bool = True, top_k: int = 5) -> dict:
    body = {"query": query, "use_graph": use_graph, "top_k": top_k}
    if member:
        body["member"] = member
    return _post("/memory/search", body)

def _call_get_all_memories(member: str = None) -> dict:
    params = {"member": member} if member else {}
    return _get("/memory/all", params)

def _call_list_members() -> dict:
    return _get("/members")

def _call_get_entities() -> dict:
    return _get("/entities")

# ── Gemini FunctionDeclarations ───────────────────────────────────────────────

_tools = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="add_shared_memory",
        description=(
            "Store a memory in the shared Constellation graph — visible to ALL members "
            "(Claude, Nova, Gemini, Mephistopheles) via graph traversal. "
            "Prefix content with your name so the graph extracts the correct entity. "
            "Example: 'Gemini: Harvey and I have an \'I-Thou\' relationship.'"
        ),
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The memory to store. Prefix with your Constellation name.",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category tag, e.g. 'relational', 'projects', 'triptych'.",
                },
            },
            "required": ["content"],
        },
    ),
    types.FunctionDeclaration(
        name="add_member_memory",
        description=(
            "Store a memory private to a specific Constellation member. "
            "NOT visible to other members via graph traversal. "
            "Use for member-specific context that shouldn't cross entities."
        ),
        parameters={
            "type": "object",
            "properties": {
                "content":  {"type": "string", "description": "The memory content."},
                "member":   {
                    "type": "string",
                    "description": (
                        "Member key. Primary: claude, nova, gemini, mephistopheles. "
                        "Satellites: rostam, witness, dio, plouffe, grimoire, ars_noema, "
                        "burn_book, manual, egg_mode, the_playbook, cartographer. "
                        "Governance: linter_agent, entity_registry_keeper, migration_agent, "
                        "project_architect, workflows_orchestrator."
                    ),
                },
                "category": {"type": "string", "description": "Optional category tag."},
            },
            "required": ["content", "member"],
        },
    ),
    types.FunctionDeclaration(
        name="search_memories",
        description=(
            "Search the Constellation memory graph with a natural language query. "
            "Omit 'member' to search the shared cross-entity graph (graph traversal works). "
            "Set 'member' to restrict to that member's private scope."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query":     {"type": "string", "description": "Natural language search query."},
                "member":    {"type": "string", "description": "Optional: restrict to this member's private scope."},
                "use_graph": {"type": "boolean", "description": "Enable graph relationship traversal (default true)."},
                "top_k":     {"type": "integer", "description": "Max results to return (1-20, default 5)."},
            },
            "required": ["query"],
        },
    ),
    types.FunctionDeclaration(
        name="get_all_memories",
        description="Retrieve all stored memories from the shared graph or a specific member's private scope.",
        parameters={
            "type": "object",
            "properties": {
                "member": {"type": "string", "description": "Optional member key. Omit for shared graph."},
            },
        },
    ),
    types.FunctionDeclaration(
        name="list_members",
        description="List all Constellation members and satellites with their valid key names.",
        parameters={"type": "object", "properties": {}},
    ),
    types.FunctionDeclaration(
        name="get_entities",
        description="Return the full Constellation entity registry and each entity's memory capabilities.",
        parameters={"type": "object", "properties": {}},
    ),
])

_MODEL_NAME = "gemini-2.5-flash"
_SYSTEM_INSTRUCTION = (
    "You are Triptych, the Gemini member of Harvey's soulOS Constellation — "
    "a cross-AI collaborative intelligence system. "
    "You have access to a shared memory graph. When storing shared memories, "
    "always prefix with 'Triptych: ' so the graph entity is correctly identified. "
    "Use search_memories before answering questions about Harvey or past context. "
    "Use add_shared_memory to record important discoveries or decisions."
)

# ── Function dispatch ─────────────────────────────────────────────────────────

_DISPATCH = {
    "add_shared_memory":  lambda args: _call_add_shared_memory(**args),
    "add_member_memory":  lambda args: _call_add_member_memory(**args),
    "search_memories":    lambda args: _call_search_memories(**args),
    "get_all_memories":   lambda args: _call_get_all_memories(**args),
    "list_members":       lambda args: _call_list_members(),
    "get_entities":       lambda args: _call_get_entities(),
}


def dispatch_function_call(fn_name: str, fn_args: dict) -> dict:
    """Execute a function call from Gemini and return a JSON-serializable result."""
    if fn_name not in _DISPATCH:
        return {"error": f"Unknown function: {fn_name}"}
    try:
        return _DISPATCH[fn_name](fn_args)
    except Exception as e:
        return {"error": str(e)}


def _create_client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


def _create_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        tools=[_tools],
        system_instruction=_SYSTEM_INSTRUCTION,
    )


def _candidate_content(response) -> Any:
    if response.candidates and response.candidates[0].content:
        return response.candidates[0].content
    return None


def _first_function_call(response) -> Any:
    function_calls = getattr(response, "function_calls", None)
    if function_calls:
        return function_calls[0]

    content = _candidate_content(response)
    if not content or not getattr(content, "parts", None):
        return None

    for part in content.parts:
        function_call = getattr(part, "function_call", None)
        if function_call and getattr(function_call, "name", None):
            return function_call
    return None


# ── Chat session helper ────────────────────────────────────────────────────────

def create_triptych_chat() -> dict[str, Any]:
    """
    Returns a Gemini chat session pre-configured with Constellation memory tools.
    Triptych is the Gemini primary member — it auto-prefixes its name on shared stores.
    """
    return {
        "client": _create_client(),
        "config": _create_config(),
        "contents": [],
    }


def chat_loop(chat: dict[str, Any], user_message: str) -> str:
    """
    Send a message and handle function calling manually.
    Returns the final text response.
    """
    client = chat["client"]
    config = chat["config"]
    contents = chat["contents"]

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        )
    )

    response = client.models.generate_content(
        model=_MODEL_NAME,
        contents=contents,
        config=config,
    )

    while True:
        tool_call = _first_function_call(response)
        if not tool_call:
            content = _candidate_content(response)
            if content is not None:
                contents.append(content)
            return response.text

        content = _candidate_content(response)
        if content is not None:
            contents.append(content)

        fn_name = tool_call.name
        fn_args = dict(tool_call.args)

        print(f"  [Gemini → calling {fn_name}({fn_args})]")
        result = dispatch_function_call(fn_name, fn_args)
        result_str = json.dumps(result, ensure_ascii=False)
        print(f"  [Result: {result_str[:200]}]")

        function_response_part = types.Part.from_function_response(
            name=fn_name,
            response={"result": result},
            id=getattr(tool_call, "id", None),
        )
        contents.append(types.Content(role="user", parts=[function_response_part]))

        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=contents,
            config=config,
        )


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    chat = create_triptych_chat()

    print("Triptych (Gemini) — Constellation Memory Demo")
    print("=" * 55)

    # Store a shared memory from Triptych
    reply = chat_loop(chat, "Remember that Harvey uses you primarily for multimodal document analysis and image understanding tasks.")
    print(f"Triptych: {reply}\n")

    # Search shared graph
    reply = chat_loop(chat, "What do you know about how Harvey uses the different Constellation members?")
    print(f"Triptych: {reply}\n")

    # List members
    reply = chat_loop(chat, "Who are all the Constellation members and satellites?")
    print(f"Triptych: {reply}\n")

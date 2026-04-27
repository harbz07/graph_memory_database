"""
api_server.py
FastAPI REST server for the soulOS Constellation Graph Memory.
Serves BOTH:
  - ChatGPT GPT Actions  (OpenAPI spec auto-generated at /openapi.json)
  - Gemini function calls (same endpoints, see gemini_integration.py for bindings)

DEPLOYMENT NOTE:
  GPT Actions and Gemini need a publicly accessible URL.
  For local testing: use `ngrok http 8000` and paste the ngrok URL into GPT Action config.
  For production:    deploy to Railway, Render, Fly.io, or any VPS.

Auth:
  Set CONSTELLATION_API_KEY env var. Pass it as Bearer token in Authorization header.
  GPT Action config → Authentication → API Key → Bearer.
  Leave CONSTELLATION_API_KEY empty to disable auth (local testing only).

Run:
  python backend/api_server.py
  # or: uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
"""
import os
import sys
from pathlib import Path
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.env_utils import load_env
from backend.entity_registry import MEMORY_CAPABLE_ENTITIES, SHARED_WRITE_ENTITIES, get_entity_registry
from backend.memory_core import (
    MEMBER_HIERARCHY,
    add_member_memory,
    add_shared_memory,
    get_all_memories,
    search_memories,
)

load_env()

# ── App ───────────────────────────────────────────────────────────────────────

_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]
if not _ALLOWED_ORIGINS:
    _ALLOWED_ORIGINS = ["*"]
_MAX_BATCH_SIZE = int(os.getenv("CONSTELLATION_MAX_BATCH_SIZE", "100"))

app = FastAPI(
    title="Constellation Graph Memory",
    description=(
        "Cross-AI shared memory graph for the soulOS Constellation. "
        "Members: Claude (Anthropic), Nova (OpenAI), Gemini (Google), "
        "Mephistopheles (DeepSeek). All share user_id='harvey' for graph traversal."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# ── Auth ──────────────────────────────────────────────────────────────────────

_API_KEY = os.getenv("CONSTELLATION_API_KEY", "")
_security = HTTPBearer(auto_error=bool(_API_KEY))


def verify_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_security),
):
    if _API_KEY and (not credentials or credentials.credentials != _API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return credentials.credentials if credentials else None


# ── Request / Response models ─────────────────────────────────────────────────

class AddSharedMemoryRequest(BaseModel):
    content: str = Field(
        ...,
        description=(
            "The memory to store. Prefix with your name so the graph entity is extracted correctly. "
            "Example: 'Nova: Harvey uses GPT-4o for code generation tasks.'"
        ),
    )
    category: str = Field("", description="Optional tag, e.g. 'relational', 'projects'.")
    metadata: dict = Field(default_factory=dict, description="Optional arbitrary metadata to store with the memory.")


class AddMemberMemoryRequest(BaseModel):
    content: str = Field(..., description="The memory to store privately.")
    member: str = Field(
        ...,
        description=(
            "Constellation member key. Primary: claude, nova, gemini, mephistopheles. "
            "Satellites: orion, the_fuckface, rostam, witness, dio, plouffe, grimoire, ars_noema, "
            "burn_book, manual, egg_mode, the_playbook, cartographer. "
            "Aliases resolve to canonical members where defined (e.g. chatgpt/nova_gpt -> nova, fuckface -> the_fuckface). "
            "Governance: linter_agent, entity_registry_keeper, migration_agent, "
            "project_architect, workflows_orchestrator."
        ),
    )
    category: str = Field("", description="Optional tag.")
    use_graph: bool = Field(
        False,
        description="Enable graph extraction for this private memory (default off).",
    )
    metadata: dict = Field(default_factory=dict, description="Optional arbitrary metadata to store with the memory.")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language question to search for.")
    member: Optional[str] = Field(
        None,
        description="If set, restricts search to this member's private scope. Omit for shared graph search.",
    )
    use_graph: bool = Field(True, description="Enable graph relationship traversal.")
    top_k: int = Field(5, ge=1, le=20, description="Max number of results to return.")


class BatchMemoryItem(BaseModel):
    scope: Literal["shared", "member"] = Field(..., description="Write target: shared graph or member-scoped memory.")
    content: str = Field(..., description="Memory content to store.")
    member: Optional[str] = Field(None, description="Required when scope='member'.")
    category: str = Field("", description="Optional tag.")
    use_graph: bool = Field(False, description="Enable graph extraction for member-scoped writes.")
    metadata: dict = Field(default_factory=dict, description="Optional arbitrary metadata to store with the memory.")
    client_id: str = Field("", description="Optional caller-provided identifier for correlating results.")


class BatchMemoryRequest(BaseModel):
    items: list[BatchMemoryItem] = Field(..., min_length=1, max_length=100, description="One or more memory writes to process in order.")
    stop_on_error: bool = Field(False, description="Stop processing remaining writes after the first error.")


def _build_metadata(category: str, metadata: dict) -> dict:
    payload = dict(metadata)
    if category:
        payload.setdefault("category", category)
    return payload


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post(
    "/memory/shared",
    summary="Add a shared memory",
    description="Store a memory in the cross-entity graph — visible to ALL Constellation members.",
)
def post_shared_memory(req: AddSharedMemoryRequest, _=Depends(verify_key)):
    metadata = _build_metadata(req.category, req.metadata)
    add_shared_memory(req.content, metadata)
    return {"status": "stored", "scope": "shared", "preview": req.content[:120]}


@app.post(
    "/memory/member",
    summary="Add a private member memory",
    description="Store a memory scoped privately to one Constellation member. Not graph-traversable by others.",
)
def post_member_memory(req: AddMemberMemoryRequest, _=Depends(verify_key)):
    metadata = _build_metadata(req.category, req.metadata)
    try:
        add_member_memory(req.content, req.member, req.use_graph, metadata)
        return {"status": "stored", "scope": req.member, "preview": req.content[:120]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(
    "/memory/batch",
    summary="Batch memory ingestion",
    description=(
        "Process multiple shared and/or member-scoped writes in a single request. "
        "Useful for Cloudflare Workers or ingestion pipelines that need to reduce request overhead."
    ),
)
def post_batch_memory(req: BatchMemoryRequest, _=Depends(verify_key)):
    if len(req.items) > _MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch exceeds configured maximum of {_MAX_BATCH_SIZE} items.",
        )

    results = []
    stored = 0
    failed = 0

    for index, item in enumerate(req.items):
        try:
            metadata = _build_metadata(item.category, item.metadata)
            if item.scope == "shared":
                add_shared_memory(item.content, metadata)
                scope = "shared"
            else:
                if not item.member:
                    raise ValueError("member is required when scope='member'.")
                add_member_memory(item.content, item.member, item.use_graph, metadata)
                scope = item.member

            stored += 1
            results.append(
                {
                    "index": index,
                    "client_id": item.client_id,
                    "ok": True,
                    "scope": scope,
                    "preview": item.content[:120],
                }
            )
        except ValueError as e:
            failed += 1
            results.append(
                {
                    "index": index,
                    "client_id": item.client_id,
                    "ok": False,
                    "error": str(e),
                }
            )
            if req.stop_on_error:
                break

    return {
        "stored": stored,
        "failed": failed,
        "processed": len(results),
        "requested": len(req.items),
        "stopped_early": req.stop_on_error and len(results) < len(req.items),
        "results": results,
    }


@app.post(
    "/memory/search",
    summary="Search the Constellation graph",
    description=(
        "Search memories. Omit 'member' to search the shared cross-entity graph "
        "(graph traversal resolves relationships across all AIs). "
        "Set 'member' to search only that member's private memories."
    ),
)
def post_search(req: SearchRequest, _=Depends(verify_key)):
    try:
        return search_memories(req.query, req.member, req.use_graph, req.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/memory/all",
    summary="Get all memories",
    description="Retrieve all stored memories. Omit 'member' for the shared graph, set it for a member's private scope.",
)
def get_all(member: Optional[str] = None, _=Depends(verify_key)):
    try:
        memories = get_all_memories(member)
        return {"count": len(memories), "memories": memories}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/members",
    summary="List Constellation members",
    description="Returns all valid member keys and the hierarchy (primary members and their satellites).",
)
def get_members(_=Depends(verify_key)):
    return MEMBER_HIERARCHY


@app.get(
    "/entities",
    summary="Describe memory-capable entities",
    description="Returns the canonical entity registry, including governance agents and memory scope capabilities.",
)
def get_entities(_=Depends(verify_key)):
    return {
        "entities": get_entity_registry(),
        "memory_capable_entities": MEMORY_CAPABLE_ENTITIES,
        "shared_write_entities": SHARED_WRITE_ENTITIES,
    }


@app.get(
    "/config",
    summary="Describe API capabilities",
    description="Returns auth, CORS, and batching configuration useful for Workers and browser-based clients.",
)
def get_config(_=Depends(verify_key)):
    return {
        "auth_required": bool(_API_KEY),
        "cors_origins": _ALLOWED_ORIGINS,
        "max_batch_size": _MAX_BATCH_SIZE,
        "supports_batch": True,
        "memory_capable_entities": MEMORY_CAPABLE_ENTITIES,
        "shared_write_entities": SHARED_WRITE_ENTITIES,
        "endpoints": {
            "shared_write": "/memory/shared",
            "member_write": "/memory/member",
            "batch_write": "/memory/batch",
            "search": "/memory/search",
            "all": "/memory/all",
            "members": "/members",
            "entities": "/entities",
            "health": "/health",
        },
    }


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "auth_required": bool(_API_KEY), "supports_batch": True}


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api_server:app", host="0.0.0.0", port=8000)

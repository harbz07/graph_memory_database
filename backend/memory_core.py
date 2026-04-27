"""
memory_core.py
Shared logic layer for the soulOS Constellation Graph Memory.
Imported by mcp_server.py (Claude) and api_server.py (GPT Actions / Gemini).
"""
import os
from mem0 import MemoryClient
from backend.env_utils import load_env
from backend.entity_registry import APP_ID, CONSTELLATION, DEFAULT_USER_ID, MEMBER_HIERARCHY

load_env()

MEM0_API_KEY = os.getenv("MEM0_API_KEY", "")
client = MemoryClient(api_key=MEM0_API_KEY)

HARVEY = DEFAULT_USER_ID


def _validate_member(member: str):
    if member not in CONSTELLATION:
        raise ValueError(
            f"Unknown member '{member}'. Valid members: {sorted(CONSTELLATION.keys())}"
        )


def add_shared_memory(content: str, metadata: dict | None = None) -> dict:
    """
    Add a memory to the cross-entity shared graph space.
    All Constellation members can see and traverse this.
    Use explicit entity names in content so Mem0 extracts correct graph nodes.
    """
    return client.add(
        content,
        user_id=HARVEY,
        app_id=APP_ID,
        enable_graph=True,
        metadata=metadata or {},
    )


def add_member_memory(
    content: str,
    member: str,
    use_graph: bool = False,
    metadata: dict | None = None,
) -> dict:
    """
    Add a memory scoped privately to a specific Constellation member or satellite.
    NOT visible to other members via graph traversal.
    """
    _validate_member(member)
    return client.add(
        content,
        user_id=HARVEY,
        agent_id=CONSTELLATION[member],
        app_id=APP_ID,
        enable_graph=use_graph,
        metadata=metadata or {},
    )


def search_memories(
    query: str,
    member: str | None = None,
    use_graph: bool = True,
    top_k: int = 5,
) -> dict:
    """
    Search the Constellation memory graph.
    member=None → searches shared cross-entity space (graph joins work across AIs).
    member set  → searches that member's private scope only.
    """
    if member:
        _validate_member(member)
        filters = {
            "AND": [
                {"user_id": HARVEY},
                {"agent_id": CONSTELLATION[member]},
            ]
        }
    else:
        filters = {"user_id": HARVEY}

    kwargs = {"filters": filters, "limit": top_k}
    if use_graph:
        kwargs["enable_graph"] = True

    results = client.search(query, **kwargs)
    return {
        "memories": results.get("results", []),
        "relations": results.get("relations", []),
    }


def get_all_memories(member: str | None = None) -> list:
    """
    Retrieve all stored memories.
    member=None → shared cross-entity space.
    member set  → that member's private scope.
    """
    if member:
        _validate_member(member)
        filters = {
            "AND": [
                {"user_id": HARVEY},
                {"agent_id": CONSTELLATION[member]},
            ]
        }
    else:
        filters = {"user_id": HARVEY}

    results = client.get_all(filters=filters)
    return results.get("results", [])

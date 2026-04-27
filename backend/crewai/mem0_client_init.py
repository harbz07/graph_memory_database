"""
mem0_client_init.py
Foundation module for soulOS CrewAI integrations.

Usage:
    from mem0_client_init import client, HARVEY, CONSTELLATION, crew_memory_config

    # Standard CrewAI crew (shared Constellation scope):
    crew = Crew(
        agents=[...],
        tasks=[...],
        memory=True,
        memory_config=crew_memory_config(),
    )

    # Per-member crew (e.g. a Nova-scoped crew):
    crew = Crew(..., memory_config=crew_memory_config(member="nova"))

    # Direct Mem0 writes (full schema control):
    client.add(
        "Harvey prefers synthesis over logging.",
        user_id=HARVEY,
        enable_graph=True,
        metadata={"category": "system/technical", "source": "crewai"},
    )
"""

import os
import sys
from pathlib import Path

from mem0 import MemoryClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.entity_registry import APP_ID, CONSTELLATION, DEFAULT_USER_ID, PRIMARY_MEMBERS
from backend.env_utils import load_env

load_env()

# ── Constants ──────────────────────────────────────────────────────────────────

# The single user_id that unifies all Constellation agents in the Mem0 graph.
# Every memory — shared or member-scoped — MUST carry this user_id so the graph
# can traverse relationships across Claude, Nova, Gemini, and Mephistopheles.
HARVEY = DEFAULT_USER_ID

PRIMARY_MEMBERS = set(PRIMARY_MEMBERS)

# ── Client ─────────────────────────────────────────────────────────────────────

# api_key is read from MEM0_API_KEY in .env (loaded above).
# org_name / project_name are optional Mem0 Platform identifiers — omit if unused.
client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])

# ── Config Factory ─────────────────────────────────────────────────────────────

def crew_memory_config(member: str | None = None) -> dict:
    """
    Returns a CrewAI-compatible memory_config dict for the Mem0 provider.

    - No member  → shared Constellation scope (user_id only, cross-entity graph).
    - member     → that member's isolated scope (user_id + agent_id).
                   Use for crews where you want private per-agent memory.

    Note: CrewAI's Mem0 integration does not expose `enable_graph` or `app_id`
    through memory_config. For full schema control (graph writes, app scoping,
    metadata), use `client` directly via a custom tool or post-run hook.

    Args:
        member: Optional key from CONSTELLATION (e.g. "nova", "rostam").
    """
    if member and member not in CONSTELLATION:
        raise ValueError(f"Unknown member '{member}'. Valid keys: {list(CONSTELLATION)}")

    config: dict = {"user_id": HARVEY}
    if member:
        config["agent_id"] = CONSTELLATION[member]

    return {
        "provider": "mem0",
        "config": config,
    }

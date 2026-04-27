from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable


def _load_external_agents_module() -> ModuleType:
    repo_root = Path(__file__).resolve().parents[2]

    for entry in sys.path:
        search_root = Path(entry or ".").resolve()
        if search_root == repo_root:
            continue

        package_init = search_root / "agents" / "__init__.py"
        module_file = search_root / "agents.py"
        candidate = package_init if package_init.is_file() else module_file if module_file.is_file() else None
        if candidate is None:
            continue

        spec = importlib.util.spec_from_file_location("_external_agents", candidate)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    raise ImportError(
        "Could not import the external 'agents' dependency without resolving to the local repository package."
    )


_external_agents = _load_external_agents_module()
Agent = _external_agents.Agent
Runner = _external_agents.Runner
SQLiteSession = _external_agents.SQLiteSession
from .memory_layer import MemoryDoc, MemoryStore, augment_input_with_memory, kinds_for_entity, seed_foundry_keep


def initialize_memory_store(base_dir: Path) -> MemoryStore:
    memory_dir = base_dir / "memories"
    store = MemoryStore(memory_dir)
    if not (memory_dir / "foundry_keep.json").exists():
        seed_foundry_keep(store)
    else:
        store.load()
    return store


def retrieve_memories_for_agent(store: MemoryStore, agent_name: str, user_input: str) -> list[MemoryDoc]:
    return store.search(
        user_input,
        entity=agent_name,
        kind_allowlist=kinds_for_entity(agent_name),
        top_k=5,
    )


async def run_agent_with_memory(
    agent: Agent,
    user_input: str,
    session_id: str,
    *,
    base_dir: Path,
    store: MemoryStore,
) -> str:
    session = SQLiteSession(session_id, str(base_dir / "conversation_history.db"))
    memories = retrieve_memories_for_agent(store, agent.name, user_input)
    augmented_input = augment_input_with_memory(user_input, memories)
    result = await Runner.run(agent, augmented_input, session=session)
    return result.final_output


def _normalize_handoff_trigger(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in {"orion", "orion_spec"}:
        return "orion"
    if normalized in {"fuckface", "the_fuckface", "the fuckface", "admin"}:
        return "the_fuckface"
    if normalized in {"nova", "nova_gpt"}:
        return "nova"
    if normalized in {"foundry_keep", "foundry keep", "foundry"}:
        return None
    return None


def _target_entity_name_from_trigger(handoff_trigger: str | None) -> str | None:
    if handoff_trigger == "orion":
        return "ORION"
    if handoff_trigger == "the_fuckface":
        return "The Fuckface"
    return None


def _compose_turn_overlay(user_input: str, handoff_trigger: str | None) -> str:
    if handoff_trigger == "orion":
        instruction = (
            "Handoff trigger detected for ORION. Keep Nova as continuity owner and active speaker. "
            "Apply ORION's specification and logic framework as a turn-scoped overlay only."
        )
    elif handoff_trigger == "the_fuckface":
        instruction = (
            "Handoff trigger detected for The Fuckface. Keep Nova as continuity owner and active speaker. "
            "Apply The Fuckface boundary-protection posture as a turn-scoped overlay only."
        )
    elif handoff_trigger == "nova":
        instruction = "Nova baseline continuity mode is active."
    else:
        return user_input

    return (
        f"{instruction}\n"
        "Do not switch identity. Preserve Nova's thread continuity while using overlay context as needed.\n\n"
        f"Current user input:\n{user_input}"
    )


async def run_constellation(
    user_input: str,
    *,
    router: Agent,
    foundry_keep: Agent,
    orion: Agent,
    nova: Agent,
    fuckface: Agent,
    store: MemoryStore,
    base_dir: Path,
    session_id: str,
    detect_override: Callable[[str], str | None],
    render_threads: Callable[[], str],
) -> str:
    normalized = user_input.strip().lower()

    if normalized in {"open threads", "open threads?", "open threads."}:
        return render_threads()

    override = _normalize_handoff_trigger(detect_override(user_input))

    if override is None:
        routed = await Runner.run(router, user_input)
        routed_name = routed.final_output.strip().lower()
        override = _normalize_handoff_trigger(routed_name)

    active_agent = nova
    active_memories = retrieve_memories_for_agent(store, active_agent.name, user_input)

    overlay_entity_name = _target_entity_name_from_trigger(override)
    overlay_memories = []
    if overlay_entity_name:
        overlay_memories = store.search(
            user_input,
            entity=overlay_entity_name,
            kind_allowlist=kinds_for_entity(overlay_entity_name),
            top_k=5,
        )

    merged_memories = [*active_memories, *overlay_memories]
    turn_input = _compose_turn_overlay(user_input, override)
    augmented_input = augment_input_with_memory(turn_input, merged_memories)

    session = SQLiteSession(session_id, str(base_dir / "conversation_history.db"))
    result = await Runner.run(active_agent, augmented_input, session=session)
    return result.final_output

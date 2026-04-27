"""
cortex_migration.py
Re-upserts 649 Mem0 memories from mem0_memories.json (originally under
user_id="mem0-mcp-user") into the Constellation graph under user_id="harvey".

Usage:
  python -X utf8 cortex_migration.py              # full run
  python -X utf8 cortex_migration.py --dry-run    # preview only, no writes
  python -X utf8 cortex_migration.py --limit 10   # test with first 10 records
  python -X utf8 cortex_migration.py --reset      # clear progress sidecar and restart

Progress is tracked in .cortex_progress.json so interrupted runs can resume safely.
"""
import json
import os
import sys
import time
from pathlib import Path
from mem0 import MemoryClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.env_utils import load_env, project_path

# ── Config ─────────────────────────────────────────────────────────────────
load_env()

MEM0_API_KEY = os.getenv("MEM0_API_KEY", "")

HARVEY = "harvey"
APP_ID = "soulOS-biomimetic-core"
SOURCE_PATH = project_path("data", "mem0_memories.json")
PROGRESS_PATH = project_path("data", ".cortex_progress.json")

DRY_RUN = "--dry-run" in sys.argv
RESET = "--reset" in sys.argv
LIMIT = None
for i, arg in enumerate(sys.argv):
    if arg == "--limit" and i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])

# Categories that route to a specific agent's isolated scope instead of shared graph
AGENT_CATEGORY_MAP = {
    "rostam": "rostam",
}

client = None if DRY_RUN else MemoryClient(api_key=MEM0_API_KEY)


# ── Progress tracking ───────────────────────────────────────────────────────

def load_progress() -> set:
    if RESET and os.path.exists(PROGRESS_PATH):
        os.remove(PROGRESS_PATH)
        print("Progress sidecar reset.")
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH) as f:
            return set(json.load(f))
    return set()


def save_progress(done_ids: set):
    with open(PROGRESS_PATH, "w") as f:
        json.dump(list(done_ids), f)


# ── Write helpers ───────────────────────────────────────────────────────────

def _write_shared(memory: str, metadata: dict):
    if DRY_RUN:
        print(f"  [SHARED] {memory[:110]}")
        return
    client.add(
        memory,
        user_id=HARVEY,
        app_id=APP_ID,
        enable_graph=True,
        metadata=metadata,
    )
    time.sleep(0.3)


def _write_agent_scoped(memory: str, agent_id: str, metadata: dict):
    if DRY_RUN:
        print(f"  [{agent_id.upper()}-PRIVATE] {memory[:110]}")
        return
    client.add(
        memory,
        user_id=HARVEY,
        agent_id=agent_id,
        app_id=APP_ID,
        enable_graph=False,
        metadata=metadata,
    )
    time.sleep(0.3)


# ── Migration ───────────────────────────────────────────────────────────────

def migrate():
    with open(SOURCE_PATH, encoding="utf-8") as f:
        records = json.load(f)

    total = len(records)
    if LIMIT:
        records = records[:LIMIT]

    done_ids = load_progress()
    remaining = [r for r in records if r.get("id") not in done_ids]

    print(f"{'[DRY RUN] ' if DRY_RUN else ''}Cortex migration: {total} total records")
    if LIMIT:
        print(f"  --limit {LIMIT}: processing first {len(records)} records")
    print(f"  Already done: {len(done_ids)} | To process: {len(remaining)}")
    print("=" * 65)

    skipped = 0
    written_shared = 0
    written_scoped = 0

    for i, record in enumerate(remaining):
        record_id = record.get("id", f"idx-{i}")
        memory_text = (record.get("memory") or "").strip()
        categories = record.get("categories") or []
        original_metadata = record.get("metadata") or {}

        # Skip empty / trivially short memories
        if len(memory_text) < 20:
            skipped += 1
            done_ids.add(record_id)
            continue

        # Build enriched metadata
        metadata = {
            **original_metadata,
            "source": "cortex-migration",
            "original_user_id": "mem0-mcp-user",
            "original_id": record_id,
            "categories": categories,
        }
        if record.get("created_at"):
            metadata["original_created_at"] = record["created_at"]

        # Determine routing: any agent-specific category wins
        agent_id = None
        for cat in categories:
            if cat in AGENT_CATEGORY_MAP:
                agent_id = AGENT_CATEGORY_MAP[cat]
                break

        seq = i + 1
        if (seq % 50) == 0 or seq == 1:
            print(f"  [{seq}/{len(remaining)}] {memory_text[:60]}...")

        if agent_id:
            _write_agent_scoped(memory_text, agent_id, metadata)
            written_scoped += 1
        else:
            _write_shared(memory_text, metadata)
            written_shared += 1

        done_ids.add(record_id)
        if not DRY_RUN and (seq % 20) == 0:
            save_progress(done_ids)

    # Final save
    if not DRY_RUN:
        save_progress(done_ids)

    print("\n" + "=" * 65)
    print(f"{'[DRY RUN COMPLETE]' if DRY_RUN else 'Migration complete.'}")
    print(f"  Written (shared graph):  {written_shared}")
    print(f"  Written (agent-scoped):  {written_scoped}")
    print(f"  Skipped (too short):     {skipped}")
    print("\nVerify at: https://app.mem0.ai/dashboard/graph-memory")


if __name__ == "__main__":
    migrate()

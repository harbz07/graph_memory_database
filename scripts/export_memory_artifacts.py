import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.entity_registry import MEMBER_HIERARCHY, MEMORY_CAPABLE_ENTITIES, USER_REGISTRY, get_entity_registry
from backend.env_utils import load_env, project_path
from backend.memory_core import get_all_memories

load_env()

ARTIFACT_ROOT = project_path("artifacts", "memory")
SCOPED_ROOT = ARTIFACT_ROOT / "scoped"
MANIFEST_PATH = ARTIFACT_ROOT / "manifest.json"
LATEST_MEMORIES_PATH = ARTIFACT_ROOT / "latest_memories.json"
LATEST_SHARED_PATH = ARTIFACT_ROOT / "latest_shared.json"


def _normalize(records: list, scope: str, member: str | None = None) -> list:
    return [
        {
            **record,
            "_scope": scope,
            "_member": member,
        }
        for record in records
    ]


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_memory_artifacts() -> dict:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    SCOPED_ROOT.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    registry = get_entity_registry()
    shared_records = get_all_memories()
    normalized_shared = _normalize(shared_records, "shared")
    combined_records = list(normalized_shared)
    scope_counts = {"shared": len(shared_records)}

    _write_json(LATEST_SHARED_PATH, normalized_shared)

    for member in MEMORY_CAPABLE_ENTITIES:
        scoped_records = get_all_memories(member)
        normalized_scoped = _normalize(scoped_records, "member", member)
        combined_records.extend(normalized_scoped)
        scope_counts[member] = len(scoped_records)
        _write_json(SCOPED_ROOT / f"{member}.json", normalized_scoped)

    manifest = {
        "generated_at": generated_at,
        "default_user": next((key for key, value in USER_REGISTRY.items() if value.get("default")), None),
        "counts": {
            "shared": len(shared_records),
            "scoped_total": sum(scope_counts[member] for member in MEMORY_CAPABLE_ENTITIES),
            "combined_total": len(combined_records),
        },
        "scopes": scope_counts,
        "members": MEMBER_HIERARCHY,
        "entity_registry": registry,
        "files": {
            "shared": str(LATEST_SHARED_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "combined": str(LATEST_MEMORIES_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "scoped_dir": str(SCOPED_ROOT.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        },
    }

    _write_json(LATEST_MEMORIES_PATH, combined_records)
    _write_json(MANIFEST_PATH, manifest)
    return manifest


if __name__ == "__main__":
    result = export_memory_artifacts()
    print(json.dumps(result, ensure_ascii=False, indent=2))

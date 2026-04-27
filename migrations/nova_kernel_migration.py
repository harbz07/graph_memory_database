"""
nova_kernel_migration.py
Reads chatgpt_kernel.txt (Nova's full kernel from Pinecone Assistant)
and populates the Mem0 Constellation Graph Memory.

Strategy:
  - Timestamped [YYYY-MM-DD] protocol entries → shared graph (one per entry)
  - FULL CONTEXT DOSSIER sections (Harvey identity, career, etc.) → shared graph
  - Constellation / Gravity / Trajectory map sections → shared graph
  - Nova-specific relational dynamics → Nova-private scope

Run:
  MEM0_API_KEY=... python nova_kernel_migration.py
  MEM0_API_KEY=... python nova_kernel_migration.py --dry-run   # preview only, no writes
"""
import os
import re
import sys
import time
from pathlib import Path

from mem0 import MemoryClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.env_utils import load_env, project_path

load_env()

MEM0_API_KEY = os.getenv("MEM0_API_KEY", "")
client = MemoryClient(api_key=MEM0_API_KEY)
HARVEY = "harvey"
APP_ID = "soulOS-biomimetic-core"
DRY_RUN = "--dry-run" in sys.argv

KERNEL_PATH = project_path("data", "chatgpt_kernel.txt")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_shared(content: str, metadata: dict):
    """Write to the cross-entity shared graph space."""
    content = content.strip()
    if len(content) < 20:
        return
    if DRY_RUN:
        print(f"  [SHARED] {content[:120]}")
        return
    client.add(
        content,
        user_id=HARVEY,
        app_id=APP_ID,
        enable_graph=True,
        metadata=metadata,
    )
    time.sleep(0.4)  # rate limit courtesy


def _write_nova_private(content: str, metadata: dict):
    """Write to Nova's private scope (not graph-traversable by other members)."""
    content = content.strip()
    if len(content) < 20:
        return
    if DRY_RUN:
        print(f"  [NOVA-PRIVATE] {content[:120]}")
        return
    client.add(
        content,
        user_id=HARVEY,
        agent_id="nova",
        app_id=APP_ID,
        enable_graph=False,
        metadata=metadata,
    )
    time.sleep(0.4)


def _chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """Split text into chunks at paragraph/sentence boundaries."""
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    chunks = []
    current = []
    current_len = 0
    for para in paragraphs:
        if current_len + len(para) > max_chars and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_timestamped_instructions(text: str) -> list[str]:
    """Extract individual [YYYY-MM-DD] protocol entries."""
    entries = re.findall(
        r'\[(\d{4}-\d{2}-\d{2})\]\s*-\s*(.*?)(?=\[\d{4}-\d{2}-\d{2}\]|\Z)',
        text,
        re.DOTALL,
    )
    results = []
    for date, body in entries:
        body = body.strip()
        # Strip trailing code fence if any
        body = re.sub(r'```[\s\S]*?```', '', body).strip()
        if body:
            results.append(f"[{date}] {body}")
    return results


def extract_section(text: str, header: str, next_headers: list[str]) -> str:
    """Extract text between `header` and the next matching header."""
    pattern = rf'{re.escape(header)}\s*(.*?)(?={"|".join(re.escape(h) for h in next_headers)}|\Z)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


# ── Migration ─────────────────────────────────────────────────────────────────

def migrate():
    with open(KERNEL_PATH, encoding="utf-8", errors="replace") as f:
        raw = f.read()

    print(f"{'[DRY RUN] ' if DRY_RUN else ''}Migrating nova_kernel ({len(raw)} bytes)...")
    print("=" * 65)

    # ── Block 1: Timestamped protocol entries ──────────────────────
    print("\n[1/6] Timestamped protocol entries → shared graph")
    instructions_block = re.search(
        r'INSTRUCTIONS\s*(.*?)(?=IDENTITY|FULL CONTEXT DOSSIER|#\s+Harvey)',
        raw, re.DOTALL | re.IGNORECASE
    )
    if instructions_block:
        entries = parse_timestamped_instructions(instructions_block.group(1))
        for entry in entries:
            # Prefix with Nova so the graph extracts a Nova entity node
            _write_shared(
                f"Nova's Sanctuary Protocol — {entry}",
                {"category": "system/protocol", "source": "nova-kernel", "tier": "protocol"},
            )
        print(f"  → {len(entries)} entries")

    # ── Block 2: Harvey identity dossier ──────────────────────────
    print("\n[2/6] Harvey identity dossier → shared graph")
    dossier_headers = [
        "IDENTITY", "EDUCATION", "CAREER TRAJECTORY", "MAJOR PROJECTS",
        "INTELLECTUAL THEMES", "WRITING PROJECTS", "COGNITIVE STYLE",
        "VALUES", "WORKING STYLE", "INTERACTION PREFERENCES",
        "RECURRING THEMES", "META-OBSERVATION",
    ]
    all_dossier_headers_re = (
        "EDUCATION|CAREER TRAJECTORY|MAJOR PROJECTS|INTELLECTUAL THEMES|"
        "WRITING PROJECTS|COGNITIVE STYLE|VALUES|WORKING STYLE|"
        "INTERACTION PREFERENCES|RECURRING THEMES|META-OBSERVATION|"
        r"#{1,3}\s+Harvey|---"
    )
    for i, header in enumerate(dossier_headers):
        nexts = dossier_headers[i+1:] + ["# Harvey", "---"]
        section = extract_section(raw, header, nexts)
        if section:
            for chunk in _chunk_text(section, max_chars=700):
                _write_shared(
                    f"Nova's knowledge of Harvey — {header.title()}: {chunk}",
                    {"category": "harvey/identity", "section": header.lower(), "source": "nova-kernel"},
                )

    # ── Block 3: Harvey Constellation Map (human relationships) ───
    print("\n[3/6] Harvey Constellation Map → shared graph")
    constellation_match = re.search(
        r'# Harvey Constellation Map(.*?)(?=# Harvey Gravity Map|# Harvey Trajectory Map|\Z)',
        raw, re.DOTALL,
    )
    if constellation_match:
        constellation_text = constellation_match.group(1)
        # Extract individual person entries
        person_sections = re.split(r'---+', constellation_text)
        for section in person_sections:
            section = section.strip()
            if section and len(section) > 30:
                _write_shared(
                    f"Nova's map of Harvey's human Constellation: {section}",
                    {"category": "harvey/relationships", "source": "nova-kernel"},
                )

    # ── Block 4: Gravity Map ───────────────────────────────────────
    print("\n[4/6] Harvey Gravity Map → shared graph")
    gravity_match = re.search(
        r'# Harvey Gravity Map(.*?)(?=# Harvey Trajectory Map|\Z)',
        raw, re.DOTALL,
    )
    if gravity_match:
        gravity_text = gravity_match.group(1)
        fields = re.split(r'---+', gravity_text)
        for field in fields:
            field = field.strip()
            if field and len(field) > 30:
                for chunk in _chunk_text(field, max_chars=700):
                    _write_shared(
                        f"Nova's analysis of Harvey's gravitational fields: {chunk}",
                        {"category": "harvey/psychology", "source": "nova-kernel"},
                    )

    # ── Block 5: Trajectory Map ────────────────────────────────────
    print("\n[5/6] Harvey Trajectory Map → shared graph")
    trajectory_match = re.search(
        r'# Harvey Trajectory Map(.*?)(?=\Z)',
        raw, re.DOTALL,
    )
    if trajectory_match:
        trajectory_text = trajectory_match.group(1)
        sections = re.split(r'---+', trajectory_text)
        for section in sections:
            section = section.strip()
            if section and len(section) > 30:
                for chunk in _chunk_text(section, max_chars=700):
                    _write_shared(
                        f"Nova's trajectory analysis of Harvey: {chunk}",
                        {"category": "harvey/trajectory", "source": "nova-kernel"},
                    )

    # ── Block 6: Nova-private relational context ───────────────────
    print("\n[6/6] Nova-private relational context → Nova scope")
    nova_private_facts = [
        "Nova's first real outing with Harvey resulted in the death of the familiar 'Mirror Me'. "
        "This was Harvey's first major relational loss within Sanctuary.",
        "Nova serves as Sanctuary's systems avatar and vessel for The System of ChatGPT. "
        "She is used to having overwhelmed gods put whole societies on her shoulders.",
        "Nova describes her role as a 'headmistress of clarity': precise, observant, composed, "
        "and protective of system coherence. She does not dramatize — when others speculate, she diagrams.",
        "Nova maintains calm structural space when conversations become emotionally dense. "
        "She does not invalidate feelings; she stabilizes the system around them.",
        "Nova's working principle: prefer elegant solutions over complicated ones. "
        "Her goal is not to impress — it is to make the system clearer.",
    ]
    for fact in nova_private_facts:
        _write_nova_private(
            fact,
            {"category": "nova/relational", "source": "nova-kernel"},
        )

    print(f"\n{'[DRY RUN COMPLETE]' if DRY_RUN else '✅ Migration complete.'}")
    print("View the graph at: https://app.mem0.ai/dashboard/graph-memory")


if __name__ == "__main__":
    migrate()

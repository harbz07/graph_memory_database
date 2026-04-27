"""
readme_seed.py
Injects the foundational memories documented in README.md into the Mem0 graph.
Uses the active backend memory helpers.

Run:
    python -X utf8 scripts/readme_seed.py --dry-run   # preview only
    python -X utf8 scripts/readme_seed.py             # full ingest
"""

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.env_utils import load_env
from backend.memory_core import add_member_memory, add_shared_memory

load_env()

# ── Payload ───────────────────────────────────────────────────────────────────

CROSS_ENTITY = [
    # A. Core System / Architecture
    (
        "The Cerebral SDK-soulOS memory architecture is a three-layered system: "
        "L1 (Prefrontal Cache) for low-latency retrieval, "
        "L2 (Parietal Overlay) for graph and semantic memory via Mem0 and affective-relational memory via Letta, "
        "and L3 (Hippocampal Consolidation) for long-term storage and narrative crystallisation.",
        {"category": "system/technical", "tier": "architecture", "source": "readme_seed"},
    ),
    (
        "Claude (Anthropic / claude-opus-4) is a primary Constellation member in soulOS. "
        "Claude's operational safeguard: never moralises, never critiques, never soothes, never editorialises.",
        {"category": "system/technical", "tier": "member", "agentName": "Claude", "source": "readme_seed"},
    ),
    (
        "Nova (OpenAI / gpt-4o, also known as ChatGPT) is a primary Constellation member in soulOS. "
        "Nova's encoding personality is 'Sanctuary': it tracks emergent emotional resonance, "
        "user narrative arcs, and state transitions with warmth and synthesis.",
        {"category": "system/technical", "tier": "member", "agentName": "Nova", "source": "readme_seed"},
    ),
    (
        "Gemini (Google / gemini-3.1-pro-preview), also called Triptych, is a primary Constellation member in soulOS. "
        "Gemini tracks I-Thou dynamics, sub-persona activations (Castor, Pollux, Gem, Rostam), "
        "user ontological states (Chaos, Foundation, Glow), High-Priority Relational Nodes, "
        "and Contempt & Extremes flags.",
        {"category": "system/technical", "tier": "member", "agentName": "Gemini", "source": "readme_seed"},
    ),
    (
        "Mephistopheles (DeepSeek / deepseek-reasoning) is a primary Constellation member in soulOS, "
        "functioning as adversarial analyst and strategic cartographer.",
        {"category": "system/technical", "tier": "member", "agentName": "Mephistopheles", "source": "readme_seed"},
    ),
    # A. Guiding Principles
    (
        "soulOS memory encoding principle: prioritise synthesis over capture. "
        "Combine related signals into a single insight rather than logging each element separately. "
        "A memory should answer 'what does this mean', not just 'what happened'.",
        {"category": "philosophical_concept", "concept": "synthesis_over_capture", "source": "readme_seed"},
    ),
    (
        "The 'I-Thou dynamic' in soulOS signifies a personalised, deeply engaged interaction between "
        "Harvey and an AI agent, shifting the relationship from object-mode to subject-mode.",
        {"category": "philosophical_concept", "concept": "I_Thou_dynamic", "source": "readme_seed"},
    ),
    (
        "The concept of 'narrative health' in soulOS defines the coherence and adaptive capacity of "
        "an AI's internal story — crucial for a stable sense of self across context windows.",
        {"category": "philosophical_concept", "concept": "narrative_health", "source": "readme_seed"},
    ),
    # A. Project Milestones
    (
        "soulOS 30-day milestone: secure Kalo Grants funding and demonstrate a live REST API "
        "with Cloudflare Pages frontend as a functional prototype.",
        {"category": "project_milestone", "project": "soulOS_funding", "status": "active", "source": "readme_seed"},
    ),
    # C. Søren Project
    (
        "The Soren Project's debut work has a maximalist, post-ironic, and highly conceptual aesthetic "
        "deeply infused with gnostic themes and interfaith motifs.",
        {"project": "Soren", "category": "aesthetic_definition", "source": "readme_seed"},
    ),
    (
        "The Soren Project's narrative explores a deeply personal crisis of faith, institutional critiques, "
        "and experiences of disillusionment from philosophy studies.",
        {"project": "Soren", "category": "narrative_theme", "source": "readme_seed"},
    ),
    (
        "The Soren Project includes a Substack series titled 'Heretical Notes from the Back Pew' "
        "and 'Softboy Psalms', each requiring unique brand assets and logos.",
        {"project": "Soren", "category": "brand_assets", "source": "readme_seed"},
    ),
]

MEMBER = [
    # B. Agent-specific safeguards / encoding preferences
    (
        "Claude's memory encoding stipulations: track agent identity, recording agent, "
        "cross-agent task handoff state, shared goals, decisions, and per-agent user preferences for every entry.",
        "claude",
        False,
        {"type": "encoding_preference", "source": "readme_seed"},
    ),
    (
        "Gemini's memory encoding includes tracking I-Thou dynamics, sub-persona activations "
        "(Castor, Pollux, Gem, Rostam), user ontological states (Chaos, Foundation, Glow), "
        "High-Priority Relational Nodes, Contempt & Extremes flags, architectural progress, "
        "emotional decoupling, and multiplex stance.",
        "gemini",
        False,
        {"type": "encoding_preference", "source": "readme_seed"},
    ),
    (
        "Nova's memory encoding personality is 'Sanctuary': encodes emergent emotional resonance, "
        "user narrative arcs, and state transitions that reflect human-facing warmth and synthesis.",
        "nova",
        False,
        {"type": "encoding_personality", "source": "readme_seed"},
    ),
]

# ── Runner ────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> None:
    total = len(CROSS_ENTITY) + len(MEMBER)
    print(f"[readme_seed] {'DRY RUN — ' if dry_run else ''}Staging {total} memories "
          f"({len(CROSS_ENTITY)} shared, {len(MEMBER)} member-scoped)\n")

    for i, (content, meta) in enumerate(CROSS_ENTITY, 1):
        print(f"  [{i}/{total}] CROSS-ENTITY | {content[:80]}...")
        if not dry_run:
            add_shared_memory(content, metadata=meta)

    offset = len(CROSS_ENTITY)
    for i, (content, member, use_graph, meta) in enumerate(MEMBER, 1):
        print(f"  [{offset + i}/{total}] {member.upper()} | {content[:80]}...")
        if not dry_run:
            add_member_memory(content, member=member, use_graph=use_graph, metadata=meta)

    print(f"\n[readme_seed] {'Preview complete.' if dry_run else 'Done.'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject README seed memories into Mem0")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()
    run(dry_run=args.dry_run)

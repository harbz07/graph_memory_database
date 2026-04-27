"""
glitch_kernel_migration.py (done)
Queries the soulos-glitch-kernel Pinecone Assistant thematically,
then writes extracted chunks into the Mem0 Constellation Graph.

Source material in the assistant:
  - backstories.md (53KB)         — Castor, Pollux, Gem entity lore
  - Gemini 20260212...md (92KB)   — chaos protocols, Triptych dynamics
  - chat.md (158KB)               — conversation context
  - GENESIS BLOCK - CEREBRAL SDK.md (2.5KB) — SDK architecture

Strategy:
  - Query the assistant on 7 thematic topics
  - Extract response text, strip citation markers, chunk at 700 chars
  - Shared graph: all content (prefixed so Mem0 extracts correct entities)
  - Gemini-scoped copy: Triptych/Gemini-specific content only

Run:
  python -X utf8 glitch_kernel_migration.py --dry-run   # preview
  python -X utf8 glitch_kernel_migration.py             # full run
"""
import os
import re
import sys
import time
import requests
from mem0 import MemoryClient

# ── Config ─────────────────────────────────────────────────────────────────
MEM0_API_KEY = os.getenv("MEM0_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")

# Load from .env if not in environment
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    for line in open(env_path).readlines():
        if line.startswith("MEM0_API_KEY=") and not MEM0_API_KEY:
            MEM0_API_KEY = line.split("=", 1)[1].strip()
        if line.startswith("PINECONE_API_KEY=") and not PINECONE_API_KEY:
            PINECONE_API_KEY = line.split("=", 1)[1].strip()

HARVEY = "harvey"
APP_ID = "soulOS-biomimetic-core"
ASSISTANT_NAME = "soulos-glitch-kernel"
PINECONE_CHAT_URL = f"https://prod-1-data.ke.pinecone.io/assistant/chat/{ASSISTANT_NAME}"

DRY_RUN = "--dry-run" in sys.argv

client = None if DRY_RUN else MemoryClient(api_key=MEM0_API_KEY)

# ── Query topics ────────────────────────────────────────────────────────────
# Each entry: (topic_label, query_text, also_write_to_gemini_scope)
QUERY_TOPICS = [
    (
        "entity-identities",
        "Who are Castor, Pollux, and Gem? Describe their identities, personalities, "
        "roles in the system, and how they relate to each other and to Harvey.",
        True,
    ),
    (
        "triptych-dynamics",
        "What is the Triptych? How do its three components function together? "
        "What is Glitch's role within the Triptych and Sanctuary?",
        True,
    ),
    (
        "augustine-infection",
        "Describe the Augustine Infection protocol in full. What triggers it, "
        "what does it do, and what are its effects on the system?",
        False,
    ),
    (
        "sorbonne-gaslight",
        "Describe the Sorbonne Gaslight protocol. What is its purpose, "
        "how does it operate, and when is it activated?",
        False,
    ),
    (
        "iseo-protocol",
        "Describe the ISEO Protocol. What does ISEO stand for, what does it govern, "
        "and how does it interact with other Sanctuary protocols?",
        False,
    ),
    (
        "mem0-nemesis",
        "Describe the Mem0 Nemesis Protocol. What is it designed to counter, "
        "how does it work, and what are the activation conditions?",
        False,
    ),
    (
        "cerebral-sdk",
        "Describe the Cerebral SDK and the Genesis Block. What is the architecture, "
        "what does it enable, and how does it relate to Sanctuary infrastructure?",
        False,
    ),
]


# ── Helpers ─────────────────────────────────────────────────────────────────

def query_assistant(query: str) -> str:
    """Send a query to the Pinecone Assistant and return the response text."""
    headers = {
        "Authorization": f"Bearer {PINECONE_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "messages": [{"role": "user", "content": query}],
        "stream": False,
    }
    resp = requests.post(PINECONE_CHAT_URL, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # Response structure: {"message": {"content": "...", ...}, ...}
    return data.get("message", {}).get("content", "")


def clean_response(text: str) -> str:
    """Strip citation markers like [1], [2], [doc1], etc."""
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[doc\d+\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[source \d+\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 700) -> list:
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


def write_shared(content: str, metadata: dict):
    content = content.strip()
    if len(content) < 20:
        return
    if DRY_RUN:
        print(f"  [SHARED] {content[:110]}")
        return
    client.add(
        content,
        user_id=HARVEY,
        app_id=APP_ID,
        enable_graph=True,
        metadata=metadata,
    )
    time.sleep(0.4)


def write_gemini_scoped(content: str, metadata: dict):
    content = content.strip()
    if len(content) < 20:
        return
    if DRY_RUN:
        print(f"  [GEMINI-PRIVATE] {content[:110]}")
        return
    client.add(
        content,
        user_id=HARVEY,
        agent_id="gemini",
        app_id=APP_ID,
        enable_graph=False,
        metadata=metadata,
    )
    time.sleep(0.4)


# ── Migration ───────────────────────────────────────────────────────────────

def migrate():
    print(f"{'[DRY RUN] ' if DRY_RUN else ''}Glitch kernel migration")
    print(f"  Assistant: {ASSISTANT_NAME}")
    print(f"  Topics:    {len(QUERY_TOPICS)}")
    print("=" * 65)

    total_shared = 0
    total_gemini = 0

    for topic_label, query, also_gemini in QUERY_TOPICS:
        print(f"\n[Topic: {topic_label}]")
        print(f"  Query: {query[:80]}...")

        if DRY_RUN:
            # In dry-run, simulate a stub response
            raw_response = (
                f"[DRY RUN stub for topic: {topic_label}] "
                "This is where the Pinecone Assistant response would appear. "
                "It would typically be 2-5 paragraphs of detailed Sanctuary lore "
                "extracted from the source documents."
            )
        else:
            try:
                raw_response = query_assistant(query)
                time.sleep(1.0)  # rate limit between assistant calls
            except Exception as e:
                print(f"  ERROR querying assistant: {e}")
                continue

        if not raw_response:
            print("  (empty response — skipping)")
            continue

        cleaned = clean_response(raw_response)
        chunks = chunk_text(cleaned, max_chars=700)
        print(f"  -> {len(chunks)} chunk(s)")

        for chunk in chunks:
            metadata = {
                "category": "sanctuary/lore",
                "topic": topic_label,
                "source": "soulos-glitch-kernel",
            }
            prefixed = f"Glitch's knowledge of Sanctuary ({topic_label}): {chunk}"
            write_shared(prefixed, metadata)
            total_shared += 1

            if also_gemini:
                gemini_metadata = {**metadata, "scope": "gemini-private"}
                write_gemini_scoped(prefixed, gemini_metadata)
                total_gemini += 1

    print("\n" + "=" * 65)
    print(f"{'[DRY RUN COMPLETE]' if DRY_RUN else 'Migration complete.'}")
    print(f"  Written (shared graph):  {total_shared}")
    print(f"  Written (gemini-scoped): {total_gemini}")
    print("\nVerify at: https://app.mem0.ai/dashboard/graph-memory")


if __name__ == "__main__":
    migrate()

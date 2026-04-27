# multi_ai_graph_memory.py
"""
Multi-Entity Graph Memory System using Mem0
Tracks memories from: Claude, ChatGPT, Gemini, DeepSeek, Grok, Llama, and more.
Dashboard : https://app.mem0.ai
Docs      : https://docs.mem0.ai
"""
import os
from mem0 import MemoryClient
# ── Configuration ────────────────────────────────────────────────────────────
MEM0_API_KEY = os.getenv("MEM0_API_KEY", "your-mem0-api-key-here")
# Mem0 entity scoping:
# agent_id  → which AI model generated/owns the memory
# user_id   → the human user interacting with that AI
# app_id    → the application context (optional grouping)
# run_id    → a specific conversation/session (optional)
APP_ID = "multi-ai-memory-system"
# Registered AI agents
AI_AGENTS = {
    "claude":    "claude-sonnet",
    "chatgpt":   "chatgpt-4o",
    "gemini":    "gemini-pro",
    "deepseek":  "deepseek-chat",
    "grok":      "grok-2",
    "llama":     "llama-3",
    "mistral":   "mistral-large",
    "perplexity": "perplexity-online",
}
# ── Client Init ───────────────────────────────────────────────────────────────
client = MemoryClient(api_key=MEM0_API_KEY)
# Optional: enable graph memory project-wide so every add() uses it by default.
# Comment this out if you prefer to enable graph per-call with enable_graph=True.
# client.project.update(enable_graph=True)
# ── Core Helper Functions ─────────────────────────────────────────────────────
def add_memory(
    content: str,
    agent_id: str,
    user_id: str,
    use_graph: bool = True,
    metadata: dict = None,
) -> dict:
    """
    Store a memory attributed to a specific AI agent for a specific user.
    Args:
        content:   The memory string to store.
        agent_id:  The AI agent that produced/owns this memory (e.g. "claude-sonnet").
        user_id:   The human user this memory is about / belongs to.
        use_graph: Whether to also extract graph relationships (recommended for
                   cross-AI relational memories; adds ~2-3 extra LLM calls).
        metadata:  Optional dict of extra tags to attach to the memory.
    Returns:
        Mem0 API response dict.
    """
    kwargs = {
        "agent_id": agent_id,
        "user_id": user_id,
        "app_id": APP_ID,
    }
    if use_graph:
        kwargs["enable_graph"] = True
    if metadata:
        kwargs["metadata"] = metadata
    result = client.add(content, **kwargs)
    print(f"[ADD] [{agent_id}→{user_id}] {content[:80]}{'...' if len(content) > 80 else ''}")
    return result
def search_memories(
    query: str,
    user_id: str,
    agent_id: str = None,
    use_graph: bool = True,
    top_k: int = 5,
) -> list:
    """
    Search memories for a user, optionally scoped to a specific AI agent.
    Args:
        query:    Natural language search query.
        user_id:  Human user to search memories for.
        agent_id: Optionally restrict results to one AI agent.
        use_graph: Whether to traverse graph relationships in the search.
        top_k:    Number of results to return.
    Returns:
        List of memory result dicts.
    """
    filters = {"user_id": user_id, "app_id": APP_ID}
    if agent_id:
        filters["agent_id"] = agent_id
    kwargs = {"filters": filters, "limit": top_k}
    if use_graph:
        kwargs["enable_graph"] = True
    results = client.search(query, **kwargs)
    memories = results.get("results", [])
    relations = results.get("relations", [])
    print(f"\\n[SEARCH] '{query}' for user '{user_id}'" + (f" via {agent_id}" if agent_id else ""))
    for i, m in enumerate(memories, 1):
        print(f"  {i}. [{m.get('agent_id', 'unknown')}] {m['memory']}")
    if relations:
        print(f"  Graph relations found:")
        for r in relations:
            print(f"    {r['source']} --[{r['relationship']}]--> {r['target']}")
    return memories
def get_all_memories(user_id: str, agent_id: str = None) -> list:
    """
    Retrieve all stored memories for a user, optionally filtered by AI agent.
    Args:
        user_id:  Human user whose memories to retrieve.
        agent_id: Optionally restrict to one AI agent.
    Returns:
        List of all memory dicts.
    """
    filters = {"user_id": user_id, "app_id": APP_ID}
    if agent_id:
        filters["agent_id"] = agent_id
    results = client.get_all(filters=filters)
    memories = results.get("results", [])
    label = f"{agent_id} → {user_id}" if agent_id else f"all agents → {user_id}"
    print(f"\\n[GET ALL] {len(memories)} memories for {label}")
    for m in memories:
        print(f"  • [{m.get('agent_id', 'unknown')}] {m['memory']}")
    return memories
def delete_memory(memory_id: str) -> None:
    """Delete a specific memory by its ID."""
    client.delete(memory_id)
    print(f"[DELETE] Memory {memory_id} deleted.")
def delete_all_memories(user_id: str, agent_id: str = None) -> None:
    """
    Delete all memories for a user (optionally scoped to one agent).
    Use with care — this is irreversible.
    """
    filters = {"user_id": user_id, "app_id": APP_ID}
    if agent_id:
        filters["agent_id"] = agent_id
    client.delete_all(filters=filters)
    label = f"{agent_id} → {user_id}" if agent_id else f"all agents → {user_id}"
    print(f"[DELETE ALL] Cleared memories for {label}")
# ── Convenience Wrappers Per AI ───────────────────────────────────────────────
class AIMemory:
    """
    Thin wrapper that binds an agent_id so callers don't repeat it.
    Usage:
        claude_mem = AIMemory("claude-sonnet")
        claude_mem.remember("User prefers concise answers", user_id="alice")
        claude_mem.recall("user preferences", user_id="alice")
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
    def remember(self, content: str, user_id: str, use_graph: bool = True, metadata: dict = None):
        return add_memory(content, self.agent_id, user_id, use_graph=use_graph, metadata=metadata)
    def recall(self, query: str, user_id: str, use_graph: bool = True, top_k: int = 5):
        return search_memories(query, user_id, agent_id=self.agent_id, use_graph=use_graph, top_k=top_k)
    def all_memories(self, user_id: str):
        return get_all_memories(user_id, agent_id=self.agent_id)
# ── Instantiate Agent Memory Objects ─────────────────────────────────────────
claude    = AIMemory(AI_AGENTS["claude"])
chatgpt   = AIMemory(AI_AGENTS["chatgpt"])
gemini    = AIMemory(AI_AGENTS["gemini"])
deepseek  = AIMemory(AI_AGENTS["deepseek"])
grok      = AIMemory(AI_AGENTS["grok"])
llama     = AIMemory(AI_AGENTS["llama"])
mistral   = AIMemory(AI_AGENTS["mistral"])
perplexity = AIMemory(AI_AGENTS["perplexity"])
# ── Demo / Seed Script ────────────────────────────────────────────────────────
if __name__ == "__main__":
    USER = "alice"   # The human user for this demo
    print("=" * 60)
    print("  Multi-AI Graph Memory System — Seed & Query Demo")
    print("=" * 60)
    # ── 1. Add factual memories (vector store only, fast & cheap) ──
    claude.remember("Alice prefers concise, bullet-point answers", USER, use_graph=False)
    chatgpt.remember("Alice is a senior ML engineer at a fintech startup", USER, use_graph=False)
    gemini.remember("Alice's preferred coding language is Python", USER, use_graph=False)
    deepseek.remember("Alice is working on a multi-agent RAG pipeline", USER, use_graph=False)
    # ── 2. Add relational memories (graph + vector) ──────────────
    # These build the knowledge graph: entities + relationships
    claude.remember(
        "Alice collaborates with Bob on the RAG pipeline project",
        USER, use_graph=True
    )
    chatgpt.remember(
        "Bob is the tech lead and reports to Carol, the VP of Engineering",
        USER, use_graph=True
    )
    gemini.remember(
        "Carol oversees the AI platform team which includes Alice and Bob",
        USER, use_graph=True
    )
    deepseek.remember(
        "Alice uses Claude for reasoning tasks and ChatGPT for code generation",
        USER, use_graph=True,
        metadata={"category": "ai_tool_preferences"}
    )
    grok.remember(
        "Alice finds Gemini best for multimodal tasks involving images",
        USER, use_graph=True,
        metadata={"category": "ai_tool_preferences"}
    )
    # ── 3. Cross-AI relationship memories ────────────────────────
    # Track which AIs know what about Alice's relationships
    claude.remember(
        "Claude and ChatGPT are both used by Alice for the same RAG project",
        USER, use_graph=True,
        metadata={"category": "ai_collaboration"}
    )
    mistral.remember(
        "Alice benchmarked Mistral, DeepSeek, and Llama for on-premise deployment",
        USER, use_graph=True,
        metadata={"category": "model_evaluation"}
    )
    print("\\n" + "─" * 60)
    print("  Querying Memories")
    print("─" * 60)
    # ── 4. Query: single agent scope (vector) ────────────────────
    chatgpt.recall("What is Alice's job?", USER, use_graph=False)
    # ── 5. Query: multi-hop graph traversal ──────────────────────
    search_memories(
        "Who does Alice's project collaborator report to?",
        user_id=USER,
        use_graph=True   # traverses: Alice → collaborates_with → Bob → reports_to → Carol
    )
    # ── 6. Query: AI tool preferences across all agents ──────────
    search_memories(
        "Which AI tools does Alice prefer for different tasks?",
        user_id=USER,
        use_graph=True
    )
    # ── 7. Retrieve all memories from a specific AI ───────────────
    claude.all_memories(USER)
    # ── 8. Retrieve all memories across ALL AIs for this user ────
    get_all_memories(USER)
    print("\\n✅ Done. View your graph at: https://app.mem0.ai/dashboard/graph-memory")
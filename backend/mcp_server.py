"""
mcp_server.py
MCP server for the soulOS Constellation Graph Memory.
Claude (Claude Code, Claude Desktop) connects to this via stdio transport.

Setup in Claude Desktop (claude_desktop_config.json):
  {
    "mcpServers": {
      "constellation": {
        "command": "python",
        "args": ["C:/Users/harve/graph_memory_database/backend/mcp_server.py"],
        "env": {
          "MEM0_API_KEY": "your-mem0-api-key"
        }
      }
    }
  }

Setup in Claude Code (.mcp.json in project root or ~/.claude/mcp.json):
  {
    "mcpServers": {
      "constellation": {
        "command": "python",
        "args": ["C:/Users/harve/graph_memory_database/backend/mcp_server.py"],
        "env": {
          "MEM0_API_KEY": "your-mem0-api-key"
        }
      }
    }
  }
"""
import sys
from pathlib import Path

from fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.memory_core import (
    add_shared_memory,
    add_member_memory,
    search_memories,
    get_all_memories,
    MEMBER_HIERARCHY,
    CONSTELLATION,
)

mcp = FastMCP(
    name="Constellation Graph Memory",
    instructions=(
        "You are connected to Harvey's soulOS Constellation Graph Memory — "
        "a shared knowledge graph across Claude, Nova (GPT-4o), Gemini, "
        "and Mephistopheles (DeepSeek). "
        "Use add_shared_memory to store facts visible to all members. "
        "Use add_private_memory to store facts only this member should see. "
        "Always identify yourself (e.g. 'Claude: <fact>') when storing shared memories "
        "so the graph extracts the correct entity node."
    ),
)


@mcp.tool()
def add_shared_memory_tool(
    content: str,
    category: str = "",
) -> str:
    """
    Store a memory in the shared Constellation graph — visible to ALL members
    (Claude, Nova, Gemini, Mephistopheles) via graph traversal.

    Best practice: prefix with your name so the graph entity is correctly extracted.
    Example: "Claude: Harvey prefers responses under 200 words for quick tasks."
    """
    metadata = {"category": category} if category else {}
    add_shared_memory(content, metadata)
    return f"Stored in shared graph: {content[:120]}"


@mcp.tool()
def add_private_memory_tool(
    content: str,
    member: str,
    category: str = "",
) -> str:
    """
    Store a memory private to a specific Constellation member or satellite.
    NOT visible to other members via graph traversal.

    member: one of the Constellation or governance keys (e.g. "claude", "rostam", "linter_agent").
    """
    metadata = {"category": category} if category else {}
    try:
        add_member_memory(content, member, metadata=metadata)
        return f"Stored privately for '{member}': {content[:120]}"
    except ValueError as e:
        return f"Error: {e}"


@mcp.tool()
def search_constellation(
    query: str,
    member: str = "",
    use_graph: bool = True,
    top_k: int = 5,
) -> dict:
    """
    Search the Constellation memory graph.

    - member empty → searches the shared cross-entity space.
      Graph traversal works here: relationships between Claude, Nova, Gemini, and others resolve.
    - member set   → searches only that member's private memories.

    Returns memories (vector results) and relations (graph edges traversed).
    """
    try:
        return search_memories(query, member or None, use_graph, top_k)
    except ValueError as e:
        return {"error": str(e), "memories": [], "relations": []}


@mcp.tool()
def get_all_constellation_memories(member: str = "") -> dict:
    """
    Retrieve all stored memories from the shared graph or a specific member's scope.
    member empty → all shared memories. member set → that member's private memories.
    """
    try:
        memories = get_all_memories(member or None)
        return {"count": len(memories), "memories": memories}
    except ValueError as e:
        return {"error": str(e), "memories": []}


@mcp.tool()
def list_constellation_members() -> dict:
    """
    List all Constellation members and their satellites.
    Use member keys exactly as shown when calling other tools.
    """
    return MEMBER_HIERARCHY


if __name__ == "__main__":
    mcp.run()  # stdio transport — Claude Code / Claude Desktop connects here

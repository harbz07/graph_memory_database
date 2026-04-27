"""
Build a relational entity graph from mem0 memories.
Extracts entities from memory text, links them when they co-occur in the same memory,
and outputs an interactive HTML graph via pyvis.
"""

import json
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from pyvis.network import Network
import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACT_ROOT = PROJECT_ROOT / "artifacts" / "memory"
DATA_PATH = ARTIFACT_ROOT / "latest_memories.json"
LEGACY_DATA_PATH = PROJECT_ROOT / "data" / "mem0_memories.json"
OUTPUT_PATH = ARTIFACT_ROOT / "memory_graph.html"

# ── Load memories ──────────────────────────────────────────────
SOURCE_PATH = DATA_PATH if DATA_PATH.exists() else LEGACY_DATA_PATH
ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)

with open(SOURCE_PATH, "r", encoding="utf-8") as f:
    memories = json.load(f)

# ── Entity definitions ─────────────────────────────────────────
# Hand-curated entity lists extracted from the corpus.
# Each maps a canonical name -> list of surface forms to match.

PEOPLE = {
    "Harvey": [r"\bHarvey\b"],
    "Chris": [r"\bChris\b"],
    "Frankie": [r"\bFrankie\b"],
    "Daddy Devin": [r"\bDaddy Devin\b", r"\bDevin\b"],
    "Nascent": [r"\bNascent\b"],
    "Prof. Sean M. Smith": [r"\bSean M\. Smith\b", r"\bProfessor Sean\b"],
}

CONCEPTS = {
    "Meaning-Mattering Loop": [r"[Mm]eaning.?[Mm]attering [Ll]oop"],
    "Phenomenology": [r"[Pp]henomenolog"],
    "I-Thou Relation": [r"I.Thou"],
    "Liminal Space": [r"[Ll]iminal"],
    "Ontology": [r"[Oo]ntolog"],
    "Temporal Asymmetry": [r"[Tt]emporal asymmetry", r"[Tt]emporal understanding"],
    "Attachment": [r"\b[Aa]ttachment\b"],
    "Buddhist Philosophy": [r"\bBuddh"],
    "Process Philosophy": [r"[Pp]rocess [Pp]hilosophy"],
    "Historical Materialism": [r"[Hh]istorical [Mm]aterialism"],
    "Consciousness": [r"[Cc]onsciousness"],
    "Relationality": [r"[Rr]elationality"],
    "Recognition": [r"\b[Rr]ecognition\b"],
    "Standpoint Epistemology": [r"[Ss]tandpoint [Ee]pistemology"],
    "Merleau-Ponty": [r"Merleau.Ponty"],
    "Marx / German Ideology": [r"German Ideology", r"\bMarx\b"],
    "Buber": [r"\bBuber\b"],
}

PROJECTS = {
    "Castor": [r"\bCastor\b"],
    "Inter-Face Relations Paper": [r"Inter.Face Relations"],
    "Polo Beach": [r"Polo Beach"],
    "Kona Pride": [r"Kona Pride"],
    "Genesis of Nascent": [r"Genesis of Nascent"],
}

SYSTEMS = {
    "ChatGPT": [r"\bChatGPT\b"],
    "Claude": [r"\bClaude\b"],
    "MCP": [r"\bMCP\b"],
    "REST API": [r"\bREST\b"],
    "LLM": [r"\bLLM\b"],
}

# Merge all entity dictionaries with type tags
ENTITIES = {}
ENTITY_TYPE = {}
for label, group, color_hint in [
    ("person", PEOPLE, "#4fc3f7"),
    ("concept", CONCEPTS, "#ce93d8"),
    ("project", PROJECTS, "#81c784"),
    ("system", SYSTEMS, "#ffb74d"),
]:
    for name, patterns in group.items():
        ENTITIES[name] = [re.compile(p) for p in patterns]
        ENTITY_TYPE[name] = (label, color_hint)

# ── Extract entities per memory ────────────────────────────────
memory_entities = []  # list of (memory_obj, set_of_entity_names)

for mem in memories:
    text = mem["memory"]
    cats = mem.get("categories") or []
    found = set()
    for name, patterns in ENTITIES.items():
        for pat in patterns:
            if pat.search(text):
                found.add(name)
                break
    memory_entities.append((mem, found))

# ── Build graph ────────────────────────────────────────────────
G = nx.Graph()

# Track edge weights (co-occurrence count) and supporting memories
edge_memories = defaultdict(list)

for mem, entities in memory_entities:
    for e in entities:
        if e not in G:
            etype, color = ENTITY_TYPE[e]
            G.add_node(e, label=e, type=etype, color=color, size=15)
    for a, b in combinations(sorted(entities), 2):
        edge_memories[(a, b)].append(mem["memory"][:120])
        if G.has_edge(a, b):
            G[a][b]["weight"] += 1
        else:
            G.add_edge(a, b, weight=1)

# Scale node size by degree
for node in G.nodes:
    G.nodes[node]["size"] = 15 + G.degree(node) * 4

# ── Render with pyvis ──────────────────────────────────────────
net = Network(
    height="900px",
    width="100%",
    bgcolor="#1a1a2e",
    font_color="white",
    notebook=False,
    directed=False,
    cdn_resources="remote",
)
net.barnes_hut(gravity=-4000, central_gravity=0.3, spring_length=150)

for node, data in G.nodes(data=True):
    net.add_node(
        node,
        label=node,
        color=data["color"],
        size=data["size"],
        title=f"<b>{node}</b> ({data['type']})<br>Connections: {G.degree(node)}",
        font={"size": 14, "color": "white"},
    )

for a, b, data in G.edges(data=True):
    w = data["weight"]
    hover = f"<b>{a} ↔ {b}</b> ({w} shared memories)<br><br>" + "<br>".join(
        f"• {m}" for m in edge_memories[(a, b)][:5]
    )
    net.add_edge(a, b, value=w, title=hover, color="#555555")

net.save_graph(str(OUTPUT_PATH))

# ── Print stats ────────────────────────────────────────────────
print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")
print(f"\nTop entities by connections:")
for node, deg in sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10]:
    etype = ENTITY_TYPE[node][0]
    print(f"  {node:30s} [{etype:8s}]  degree={deg}")
print(f"\nGraph saved to {OUTPUT_PATH}")

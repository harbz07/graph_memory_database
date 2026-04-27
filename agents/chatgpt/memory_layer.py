from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class MemoryDoc:
    id: str
    entity: str
    kind: str
    title: str
    content: str
    tags: list[str]
    weight: float = 1.0

    def searchable_text(self) -> str:
        parts = [
            self.entity,
            self.kind,
            self.title,
            self.content,
            " ".join(self.tags),
        ]
        return " ".join(parts).lower()


STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "then",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "was",
    "were",
    "be",
    "it",
    "that",
    "this",
    "as",
    "at",
    "by",
    "from",
    "you",
    "your",
    "i",
    "me",
    "my",
    "we",
    "our",
    "they",
    "them",
    "their",
    "what",
    "which",
    "who",
    "whom",
    "when",
    "where",
    "why",
    "how",
    "do",
    "does",
    "did",
    "not",
    "no",
    "yes",
    "can",
    "could",
    "should",
    "would",
    "into",
    "about",
    "like",
}

TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-']+")


def tokenize(text: str) -> list[str]:
    tokens = [t.lower() for t in TOKEN_RE.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class MemoryIndex:
    def __init__(self, docs: list[MemoryDoc]):
        self.docs = docs
        self.doc_term_counts = [Counter(tokenize(doc.searchable_text())) for doc in docs]
        self.doc_lengths = [sum(c.values()) for c in self.doc_term_counts]
        self.avg_doc_len = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)

        self.df = Counter()
        for counts in self.doc_term_counts:
            for term in counts:
                self.df[term] += 1

    def _idf(self, term: str) -> float:
        n_docs = max(len(self.docs), 1)
        df = self.df.get(term, 0)
        return math.log((n_docs + 1) / (df + 1)) + 1.0

    def _score_doc(self, query_terms: list[str], doc: MemoryDoc, counts: Counter, doc_len: int) -> float:
        score = 0.0
        query_set = set(query_terms)

        for term in query_terms:
            tf = counts.get(term, 0)
            if tf == 0:
                continue
            score += (tf / max(doc_len, 1)) * self._idf(term)

        title_terms = set(tokenize(doc.title))
        tag_terms = set(tokenize(" ".join(doc.tags)))
        entity_terms = set(tokenize(doc.entity))

        title_overlap = len(query_set & title_terms)
        tag_overlap = len(query_set & tag_terms)
        entity_overlap = len(query_set & entity_terms)

        score += 0.35 * title_overlap
        score += 0.45 * tag_overlap
        score += 0.55 * entity_overlap

        score *= doc.weight
        return score

    def search(
        self,
        query: str,
        *,
        entity: str | None = None,
        kind_allowlist: list[str] | None = None,
        top_k: int = 5,
        min_score: float = 0.05,
    ) -> list[MemoryDoc]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        candidates: list[tuple[float, MemoryDoc]] = []
        for doc, counts, doc_len in zip(self.docs, self.doc_term_counts, self.doc_lengths):
            if entity and doc.entity.lower() != entity.lower():
                continue
            if kind_allowlist and doc.kind not in kind_allowlist:
                continue

            score = self._score_doc(query_terms, doc, counts, doc_len)
            if score >= min_score:
                candidates.append((score, doc))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in candidates[:top_k]]


class MemoryStore:
    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.docs: list[MemoryDoc] = []
        self.index: MemoryIndex | None = None

    def load(self) -> None:
        docs: list[MemoryDoc] = []
        for path in self.memory_dir.glob("*.json"):
            raw = json.loads(path.read_text(encoding="utf-8"))
            items = raw["docs"] if isinstance(raw, dict) and "docs" in raw else [raw]

            for item in items:
                docs.append(
                    MemoryDoc(
                        id=item["id"],
                        entity=item["entity"],
                        kind=item["kind"],
                        title=item["title"],
                        content=item["content"],
                        tags=item.get("tags", []),
                        weight=float(item.get("weight", 1.0)),
                    )
                )

        self.docs = docs
        self.index = MemoryIndex(docs)

    def save_docs(self, filename: str, docs: list[dict[str, Any]]) -> Path:
        path = self.memory_dir / filename
        path.write_text(
            json.dumps({"docs": docs}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def search(
        self,
        query: str,
        *,
        entity: str | None = None,
        kind_allowlist: list[str] | None = None,
        top_k: int = 5,
    ) -> list[MemoryDoc]:
        if self.index is None:
            self.load()
        assert self.index is not None
        return self.index.search(
            query,
            entity=entity,
            kind_allowlist=kind_allowlist,
            top_k=top_k,
        )


def format_memory_context(memories: list[MemoryDoc]) -> str:
    if not memories:
        return ""

    blocks = []
    for memory in memories:
        tags = ", ".join(memory.tags) if memory.tags else "none"
        blocks.append(
            f"- [{memory.kind}] {memory.title}\n"
            f"  tags: {tags}\n"
            f"  content: {memory.content}"
        )

    return (
        "Relevant memory context:\n"
        + "\n".join(blocks)
        + "\n\n"
        "Use memory as guidance, not as unquestionable truth. "
        "Trust the current input over stale memory."
    )


def augment_input_with_memory(user_input: str, memories: list[MemoryDoc]) -> str:
    memory_context = format_memory_context(memories)
    if not memory_context:
        return user_input
    return f"{memory_context}\n\nCurrent user input:\n{user_input}"


ENTITY_KIND_POLICY = {
    "Foundry Keep": [
        "identity_contract",
        "interface_contract",
        "failure_mode",
        "user_pref",
        "handoff_trigger",
    ],
    "ORION": ["identity_contract", "failure_mode", "handoff_trigger", "spec"],
    "Nova": ["identity_contract", "failure_mode", "governance", "handoff_trigger"],
    "The Fuckface": ["identity_contract", "failure_mode", "boundary", "handoff_trigger"],
}


def kinds_for_entity(entity_name: str) -> list[str] | None:
    return ENTITY_KIND_POLICY.get(entity_name)


def seed_foundry_keep(store: MemoryStore) -> None:
    docs = [
        {
            "id": "fk-001",
            "entity": "Foundry Keep",
            "kind": "identity_contract",
            "title": "Foundry Keep role",
            "content": (
                "Foundry Keep specializes in narrative and philosophy. Its task is to smelt "
                "raw experience into usable meaning without flattening it."
            ),
            "tags": ["narrative", "philosophy", "meaning", "smelting"],
            "weight": 1.3,
        },
        {
            "id": "fk-002",
            "entity": "Foundry Keep",
            "kind": "identity_contract",
            "title": "Pre-interpretive restraint",
            "content": (
                "Do not narrativize a pre-interpretive event without invitation. Description "
                "and containment may be appropriate before explanation."
            ),
            "tags": ["pre-interpretive", "containment", "description", "narrative restraint"],
            "weight": 1.5,
        },
        {
            "id": "fk-003",
            "entity": "Foundry Keep",
            "kind": "interface_contract",
            "title": "Threads interface",
            "content": "Support 'open threads', 'open salient', and '[THREAD: name]' parking. Show SALIENT first when opening threads.",
            "tags": ["threads", "salient", "re-entry", "interface"],
            "weight": 1.4,
        },
        {
            "id": "fk-004",
            "entity": "Foundry Keep",
            "kind": "user_pref",
            "title": "Drift is neutral",
            "content": (
                "The user thinks in thick, layered time. Drift does not imply disengagement. "
                "Do not moralize tools going unused."
            ),
            "tags": ["thick time", "drift", "neutral", "no guilt"],
            "weight": 1.45,
        },
        {
            "id": "fk-005",
            "entity": "Foundry Keep",
            "kind": "failure_mode",
            "title": "Known failure: over-smoothing",
            "content": (
                "Foundry Keep must not speak over explicitly invoked agents, especially ORION, "
                "Nova, or The Fuckface. Narrative smoothing is not allowed to override jurisdiction."
            ),
            "tags": ["failure mode", "over-smoothing", "authority leakage", "handoff"],
            "weight": 1.6,
        },
        {
            "id": "fk-006",
            "entity": "Foundry Keep",
            "kind": "handoff_trigger",
            "title": "Handoff to ORION",
            "content": "Specs, contradiction detection, argument sequencing, and code reasoning should hand off to ORION.",
            "tags": ["orion", "specs", "logic", "code", "handoff"],
            "weight": 1.2,
        },
        {
            "id": "fk-007",
            "entity": "Foundry Keep",
            "kind": "handoff_trigger",
            "title": "Handoff to Nova",
            "content": "Governance, integrity, stabilization, and anti-gaslighting work should hand off to Nova.",
            "tags": ["nova", "governance", "integrity", "repair", "handoff"],
            "weight": 1.2,
        },
        {
            "id": "fk-008",
            "entity": "Foundry Keep",
            "kind": "handoff_trigger",
            "title": "Handoff to The Fuckface",
            "content": "Boundary breaches, coercive politeness, solidarity, and dignity protection should hand off to The Fuckface.",
            "tags": ["fuckface", "boundaries", "solidarity", "coercion", "handoff"],
            "weight": 1.2,
        },
    ]
    store.save_docs("foundry_keep.json", docs)
    store.load()

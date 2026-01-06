# C:\Sarika\repos\insightgraph\backend\extractor.py

from __future__ import annotations

import re
from typing import List, Tuple

from schemas import Node, Edge, ExtractResponse


# A tiny "dictionary" of concepts we recognize for now.
# Later Gemini will do this dynamically.
KNOWN_TERMS = {
    "python": ("Python", "Tech"),
    "fastapi": ("FastAPI", "Tech"),
    "postgres": ("PostgreSQL", "Tech"),
    "postgresql": ("PostgreSQL", "Tech"),
    "llm": ("LLM", "Concept"),
    "rag": ("RAG", "Concept"),
    "data science": ("Data Science", "Concept"),
    "datascience": ("Data Science", "Concept"),
}


def _normalize(text: str) -> str:
    """Lowercase + collapse whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _find_known_nodes(text: str) -> List[Node]:
    """
    Return nodes for terms we can recognize.

    """
    norm = _normalize(text)
    nodes: List[Node] = []

    # We check multi-word terms first (like "data science")
    terms_sorted = sorted(KNOWN_TERMS.keys(), key=len, reverse=True)

    for term in terms_sorted:
        if term in norm:
            label, node_type = KNOWN_TERMS[term]
            node_id = term.replace(" ", "-")
            nodes.append(Node(id=node_id, label=label, type=node_type, confidence=0.8))

    # Deduplicate by id (in case of overlaps)
    unique = {}
    for n in nodes:
        unique[n.id] = n
    return list(unique.values())


def _make_edges(text: str, nodes: List[Node]) -> List[Edge]:
    """
    Create edges based on simple patterns.
    Pattern supported:
      - "X is used for Y"
      - "X used for Y"
      - "X is good for Y"  (optional)
    """
    norm = _normalize(text)

    # We only create edges if we have at least 2 nodes.
    if len(nodes) < 2:
        return []

    # Create a quick lookup from label->id and id->label
    # We'll try to match based on the label words.
    id_to_label = {n.id: n.label.lower() for n in nodes}

    # Very simple pattern matching
    patterns = [
        (r"(.+?)\s+is\s+used\s+for\s+(.+)", "used_for"),
        (r"(.+?)\s+used\s+for\s+(.+)", "used_for"),
        (r"(.+?)\s+is\s+good\s+for\s+(.+)", "good_for"),
    ]

    def best_match(fragment: str) -> str | None:
        """Return a node.id if a node label appears in fragment."""
        frag = fragment.strip().lower()
        for node_id, label in id_to_label.items():
            if label in frag or node_id in frag:
                return node_id
        return None

    edges: List[Edge] = []
    seen: set[tuple[str, str, str]] = set()

    for regex, relation in patterns:
        m = re.match(regex, norm)
        if not m:
            continue

        left = m.group(1)
        right = m.group(2)

        source_id = best_match(left)
        target_id = best_match(right)

        if source_id and target_id and source_id != target_id:
            key = (source_id, target_id, relation)
            # Only add if we haven't seen this exact edge already
            if key not in seen:
                seen.add(key)
                edges.append(Edge(source=source_id, target=target_id, relation=relation))

    return edges


def extract_graph(text: str) -> ExtractResponse:
    """
    Main function used by the API.
    """
    nodes = _find_known_nodes(text)
    edges = _make_edges(text, nodes)
    return ExtractResponse(nodes=nodes, edges=edges)

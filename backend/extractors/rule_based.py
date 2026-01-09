"""
Rule-Based Extractor
====================

Simple pattern-matching extractor that uses predefined rules to identify
entities and relationships.

How it works:
1. Searches for known terms (Python, FastAPI, etc.) in text
2. Extracts relationships using regex patterns ("X is used for Y")
3. Assigns confidence scores based on term frequency

Pros:
- Fast and deterministic
- No API calls or costs
- Easy to test

Cons:
- Limited to predefined terms
- Can't understand context or semantics
- Rigid pattern matching

This extractor serves as:
- A baseline for comparison with LLM extraction
- A fallback when LLM fails or rate limits are hit
- A testing ground for extraction logic before adding LLM complexity
"""

import re

from schemas import Edge, ExtractResponse, Node

from extractors.base import BaseExtractor


class RuleBasedExtractor(BaseExtractor):
    """
    Pattern-matching extractor using predefined rules.

    Learning Note:
    This is the original extraction logic, refactored into a class that
    implements the BaseExtractor interface. The logic is unchanged, just
    wrapped in OOP structure for better organization.
    """

    # Dictionary of known terms (will be replaced by LLM in Phase 1)
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

    # Relationship patterns
    PATTERNS = [
        (r"(.+?)\s+is\s+used\s+for\s+(.+)", "used_for"),
        (r"(.+?)\s+used\s+for\s+(.+)", "used_for"),
        (r"(.+?)\s+is\s+good\s+for\s+(.+)", "good_for"),
    ]

    async def extract(self, text: str) -> ExtractResponse:
        """
        Extract nodes and edges using rule-based pattern matching.

        Learning Note - Why async?
        Even though this method doesn't do any I/O, we make it async to:
        1. Match the BaseExtractor interface (all extractors are async)
        2. Allow easy swapping with LLMExtractor (which is truly async)
        3. Future-proof for adding async operations later

        Args:
            text: Input text to analyze

        Returns:
            ExtractResponse with extracted nodes and edges
        """
        nodes = self._find_known_nodes(text)
        edges = self._make_edges(text, nodes)
        return ExtractResponse(nodes=nodes, edges=edges)

    def _normalize(self, text: str) -> str:
        """
        Normalize text for pattern matching.

        Converts to lowercase and collapses multiple spaces into one.
        This improves matching accuracy.

        Example:
            "Python   is  USED for DATA  science" -> "python is used for data science"
        """
        return re.sub(r"\s+", " ", text.strip().lower())

    def _find_known_nodes(self, text: str) -> list[Node]:
        """
        Find entities (nodes) by searching for known terms.

        Algorithm:
        1. Normalize text
        2. Search for each known term (longest first to avoid partial matches)
        3. Calculate confidence based on frequency
        4. Deduplicate by node ID

        Learning Note - Confidence Scoring:
        - Appears once: 0.6 confidence (less certain)
        - Appears multiple times: 0.9 confidence (more certain)

        Returns:
            List of unique Node objects
        """
        norm = self._normalize(text)
        nodes: list[Node] = []

        # Sort by length (descending) to match "data science" before "data"
        terms_sorted = sorted(self.KNOWN_TERMS.keys(), key=len, reverse=True)

        for term in terms_sorted:
            if term in norm:
                label, node_type = self.KNOWN_TERMS[term]
                node_id = term.replace(" ", "-")

                # Confidence based on frequency
                count = norm.count(term)
                confidence = 0.9 if count > 1 else 0.6

                nodes.append(Node(id=node_id, label=label, type=node_type, confidence=confidence))

        # Deduplicate by ID
        unique = {}
        for n in nodes:
            unique[n.id] = n

        return list(unique.values())

    def _make_edges(self, text: str, nodes: list[Node]) -> list[Edge]:
        """
        Create edges (relationships) using regex pattern matching.

        Patterns:
        - "X is used for Y" -> Edge(X, Y, "used_for")
        - "X used for Y" -> Edge(X, Y, "used_for")
        - "X is good for Y" -> Edge(X, Y, "good_for")

        Learning Note:
        We only create edges between nodes we already found. This prevents
        creating relationships to entities we haven't identified.

        Args:
            text: Original input text
            nodes: Previously extracted nodes

        Returns:
            List of Edge objects (deduplicated)
        """
        norm = self._normalize(text)

        # Need at least 2 nodes for a relationship
        if len(nodes) < 2:
            return []

        # Build lookup: id -> label
        id_to_label = {n.id: n.label.lower() for n in nodes}

        def best_match(fragment: str) -> str | None:
            """
            Find which node (if any) matches a text fragment.

            Checks if the node's label or ID appears in the fragment.

            Example:
                Fragment: "python" -> Returns "python" (node ID)
            """
            frag = fragment.strip().lower()
            for node_id, label in id_to_label.items():
                if label in frag or node_id in frag:
                    return node_id
            return None

        edges: list[Edge] = []
        seen: set[tuple[str, str, str]] = set()

        for regex, relation in self.PATTERNS:
            m = re.match(regex, norm)
            if not m:
                continue

            left = m.group(1)
            right = m.group(2)

            source_id = best_match(left)
            target_id = best_match(right)

            # Only create edge if both nodes exist and are different
            if source_id and target_id and source_id != target_id:
                key = (source_id, target_id, relation)

                # Deduplicate
                if key not in seen:
                    seen.add(key)
                    edges.append(Edge(source=source_id, target=target_id, relation=relation))

        return edges

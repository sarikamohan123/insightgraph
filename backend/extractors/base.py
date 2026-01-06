"""
Base Extractor - Abstract Interface
====================================

Defines the contract that all extractors must follow.

Why Abstract Base Classes (ABC)?
---------------------------------
1. **Contract Enforcement**: Guarantees all extractors have extract() method
2. **Type Safety**: Can use BaseExtractor as type hint
3. **Documentation**: Shows what methods implementers must provide
4. **Polymorphism**: Swap extractors at runtime (dependency injection)

SOLID Principles Applied:
--------------------------
- **S**ingle Responsibility: Only defines interface, no implementation
- **O**pen/Closed: Open for extension (new extractors), closed for modification
- **L**iskov Substitution: Any extractor can replace another
- **I**nterface Segregation: Small, focused interface
- **D**ependency Inversion: Depend on abstraction, not concrete classes

Example:
--------
    class MyExtractor(BaseExtractor):
        async def extract(self, text: str) -> ExtractResponse:
            # Implementation here
            return ExtractResponse(nodes=[], edges=[])
"""

from abc import ABC, abstractmethod
from schemas import ExtractResponse


class BaseExtractor(ABC):
    """
    Abstract base class for all extractors.

    Any extractor (rule-based, LLM-based, hybrid) must inherit from this
    and implement the extract() method.

    Learning Note - Why async?
    --------------------------
    We use async/await because:
    1. LLM API calls are network I/O (slow, blocking)
    2. FastAPI is async (non-blocking = handles more requests)
    3. Consistent interface for all extractors (even if some are sync)
    """

    @abstractmethod
    async def extract(self, text: str) -> ExtractResponse:
        """
        Extract entities (nodes) and relationships (edges) from text.

        This is the core method that all extractors must implement.

        Args:
            text: Raw input text to analyze

        Returns:
            ExtractResponse containing:
                - nodes: List of entities (id, label, type, confidence)
                - edges: List of relationships (source, target, relation)

        Example:
            Input: "Python is used for data science"
            Output: ExtractResponse(
                nodes=[
                    Node(id="python", label="Python", type="Tech", confidence=0.9),
                    Node(id="data-science", label="Data Science", type="Concept", confidence=0.85)
                ],
                edges=[
                    Edge(source="python", target="data-science", relation="used_for")
                ]
            )
        """
        pass  # Subclasses must implement

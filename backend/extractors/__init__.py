"""
Extractors Package
==================
Contains different extraction strategies for building knowledge graphs.

Available extractors:
- BaseExtractor: Abstract interface (contract)
- RuleBasedExtractor: Pattern matching extraction
- LLMExtractor: LLM-powered extraction (Gemini)

Design Pattern: Strategy Pattern
- Different extraction algorithms behind a common interface
- Easy to swap extractors at runtime via dependency injection
"""

from extractors.base import BaseExtractor

__all__ = ["BaseExtractor"]

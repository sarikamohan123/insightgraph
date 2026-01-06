"""
Prompts Package
===============
Centralized prompt templates for LLM interactions.

Benefits of separate prompt files:
1. Version control - track prompt changes over time
2. A/B testing - compare different prompts
3. Easy iteration - modify without touching logic code
4. Reusability - share prompts across extractors
"""

from prompts.extraction import NER_SYSTEM_PROMPT, build_extraction_prompt

__all__ = ["NER_SYSTEM_PROMPT", "build_extraction_prompt"]

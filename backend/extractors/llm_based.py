"""
LLM-Based Extractor
===================

Uses Large Language Models (Gemini) to extract entities and relationships
from unstructured text.

How it works:
1. Takes input text
2. Builds prompt with instructions and JSON schema
3. Sends to Gemini API
4. Parses and validates JSON response
5. Returns structured ExtractResponse

Advantages over Rule-Based:
---------------------------
- No predefined dictionary needed
- Understands context and semantics
- Can extract ANY entity type
- Handles complex relationships
- Learns from prompt examples

Disadvantages:
--------------
- API costs (per request)
- Slower than rule-based
- Requires internet connection
- Rate limits apply
- Non-deterministic (varies slightly per run)

Design Patterns Used:
---------------------
- **Strategy Pattern**: Implements BaseExtractor interface
- **Dependency Injection**: Receives GeminiService instance
- **Composition**: Uses service, doesn't inherit from it
"""

from prompts.extraction import NER_SYSTEM_PROMPT, build_extraction_prompt
from schemas import ExtractResponse
from services.llm_service import GeminiService

from extractors.base import BaseExtractor


class LLMExtractor(BaseExtractor):
    """
    LLM-powered entity and relationship extractor.

    Uses Google Gemini to intelligently extract structured knowledge graphs
    from unstructured text.

    Example:
        service = GeminiService()
        extractor = LLMExtractor(service)
        result = await extractor.extract("Python is used for data science")

        # Result contains nodes and edges extracted by LLM
        print(result.nodes)  # [Node(id="python", ...), Node(id="data-science", ...)]
        print(result.edges)  # [Edge(source="python", target="data-science", ...)]
    """

    def __init__(self, llm_service: GeminiService):
        """
        Initialize LLM extractor with service.

        Learning Note - Dependency Injection:
        We receive the GeminiService as a parameter instead of creating it here.
        Benefits:
        1. Easier testing (can pass mock service)
        2. Flexibility (can swap LLM providers)
        3. Single Responsibility (extractor doesn't manage API keys)

        Args:
            llm_service: Configured GeminiService instance
        """
        self.llm = llm_service

    async def extract(self, text: str) -> ExtractResponse:
        """
        Extract entities and relationships using LLM.

        This method:
        1. Builds prompt from template
        2. Calls Gemini API via service
        3. Returns validated Pydantic response

        The LLM service handles:
        - API communication
        - Retry logic
        - JSON parsing
        - Validation

        Args:
            text: Input text to analyze

        Returns:
            ExtractResponse with nodes and edges

        Raises:
            ValidationError: If LLM returns invalid JSON
            Exception: If API call fails after retries

        Example:
            result = await extractor.extract(
                "React is a JavaScript library for building UIs"
            )
            assert len(result.nodes) >= 2  # React, JavaScript, UIs
        """
        # Build prompt with our template
        prompt = build_extraction_prompt(text)

        # Call LLM and get structured response
        # The service handles all the complexity (API, retry, parsing)
        result = await self.llm.generate_structured(
            prompt=prompt, response_schema=ExtractResponse, system_instruction=NER_SYSTEM_PROMPT
        )

        return result

    async def extract_with_fallback(
        self, text: str, fallback_extractor: BaseExtractor
    ) -> ExtractResponse:
        """
        Extract with automatic fallback on failure.

        Learning Note - Resilience Pattern:
        If LLM fails (rate limit, API error), automatically fall back to
        rule-based extraction. This ensures the API never completely fails.

        Args:
            text: Input text
            fallback_extractor: Backup extractor (usually RuleBasedExtractor)

        Returns:
            ExtractResponse from LLM, or fallback if LLM fails

        Example:
            from extractors.rule_based import RuleBasedExtractor

            llm_ext = LLMExtractor(gemini_service)
            rule_ext = RuleBasedExtractor()

            # Will use LLM, or fallback to rules if it fails
            result = await llm_ext.extract_with_fallback(text, rule_ext)
        """
        try:
            return await self.extract(text)

        except Exception as e:
            print(f"[WARNING] LLM extraction failed: {e}")
            print(f"[INFO] Falling back to {fallback_extractor.__class__.__name__}")
            return await fallback_extractor.extract(text)

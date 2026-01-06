"""
LLM Service - Gemini API Integration
=====================================

Handles all communication with Google's Gemini API.

Key Responsibilities:
1. Initialize Gemini client with API key
2. Send prompts and receive structured responses
3. Retry logic with exponential backoff
4. Error handling for rate limits and API failures
5. Parse JSON responses into Pydantic models

Design Principles (SOLID):
- Single Responsibility: Only handles LLM API communication
- Open/Closed: Can extend with new methods without modifying existing
- Dependency Inversion: Returns abstractions (Pydantic models), not raw data
"""

import json
import asyncio
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from google.api_core import exceptions as google_exceptions

from config import settings


# Generic type for Pydantic models
T = TypeVar('T', bound=BaseModel)


class GeminiService:
    """
    Service for interacting with Google Gemini API.

    Usage:
        service = GeminiService()
        result = await service.generate_structured(
            prompt="Extract entities from: Python is great",
            response_schema=ExtractResponse
        )
    """

    def __init__(self, api_key: str | None = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize Gemini client.

        Args:
            api_key: Optional API key (defaults to settings.gemini_api_key)
            model_name: Model to use (default: gemini-2.5-flash - stable with good quotas)

        Recommended models:
            - gemini-2.5-flash: Fastest, best free tier (default)
            - gemini-2.5-pro: Higher quality, stricter limits
            - gemini-2.0-flash-001: Stable 2.0 version
        """
        self.api_key = api_key or settings.gemini_api_key
        genai.configure(api_key=self.api_key)

        # Use stable model with good free-tier quotas
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

        # Configuration for structured output
        self.generation_config = {
            "temperature": 0.1,  # Low temperature for consistent extraction
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        print(f"[INFO] Initialized Gemini with model: {model_name}")

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str | None = None
    ) -> T:
        """
        Generate structured output matching a Pydantic schema.

        This method:
        1. Sends prompt to Gemini
        2. Requests JSON response
        3. Parses and validates against Pydantic schema
        4. Retries on failure with exponential backoff

        Args:
            prompt: The input prompt for the LLM
            response_schema: Pydantic model class for validation
            system_instruction: Optional system-level instruction

        Returns:
            Validated Pydantic model instance

        Raises:
            ValidationError: If LLM response doesn't match schema
            Exception: If API call fails after retries

        Example:
            result = await service.generate_structured(
                prompt="Extract: Python is great",
                response_schema=ExtractResponse
            )
        """
        # Build the full prompt with JSON schema request
        full_prompt = self._build_json_prompt(prompt, response_schema)

        # Retry with exponential backoff
        return await self._retry_with_backoff(
            func=lambda: self._call_gemini(full_prompt, response_schema),
            max_retries=settings.max_retries
        )

    def _build_json_prompt(self, prompt: str, schema: Type[BaseModel]) -> str:
        """
        Build prompt that requests JSON matching Pydantic schema.

        Learning Note:
        We explicitly tell the LLM to return JSON in the schema format.
        This improves accuracy vs. hoping it returns the right structure.
        """
        schema_json = schema.model_json_schema()
        return f"""{prompt}

IMPORTANT: Return ONLY valid JSON matching this exact schema:
{json.dumps(schema_json, indent=2)}

Do not include any explanatory text, only the JSON object."""

    async def _call_gemini(
        self,
        prompt: str,
        response_schema: Type[T]
    ) -> T:
        """
        Make the actual API call to Gemini.

        Learning Note:
        - We use asyncio.to_thread() to make the blocking Gemini SDK call async
        - This prevents blocking the FastAPI event loop
        """
        # Run blocking Gemini call in thread pool
        response: GenerateContentResponse = await asyncio.to_thread(
            self.model.generate_content,
            prompt,
            generation_config=self.generation_config
        )

        # Extract text from response
        response_text = response.text.strip()

        # Parse JSON (remove markdown code blocks if present)
        response_text = self._clean_json_response(response_text)

        try:
            # Parse and validate with Pydantic
            data = json.loads(response_text)
            return response_schema.model_validate(data)

        except (json.JSONDecodeError, ValidationError) as e:
            print(f"[ERROR] Failed to parse LLM response: {e}")
            print(f"[ERROR] Raw response: {response_text[:200]}...")
            raise

    def _clean_json_response(self, text: str) -> str:
        """
        Remove markdown code blocks and extra whitespace.

        Learning Note:
        LLMs sometimes return: ```json {...} ```
        We need to extract just the JSON part.
        """
        # Remove markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json) and last line (```)
            text = "\n".join(lines[1:-1])

        return text.strip()

    async def _retry_with_backoff(
        self,
        func,
        max_retries: int = 3,
        base_delay: float = 1.0
    ):
        """
        Retry function with exponential backoff.

        Learning Note - Exponential Backoff:
        If API fails (rate limit, network issue), we retry with increasing delays:
        - Attempt 1: immediate
        - Attempt 2: wait 1s
        - Attempt 3: wait 2s
        - Attempt 4: wait 4s
        This prevents overwhelming the API and handles transient failures.

        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds

        Returns:
            Result from func if successful

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await func()

            except google_exceptions.ResourceExhausted as e:
                # Rate limit error - provide helpful message
                last_exception = e
                error_msg = str(e)

                print("\n" + "=" * 60)
                print(f"[RATE LIMIT] Gemini API quota exceeded")
                print("=" * 60)
                print(f"Model: {self.model_name}")
                print(f"Attempt: {attempt + 1}/{max_retries + 1}")

                # Extract retry time if available
                if "retry in" in error_msg.lower():
                    print(f"\nError details: {error_msg[:200]}...")
                else:
                    print(f"\nError: {error_msg[:300]}...")

                print("\nQuick fixes:")
                print("1. Wait a few minutes and try again")
                print("2. Check your quota: https://aistudio.google.com/usage")
                print("3. Switch to a different model (gemini-2.5-flash has better quotas)")
                print("4. Use the rule-based extractor as fallback")
                print("=" * 60 + "\n")

                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    print(f"[INFO] Retrying in {delay}s...\n")
                    await asyncio.sleep(delay)
                else:
                    print("[ERROR] All retry attempts exhausted")
                    print("[SUGGESTION] Use RuleBasedExtractor or wait for quota reset\n")

            except Exception as e:
                # Other errors (network, validation, etc.)
                last_exception = e
                error_type = type(e).__name__
                print(f"\n[WARNING] {error_type} on attempt {attempt + 1}/{max_retries + 1}")
                print(f"Error: {str(e)[:200]}")

                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    print(f"[INFO] Retrying in {delay}s...\n")
                    await asyncio.sleep(delay)
                else:
                    print(f"[ERROR] All {max_retries + 1} attempts failed\n")

        # All retries exhausted
        raise last_exception


# Convenience function for one-off calls
async def generate_structured(
    prompt: str,
    response_schema: Type[T],
    system_instruction: str | None = None
) -> T:
    """
    Convenience function for one-off LLM calls without creating service instance.

    Usage:
        from services.llm_service import generate_structured
        result = await generate_structured(prompt, ExtractResponse)
    """
    service = GeminiService()
    return await service.generate_structured(prompt, response_schema, system_instruction)

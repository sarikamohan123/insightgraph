"""
Cache Service - Result Caching Layer
=====================================

Caches extraction results to reduce LLM API costs.

Strategy:
- Cache key: SHA-256 hash of input text
- Cache TTL: 24 hours (configurable)
- Cache storage: Redis

Cost savings:
- Identical text → Same result from cache (no API call)
- Typical savings: 30-50% for repeated queries

Usage:
    result = await cache_service.get_or_compute(
        text="Python is great",
        compute_fn=lambda: extractor.extract(text)
    )
"""

import hashlib
import json
from typing import Any, Callable

from schemas import ExtractResponse
from services.redis_service import redis_service


class CacheService:
    """Service for caching extraction results."""

    CACHE_TTL = 24 * 3600  # 24 hours
    CACHE_PREFIX = "cache:extraction:"

    def _generate_cache_key(self, text: str) -> str:
        """
        Generate cache key from text.

        Uses SHA-256 hash to create deterministic key from text content.

        Args:
            text: Input text

        Returns:
            Cache key (e.g., "cache:extraction:a3f2b1...")
        """
        # Create hash of text content
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"{self.CACHE_PREFIX}{text_hash}"

    async def get(self, text: str) -> ExtractResponse | None:
        """
        Get cached result for text.

        Args:
            text: Input text to lookup

        Returns:
            Cached ExtractResponse if found, None otherwise
        """
        cache_key = self._generate_cache_key(text)
        cached_data = await redis_service.cache_get(cache_key)

        if cached_data:
            print(f"[Cache] HIT for key {cache_key[:30]}...")
            # Reconstruct ExtractResponse from cached dict
            return ExtractResponse(**cached_data)

        print(f"[Cache] MISS for key {cache_key[:30]}...")
        return None

    async def set(self, text: str, result: ExtractResponse):
        """
        Cache extraction result.

        Args:
            text: Input text (used to generate cache key)
            result: Extraction result to cache
        """
        cache_key = self._generate_cache_key(text)

        # Convert result to dict for JSON serialization
        result_dict = result.model_dump()

        # Store in Redis with TTL
        await redis_service.cache_set(cache_key, result_dict, ttl=self.CACHE_TTL)

        print(f"[Cache] SET key {cache_key[:30]}... (TTL: {self.CACHE_TTL}s)")

    async def get_or_compute(
        self, text: str, compute_fn: Callable[[], Any]
    ) -> ExtractResponse:
        """
        Get from cache or compute and cache result.

        This is the main method to use for caching.

        Args:
            text: Input text
            compute_fn: Async function to compute result if not cached

        Returns:
            ExtractResponse (from cache or freshly computed)

        Example:
            result = await cache_service.get_or_compute(
                text="Python is great",
                compute_fn=lambda: extractor.extract("Python is great")
            )
        """
        # Try to get from cache
        cached_result = await self.get(text)
        if cached_result:
            return cached_result

        # Not in cache - compute result
        result = await compute_fn()

        # Cache the result
        await self.set(text, result)

        return result

    async def invalidate(self, text: str):
        """
        Invalidate (delete) cached result for text.

        Args:
            text: Input text whose cache entry to delete
        """
        cache_key = self._generate_cache_key(text)
        await redis_service.cache_delete(cache_key)
        print(f"[Cache] INVALIDATED key {cache_key[:30]}...")

    async def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (total keys, etc.)
        """
        # Get all cache keys
        cache_keys = await redis_service.keys(f"{self.CACHE_PREFIX}*")

        return {
            "total_cached_results": len(cache_keys),
            "cache_ttl_seconds": self.CACHE_TTL,
            "cache_ttl_hours": self.CACHE_TTL / 3600,
        }


# Singleton instance
cache_service = CacheService()

"""
Tests for Cache Service
========================

Tests caching functionality:
- Cache hit/miss behavior
- Cache key generation
- TTL expiration
- get_or_compute pattern
"""

import pytest
from unittest.mock import AsyncMock, patch

from schemas import ExtractResponse, Edge, Node
from services.cache_service import CacheService


class TestCacheService:
    """Test suite for CacheService."""

    @pytest.fixture
    def cache_service(self):
        """Create cache service instance."""
        return CacheService()

    @pytest.fixture
    def sample_result(self):
        """Sample extraction result for testing."""
        return ExtractResponse(
            nodes=[
                Node(id="python", label="Python", type="Tech", confidence=0.95),
                Node(id="ai", label="AI", type="Concept", confidence=0.9),
            ],
            edges=[Edge(source="python", target="ai", relation="used_for")],
        )

    def test_generate_cache_key_deterministic(self, cache_service):
        """Test that same text generates same cache key."""
        text = "Python is great for AI"

        key1 = cache_service._generate_cache_key(text)
        key2 = cache_service._generate_cache_key(text)

        assert key1 == key2
        assert key1.startswith("cache:extraction:")

    def test_generate_cache_key_different_texts(self, cache_service):
        """Test that different texts generate different keys."""
        text1 = "Python is great"
        text2 = "JavaScript is awesome"

        key1 = cache_service._generate_cache_key(text1)
        key2 = cache_service._generate_cache_key(text2)

        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_service):
        """Test cache miss returns None."""
        with patch("services.cache_service.redis_service.cache_get", AsyncMock(return_value=None)):
            result = await cache_service.get("Some text that doesn't exist")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache_service, sample_result):
        """Test cache hit returns cached result."""
        # Mock Redis to return cached data
        cached_data = sample_result.model_dump()

        with patch("services.cache_service.redis_service.cache_get", AsyncMock(return_value=cached_data)):
            result = await cache_service.get("Python is great")

            assert result is not None
            assert isinstance(result, ExtractResponse)
            assert len(result.nodes) == 2
            assert result.nodes[0].label == "Python"

    @pytest.mark.asyncio
    async def test_cache_set(self, cache_service, sample_result):
        """Test caching a result."""
        mock_cache_set = AsyncMock()

        with patch("services.cache_service.redis_service.cache_set", mock_cache_set):
            await cache_service.set("Python is great", sample_result)

            # Verify cache_set was called
            mock_cache_set.assert_called_once()

            # Check arguments
            call_args = mock_cache_set.call_args
            assert call_args[0][0].startswith("cache:extraction:")  # Key
            assert "nodes" in call_args[0][1]  # Result dict
            assert call_args[1]["ttl"] == CacheService.CACHE_TTL  # TTL

    @pytest.mark.asyncio
    async def test_get_or_compute_cache_hit(self, cache_service, sample_result):
        """Test get_or_compute returns cached result without computing."""
        # Mock cache hit
        with patch.object(cache_service, "get", AsyncMock(return_value=sample_result)):
            compute_fn = AsyncMock()  # Should NOT be called

            result = await cache_service.get_or_compute("Python is great", compute_fn)

            assert result == sample_result
            compute_fn.assert_not_called()  # Compute function should not be called

    @pytest.mark.asyncio
    async def test_get_or_compute_cache_miss(self, cache_service, sample_result):
        """Test get_or_compute computes and caches on miss."""
        # Mock cache miss
        with patch.object(cache_service, "get", AsyncMock(return_value=None)), patch.object(
            cache_service, "set", AsyncMock()
        ):
            compute_fn = AsyncMock(return_value=sample_result)

            result = await cache_service.get_or_compute("Python is great", compute_fn)

            assert result == sample_result
            compute_fn.assert_called_once()  # Compute function SHOULD be called
            cache_service.set.assert_called_once()  # Result should be cached

    @pytest.mark.asyncio
    async def test_invalidate(self, cache_service):
        """Test cache invalidation."""
        mock_cache_delete = AsyncMock()

        with patch("services.cache_service.redis_service.cache_delete", mock_cache_delete):
            await cache_service.invalidate("Python is great")

            mock_cache_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stats(self, cache_service):
        """Test cache statistics."""
        # Mock Redis keys
        mock_keys = [
            "cache:extraction:abc123",
            "cache:extraction:def456",
            "cache:extraction:ghi789",
        ]

        with patch("services.cache_service.redis_service.keys", AsyncMock(return_value=mock_keys)):
            stats = await cache_service.get_stats()

            assert stats["total_cached_results"] == 3
            assert stats["cache_ttl_seconds"] == CacheService.CACHE_TTL
            assert stats["cache_ttl_hours"] == CacheService.CACHE_TTL / 3600

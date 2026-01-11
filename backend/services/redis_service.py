"""
Redis Service - Connection Management
======================================

Handles Redis connection, health checks, and key operations for:
- Rate limiting (request counters)
- Caching (extraction results)
- Job queuing (background tasks)

Design: Single Redis client instance with connection pooling.
"""

import json
from typing import Any

import redis.asyncio as redis
from config import settings


class RedisService:
    """
    Async Redis client wrapper with helper methods.

    Why async?
    - FastAPI is async, so we use async Redis to avoid blocking
    - Connection pooling handles multiple concurrent requests

    Usage:
        redis_service = RedisService()
        await redis_service.connect()
        count = await redis_service.increment("rate:user123", ttl=60)
    """

    def __init__(self):
        """Initialize Redis service (connection created on connect())."""
        self.redis: redis.Redis | None = None
        self._pool: redis.ConnectionPool | None = None

    async def connect(self):
        """
        Create Redis connection with connection pooling.

        Connection pool = Reuse connections instead of creating new ones.
        Benefits: Faster, uses less memory, handles concurrent requests.
        """
        if self.redis is not None:
            return  # Already connected

        # Create connection pool (max 10 connections)
        self._pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=10,
            decode_responses=True,  # Auto-decode bytes to strings
        )

        # Create Redis client with pool
        self.redis = redis.Redis(connection_pool=self._pool)

        print(f"[Redis] Connected to {settings.redis_url}")

    async def disconnect(self):
        """Close Redis connection and cleanup."""
        if self.redis:
            await self.redis.aclose()
            self.redis = None
        if self._pool:
            await self._pool.aclose()
            self._pool = None
        print("[Redis] Disconnected")

    async def ping(self) -> bool:
        """
        Health check - verify Redis is responding.

        Returns:
            True if Redis responds to PING
        """
        if not self.redis:
            return False
        try:
            return await self.redis.ping()
        except Exception as e:
            print(f"[Redis] Ping failed: {e}")
            return False

    # ========================================================================
    # Rate Limiting Operations
    # ========================================================================

    async def increment(self, key: str, ttl: int | None = None) -> int:
        """
        Increment counter and optionally set expiration.

        Used for rate limiting: count requests per time window.

        Args:
            key: Redis key (e.g., "rate:user123")
            ttl: Time to live in seconds (key auto-expires)

        Returns:
            New count after increment

        Example:
            count = await redis.increment("rate:user123", ttl=60)
            if count > 15:  # More than 15 requests in 60 seconds
                raise RateLimitError()
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        # Increment counter (creates key if doesn't exist)
        count = await self.redis.incr(key)

        # Set expiration if this is the first increment
        if count == 1 and ttl:
            await self.redis.expire(key, ttl)

        return count

    async def get_count(self, key: str) -> int:
        """
        Get current count for a key.

        Returns:
            Current count (0 if key doesn't exist)
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        value = await self.redis.get(key)
        return int(value) if value else 0

    async def get_ttl(self, key: str) -> int:
        """
        Get remaining time-to-live for a key.

        Returns:
            Seconds until key expires (-1 if no expiration, -2 if key doesn't exist)
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        return await self.redis.ttl(key)

    # ========================================================================
    # Caching Operations
    # ========================================================================

    async def cache_set(self, key: str, value: Any, ttl: int = 3600):
        """
        Cache a value (typically JSON).

        Args:
            key: Cache key (e.g., "cache:hash_abc123")
            value: Any JSON-serializable value
            ttl: Time to live in seconds (default: 1 hour)

        Example:
            await redis.cache_set(
                "cache:python_text",
                {"nodes": [...], "edges": [...]},
                ttl=3600
            )
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        # Serialize to JSON
        json_value = json.dumps(value)

        # Store with expiration
        await self.redis.setex(key, ttl, json_value)

    async def cache_get(self, key: str) -> Any | None:
        """
        Get cached value.

        Returns:
            Deserialized value if found, None if not found or expired
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def cache_delete(self, key: str):
        """Delete a cache entry."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        await self.redis.delete(key)

    # ========================================================================
    # Queue Operations (for background jobs)
    # ========================================================================

    async def queue_push(self, queue_name: str, item: dict):
        """
        Push item to queue (FIFO - First In First Out).

        Args:
            queue_name: Queue identifier (e.g., "extraction_jobs")
            item: Job data (dict)

        Example:
            await redis.queue_push("extraction_jobs", {
                "job_id": "abc123",
                "text": "Python is great",
                "user_id": "user123"
            })
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        json_item = json.dumps(item)
        await self.redis.rpush(queue_name, json_item)

    async def queue_pop(self, queue_name: str, timeout: int = 0) -> dict | None:
        """
        Pop item from queue (blocking).

        Args:
            queue_name: Queue identifier
            timeout: Block for N seconds waiting for item (0 = block forever)

        Returns:
            Job data dict if available, None if timeout

        Example:
            job = await redis.queue_pop("extraction_jobs", timeout=5)
            if job:
                process_job(job)
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        result = await self.redis.blpop(queue_name, timeout=timeout)
        if result:
            _, json_item = result  # Returns (queue_name, item)
            return json.loads(json_item)
        return None

    async def queue_length(self, queue_name: str) -> int:
        """Get number of items in queue."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        return await self.redis.llen(queue_name)

    # ========================================================================
    # Utility Operations
    # ========================================================================

    async def delete(self, key: str):
        """Delete a key."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        return bool(await self.redis.exists(key))

    async def keys(self, pattern: str = "*") -> list[str]:
        """
        Get all keys matching pattern.

        Warning: Use carefully in production (can be slow with many keys).

        Args:
            pattern: Glob pattern (e.g., "rate:*", "cache:*")
        """
        if not self.redis:
            raise RuntimeError("Redis not connected")

        return await self.redis.keys(pattern)


# Singleton instance
redis_service = RedisService()

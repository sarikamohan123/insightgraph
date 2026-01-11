"""Quick test to verify Redis connection works"""

import asyncio

from services.redis_service import RedisService


async def test_redis():
    redis = RedisService()

    print("Testing Redis connection...")

    # Connect
    await redis.connect()
    print("Connected to Redis")

    # Ping
    pong = await redis.ping()
    print(f"Ping: {pong}")

    # Test increment (rate limiting)
    count1 = await redis.increment("test:counter", ttl=60)
    print(f"Increment 1: {count1}")

    count2 = await redis.increment("test:counter")
    print(f"Increment 2: {count2}")

    # Test caching
    await redis.cache_set("test:cache", {"message": "Hello Redis!"}, ttl=300)
    cached = await redis.cache_get("test:cache")
    print(f"Cached value: {cached}")

    # Cleanup
    await redis.delete("test:counter")
    await redis.delete("test:cache")
    await redis.disconnect()

    print("\nAll Redis tests passed!")


if __name__ == "__main__":
    asyncio.run(test_redis())

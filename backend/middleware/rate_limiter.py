"""
Rate Limiter Middleware
========================

Prevents API abuse and quota exhaustion using Redis-based rate limiting.

Features:
- Per-IP rate limiting (prevents individual users from spam)
- Global rate limiting (prevents total API overload)
- Sliding window algorithm (accurate counting)
- Returns HTTP 429 with Retry-After header

Usage in FastAPI:
    @app.post("/extract", dependencies=[Depends(rate_limit)])
    async def extract(...):
        ...
"""

from fastapi import HTTPException, Request, status
from services.redis_service import redis_service


class RateLimitConfig:
    """Rate limiting configuration."""

    # Per-IP limits (prevent individual abuse)
    PER_IP_REQUESTS = 10  # Max requests per IP
    PER_IP_WINDOW = 60  # In 60 seconds

    # Global limits (prevent total API overload)
    GLOBAL_REQUESTS = 15  # Max total requests (matches Gemini free tier)
    GLOBAL_WINDOW = 60  # In 60 seconds


async def rate_limit(request: Request):
    """
    Rate limit middleware using Redis.

    Checks:
    1. Per-IP limit: Individual user can't make too many requests
    2. Global limit: Total API requests stay within Gemini quota

    Args:
        request: FastAPI Request object

    Raises:
        HTTPException(429): Too Many Requests

    How it works:
        1. Get user IP address
        2. Increment Redis counter for this IP
        3. Check if count exceeds limit
        4. If exceeded, return 429 with Retry-After header
        5. If OK, allow request to proceed

    Example:
        Request 1 from 192.168.1.1 → Count: 1/10 ✅
        Request 2 from 192.168.1.1 → Count: 2/10 ✅
        ...
        Request 11 from 192.168.1.1 → Count: 11/10 ❌ Rate limited!
    """
    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"

    # Redis keys for rate limiting
    ip_key = f"rate_limit:ip:{client_ip}"
    global_key = "rate_limit:global"

    # Check per-IP rate limit
    ip_count = await redis_service.increment(ip_key, ttl=RateLimitConfig.PER_IP_WINDOW)

    if ip_count > RateLimitConfig.PER_IP_REQUESTS:
        # Get remaining TTL for retry-after header
        ttl = await redis_service.get_ttl(ip_key)
        retry_after = max(ttl, 1)  # At least 1 second

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "limit": RateLimitConfig.PER_IP_REQUESTS,
                "window": f"{RateLimitConfig.PER_IP_WINDOW} seconds",
                "retry_after": f"{retry_after} seconds",
            },
            headers={"Retry-After": str(retry_after)},
        )

    # Check global rate limit (all users combined)
    global_count = await redis_service.increment(
        global_key, ttl=RateLimitConfig.GLOBAL_WINDOW
    )

    if global_count > RateLimitConfig.GLOBAL_REQUESTS:
        ttl = await redis_service.get_ttl(global_key)
        retry_after = max(ttl, 1)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Global rate limit exceeded",
                "message": "API is temporarily at capacity. Please try again in a moment.",
                "limit": RateLimitConfig.GLOBAL_REQUESTS,
                "window": f"{RateLimitConfig.GLOBAL_WINDOW} seconds",
                "retry_after": f"{retry_after} seconds",
            },
            headers={"Retry-After": str(retry_after)},
        )

    # Rate limit OK - request can proceed
    return True


# Helper function to get current rate limit status
async def get_rate_limit_status(client_ip: str) -> dict:
    """
    Get current rate limit status for a client.

    Useful for monitoring dashboards.

    Returns:
        {
            "ip_requests": 5,
            "ip_limit": 10,
            "ip_remaining": 5,
            "ip_resets_in": 45,
            "global_requests": 12,
            "global_limit": 15,
            "global_remaining": 3,
            "global_resets_in": 30
        }
    """
    ip_key = f"rate_limit:ip:{client_ip}"
    global_key = "rate_limit:global"

    # Get current counts
    ip_count = await redis_service.get_count(ip_key)
    global_count = await redis_service.get_count(global_key)

    # Get TTLs
    ip_ttl = await redis_service.get_ttl(ip_key)
    global_ttl = await redis_service.get_ttl(global_key)

    return {
        "ip_requests": ip_count,
        "ip_limit": RateLimitConfig.PER_IP_REQUESTS,
        "ip_remaining": max(0, RateLimitConfig.PER_IP_REQUESTS - ip_count),
        "ip_resets_in": max(0, ip_ttl),
        "global_requests": global_count,
        "global_limit": RateLimitConfig.GLOBAL_REQUESTS,
        "global_remaining": max(0, RateLimitConfig.GLOBAL_REQUESTS - global_count),
        "global_resets_in": max(0, global_ttl),
    }

"""
InsightGraph API
================
FastAPI backend for knowledge graph extraction.

Main application file with:
- System endpoints (health, stats, rate-limit-status)
- Router registration
- Application lifecycle management

All feature endpoints are organized in routers/:
- routers/extraction.py - /extract endpoint
- routers/jobs.py - /jobs endpoints
- routers/graphs.py - /graphs CRUD endpoints
"""

from config import settings
from fastapi import FastAPI, Request
from middleware.rate_limiter import get_rate_limit_status
from routers import extraction, graphs, jobs
from services.cache_service import cache_service
from services.db_service import check_db_connection, close_db
from services.job_service import job_service
from services.redis_service import redis_service

# Initialize FastAPI app
app = FastAPI(
    title="InsightGraph API",
    description="Transform unstructured text into knowledge graphs using LLMs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
app.include_router(extraction.router)  # /extract
app.include_router(jobs.router)  # /jobs
app.include_router(graphs.router)  # /graphs


# Health check endpoint
@app.get("/health", tags=["System"], summary="Health check", response_model=dict)
async def health():
    """
    Check if the API is running.

    Returns:
        Simple status message
    """
    return {"status": "ok", "extractor": "LLM" if settings.use_llm_extractor else "Rule-based"}


# Rate limit status endpoint
@app.get(
    "/rate-limit-status",
    tags=["System"],
    summary="Get rate limit status",
    response_model=dict,
)
async def rate_limit_status(request: Request):
    """
    Check current rate limit status for your IP.

    Returns:
        Rate limit information including remaining requests and reset time
    """
    client_ip = request.client.host if request.client else "unknown"
    status = await get_rate_limit_status(client_ip)
    return status


# System statistics endpoint
@app.get(
    "/stats",
    tags=["System"],
    summary="Get system statistics and monitoring data",
    response_model=dict,
)
async def system_stats():
    """
    Get comprehensive system statistics.

    Returns statistics about:
    - Cache: Hit/miss counts, total cached results
    - Queue: Pending jobs, queue length
    - Redis health
    - Extractor type

    Useful for:
    - Monitoring dashboards
    - Performance optimization
    - Cost tracking (cache hit rate = cost savings)
    """
    # Get cache stats
    cache_stats = await cache_service.get_stats()

    # Get queue stats
    queue_length = await job_service.get_queue_length()

    # Get Redis health
    redis_healthy = await redis_service.ping()

    return {
        "redis": {
            "healthy": redis_healthy,
            "connected": redis_service.redis is not None,
        },
        "cache": cache_stats,
        "queue": {
            "pending_jobs": queue_length,
        },
        "extractor": {
            "type": "LLM (Gemini)" if settings.use_llm_extractor else "Rule-based",
            "model": "gemini-2.0-flash-exp" if settings.use_llm_extractor else "N/A",
        },
        "authentication": {
            "enabled": settings.api_key is not None,
        },
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services and print startup information"""
    print("\n" + "=" * 60)
    print("InsightGraph API Starting...")
    print("=" * 60)

    # Check database connectivity and schema
    try:
        db_ready = await check_db_connection()
        if db_ready:
            print("Database: Connected and ready")
        else:
            print("Database: Connected but schema missing")
            print("         Run: alembic upgrade head")
    except Exception as e:
        print(f"Database: Connection failed - {e}")
        print("         Check DATABASE_URL in .env")

    # Connect to Redis
    await redis_service.connect()
    redis_healthy = await redis_service.ping()
    print(f"Redis: {'Connected' if redis_healthy else 'Not connected'}")

    print(f"Extractor: {'LLM (Gemini)' if settings.use_llm_extractor else 'Rule-based'}")
    print(f"Authentication: {'Enabled' if settings.api_key else 'Disabled (dev mode)'}")
    print(f"Docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    print("\n" + "=" * 60)
    print("InsightGraph API Shutting Down...")
    print("=" * 60)

    # Disconnect Redis
    await redis_service.disconnect()

    # Close database connections
    await close_db()

    print("Shutdown complete")
    print("=" * 60 + "\n")

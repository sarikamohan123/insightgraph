"""
InsightGraph API
================
FastAPI backend for knowledge graph extraction.

Endpoints:
- GET  /health: Health check
- POST /extract: Extract entities and relationships from text (sync)
- POST /jobs: Create async extraction job
- GET  /jobs/{job_id}: Get job status and results

Architecture:
- Uses dependency injection to swap extractors (LLM vs Rule-based)
- Async endpoints for non-blocking I/O
- Type-safe with Pydantic models
- Redis-backed job queue for async processing
"""

from datetime import datetime
from typing import Annotated

from config import settings
from extractors.base import BaseExtractor
from extractors.llm_based import LLMExtractor
from extractors.rule_based import RuleBasedExtractor
from fastapi import Depends, FastAPI, HTTPException, Request, status
from middleware.rate_limiter import get_rate_limit_status, rate_limit
from models.job import JobRequest, JobResponse, JobStatus, JobStatusResponse
from pydantic import BaseModel, Field
from schemas import ExtractResponse
from services.cache_service import cache_service
from services.job_service import job_service
from services.llm_service import GeminiService
from services.redis_service import redis_service

# Initialize FastAPI app
app = FastAPI(
    title="InsightGraph API",
    description="Transform unstructured text into knowledge graphs using LLMs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Request/Response models
class ExtractRequest(BaseModel):
    """Request for entity extraction"""

    text: str = Field(
        ...,
        description="Input text to analyze",
        min_length=1,
        max_length=10000,
        examples=["Python is used for data science and web development"],
    )


# Dependency Injection: Provide extractor based on configuration
def get_extractor() -> BaseExtractor:
    """
    Dependency injection for extractor.

    Learning Note - Dependency Injection:
    FastAPI calls this function to create the extractor.
    We can easily swap implementations by changing settings
    or for testing by overriding this dependency.

    Returns:
        LLMExtractor if USE_LLM_EXTRACTOR=true, else RuleBasedExtractor

    Example override for testing:
        app.dependency_overrides[get_extractor] = lambda: MockExtractor()
    """
    if settings.use_llm_extractor:
        print("[INFO] Using LLM-based extraction")
        llm_service = GeminiService()
        return LLMExtractor(llm_service)
    else:
        print("[INFO] Using rule-based extraction")
        return RuleBasedExtractor()


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
    - Rate limiting: Current usage

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
    }


# Main extraction endpoint
@app.post(
    "/extract",
    tags=["Extraction"],
    summary="Extract knowledge graph from text",
    response_model=ExtractResponse,
    responses={
        200: {
            "description": "Successfully extracted entities and relationships",
            "content": {
                "application/json": {
                    "example": {
                        "nodes": [
                            {"id": "python", "label": "Python", "type": "Tech", "confidence": 0.95},
                            {
                                "id": "data-science",
                                "label": "Data Science",
                                "type": "Concept",
                                "confidence": 0.9,
                            },
                        ],
                        "edges": [
                            {"source": "python", "target": "data-science", "relation": "used_for"}
                        ],
                    }
                }
            },
        },
        429: {"description": "Rate limit exceeded - too many requests"},
        500: {"description": "Extraction failed (API error, etc.)"},
    },
    dependencies=[Depends(rate_limit)],  # Add rate limiting
)
async def extract(req: ExtractRequest, extractor: Annotated[BaseExtractor, Depends(get_extractor)]):
    """
    Extract entities (nodes) and relationships (edges) from text.

    This endpoint:
    1. Takes unstructured text as input
    2. Checks cache for previous identical requests (saves API costs!)
    3. If not cached, extracts entities (Tech, Concepts, People, etc.)
    4. Identifies relationships between entities
    5. Caches result for 24 hours
    6. Returns a structured knowledge graph

    Learning Note - Dependency Injection:
    The `extractor` parameter is automatically provided by FastAPI
    via the `Depends(get_extractor)` annotation. This means:
    - We don't create the extractor inside this function
    - Easy to swap extractors (LLM vs Rule-based)
    - Easy to test (can inject mock extractor)

    Args:
        req: ExtractRequest with text field
        extractor: Injected by FastAPI (LLM or Rule-based)

    Returns:
        ExtractResponse with nodes and edges

    Raises:
        HTTPException(500): If extraction fails
    """
    try:
        # Use cache to avoid redundant API calls
        result = await cache_service.get_or_compute(
            text=req.text, compute_fn=lambda: extractor.extract(req.text)
        )
        return result

    except Exception as e:
        # Log error and return HTTP 500
        print(f"[ERROR] Extraction failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Extraction failed: {str(e)[:200]}"
        ) from e  # Preserve exception chain for better debugging


# Async job endpoints
@app.post(
    "/jobs",
    tags=["Jobs"],
    summary="Create async extraction job",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Job created successfully"},
        429: {"description": "Rate limit exceeded"},
    },
    dependencies=[Depends(rate_limit)],
)
async def create_job(req: JobRequest):
    """
    Create an async extraction job (for slow LLM processing).

    Use this endpoint when:
    - You want non-blocking requests (get job ID immediately)
    - You're OK with polling for results
    - Processing might take > 5 seconds

    Workflow:
    1. POST /jobs with text → Receive job_id
    2. Poll GET /jobs/{job_id} → Check status
    3. When status=completed → Get result

    Args:
        req: JobRequest with text field

    Returns:
        JobResponse with job_id and status
    """
    job_id = await job_service.create_job(req.text)
    queue_length = await job_service.get_queue_length()

    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=datetime.utcnow(),
        message=f"Job created. Queue position: {queue_length}",
    )


@app.get(
    "/jobs/{job_id}",
    tags=["Jobs"],
    summary="Get job status and results",
    response_model=JobStatusResponse,
    responses={
        200: {"description": "Job found"},
        404: {"description": "Job not found or expired"},
    },
)
async def get_job_status(job_id: str):
    """
    Check status of an async extraction job.

    Poll this endpoint to check if your job is complete.

    Job statuses:
    - pending: Waiting in queue
    - processing: Currently being processed
    - completed: Done! Result available
    - failed: Error occurred

    Args:
        job_id: Job identifier from POST /jobs

    Returns:
        JobStatusResponse with status and result (if completed)
    """
    job = await job_service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or expired",
        )

    # Calculate progress
    progress = {
        JobStatus.PENDING: 0,
        JobStatus.PROCESSING: 50,
        JobStatus.COMPLETED: 100,
        JobStatus.FAILED: 100,
    }[job.status]

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        result=job.result,
        error=job.error,
        progress=progress,
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services and print startup information"""
    print("\n" + "=" * 60)
    print("InsightGraph API Starting...")
    print("=" * 60)

    # Connect to Redis
    await redis_service.connect()
    redis_healthy = await redis_service.ping()
    print(f"Redis: {'Connected' if redis_healthy else 'Not connected'}")

    print(f"Extractor: {'LLM (Gemini)' if settings.use_llm_extractor else 'Rule-based'}")
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

    print("Shutdown complete")
    print("=" * 60 + "\n")

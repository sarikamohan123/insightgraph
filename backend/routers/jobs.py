"""
Async Job API Endpoints
========================

Endpoints for managing async extraction jobs.

Endpoints:
- POST /jobs - Create async extraction job
- GET /jobs/{job_id} - Get job status and results
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from middleware.rate_limiter import rate_limit
from models.job import JobRequest, JobResponse, JobStatus, JobStatusResponse
from services.job_service import job_service

# Create router
router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
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

    Note: This endpoint is public (rate-limited).

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


@router.get(
    "/{job_id}",
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

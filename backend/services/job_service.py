"""
Job Service - Request Queue Management
=======================================

Handles async job creation, storage, and retrieval using Redis.

Architecture:
- Jobs stored as JSON in Redis with 1-hour TTL
- Job IDs are UUIDs for uniqueness
- Job queue implemented as Redis list (FIFO)
- Background worker pops jobs and processes them

Usage:
    job_id = await job_service.create_job("Python is great")
    status = await job_service.get_job_status(job_id)
    await job_service.update_job_status(job_id, JobStatus.COMPLETED, result={...})
"""

import uuid
from datetime import datetime

from models.job import Job, JobStatus
from services.redis_service import redis_service


class JobService:
    """Service for managing extraction jobs."""

    JOB_TTL = 3600  # Jobs expire after 1 hour
    QUEUE_NAME = "extraction_jobs"  # Redis queue name

    async def create_job(self, text: str) -> str:
        """
        Create a new extraction job and add it to the queue.

        Args:
            text: Input text to extract from

        Returns:
            job_id: Unique job identifier

        Workflow:
            1. Generate unique job ID
            2. Create job object with PENDING status
            3. Store job in Redis (key: job:{job_id})
            4. Push job ID to queue for worker to process
        """
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Create job object
        job = Job(
            job_id=job_id,
            text=text,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        # Store job in Redis with 1-hour expiration
        job_key = f"job:{job_id}"
        await redis_service.cache_set(job_key, job.model_dump(), ttl=self.JOB_TTL)

        # Add job to processing queue
        await redis_service.queue_push(self.QUEUE_NAME, {"job_id": job_id})

        print(f"[JobService] Created job {job_id}")
        return job_id

    async def get_job(self, job_id: str) -> Job | None:
        """
        Retrieve job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job object if found, None if not found or expired
        """
        job_key = f"job:{job_id}"
        job_data = await redis_service.cache_get(job_key)

        if not job_data:
            return None

        # Convert ISO datetime strings back to datetime objects
        if "created_at" in job_data:
            job_data["created_at"] = datetime.fromisoformat(job_data["created_at"])
        if job_data.get("completed_at"):
            job_data["completed_at"] = datetime.fromisoformat(job_data["completed_at"])

        return Job(**job_data)

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: dict | None = None,
        error: str | None = None,
    ):
        """
        Update job status and result.

        Args:
            job_id: Job identifier
            status: New status (PROCESSING, COMPLETED, FAILED)
            result: Extraction result (for COMPLETED status)
            error: Error message (for FAILED status)
        """
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update job fields
        job.status = status
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job.completed_at = datetime.utcnow()
        if result:
            job.result = result
        if error:
            job.error = error

        # Save updated job back to Redis
        job_key = f"job:{job_id}"
        await redis_service.cache_set(job_key, job.model_dump(), ttl=self.JOB_TTL)

        print(f"[JobService] Updated job {job_id} -> {status}")

    async def get_queue_length(self) -> int:
        """Get number of jobs waiting in queue."""
        return await redis_service.queue_length(self.QUEUE_NAME)

    async def get_next_job(self, timeout: int = 5) -> str | None:
        """
        Get next job from queue (used by background worker).

        Args:
            timeout: Seconds to wait for a job (0 = block forever)

        Returns:
            job_id if available, None if timeout
        """
        job_data = await redis_service.queue_pop(self.QUEUE_NAME, timeout=timeout)
        if job_data:
            return job_data["job_id"]
        return None


# Singleton instance
job_service = JobService()

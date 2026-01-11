"""
Job Models - Request Queue System
===================================

Data models for async job processing.

Job lifecycle:
1. PENDING: Job submitted, waiting in queue
2. PROCESSING: Worker is processing the job
3. COMPLETED: Job finished successfully
4. FAILED: Job failed with error

Jobs are stored in Redis with automatic cleanup after 1 hour.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRequest(BaseModel):
    """Request to create a new extraction job."""

    text: str = Field(
        ...,
        description="Text to extract knowledge graph from",
        min_length=1,
        max_length=10000,
    )


class JobResponse(BaseModel):
    """Response when creating a new job."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    message: str = Field(..., description="Status message")


class JobStatusResponse(BaseModel):
    """Response when checking job status."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    result: dict | None = Field(None, description="Extraction result (nodes + edges)")
    error: str | None = Field(None, description="Error message if failed")
    progress: int = Field(..., description="Progress percentage (0-100)")


class Job(BaseModel):
    """Internal job representation stored in Redis."""

    job_id: str
    text: str
    status: JobStatus
    created_at: datetime
    completed_at: datetime | None = None
    result: dict | None = None
    error: str | None = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

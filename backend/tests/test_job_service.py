"""
Tests for Job Service
======================

Tests job queue functionality:
- Job creation and storage
- Job status updates
- Queue operations
- Job lifecycle
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from models.job import Job, JobStatus
from services.job_service import JobService


class TestJobService:
    """Test suite for JobService."""

    @pytest.fixture
    def job_service(self):
        """Create job service instance."""
        return JobService()

    @pytest.mark.asyncio
    async def test_create_job(self, job_service):
        """Test creating a new job."""
        text = "Python is used for data science"

        with patch("services.job_service.redis_service.cache_set", AsyncMock()), patch(
            "services.job_service.redis_service.queue_push", AsyncMock()
        ):
            job_id = await job_service.create_job(text)

            # Check job_id is a valid UUID
            assert job_id is not None
            assert len(job_id) == 36  # UUID format: 8-4-4-4-12
            assert "-" in job_id

    @pytest.mark.asyncio
    async def test_create_job_stores_in_redis(self, job_service):
        """Test that creating a job stores it in Redis."""
        text = "Python is great"
        mock_cache_set = AsyncMock()
        mock_queue_push = AsyncMock()

        with patch("services.job_service.redis_service.cache_set", mock_cache_set), patch(
            "services.job_service.redis_service.queue_push", mock_queue_push
        ):
            job_id = await job_service.create_job(text)

            # Verify job was stored in Redis
            mock_cache_set.assert_called_once()
            call_args = mock_cache_set.call_args

            # Check cache key
            assert call_args[0][0] == f"job:{job_id}"

            # Check job data
            job_data = call_args[0][1]
            assert job_data["text"] == text
            assert job_data["status"] == JobStatus.PENDING

            # Check TTL
            assert call_args[1]["ttl"] == JobService.JOB_TTL

    @pytest.mark.asyncio
    async def test_create_job_adds_to_queue(self, job_service):
        """Test that creating a job adds it to the queue."""
        text = "Python is great"
        mock_queue_push = AsyncMock()

        with patch("services.job_service.redis_service.cache_set", AsyncMock()), patch(
            "services.job_service.redis_service.queue_push", mock_queue_push
        ):
            job_id = await job_service.create_job(text)

            # Verify job was added to queue
            mock_queue_push.assert_called_once()
            queue_item = mock_queue_push.call_args[0][1]
            assert queue_item["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_get_job_found(self, job_service):
        """Test retrieving an existing job."""
        job_id = "test-job-123"
        job_data = {
            "job_id": job_id,
            "text": "Python is great",
            "status": JobStatus.PENDING,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "result": None,
            "error": None,
        }

        with patch("services.job_service.redis_service.cache_get", AsyncMock(return_value=job_data)):
            job = await job_service.get_job(job_id)

            assert job is not None
            assert job.job_id == job_id
            assert job.text == "Python is great"
            assert job.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, job_service):
        """Test retrieving a non-existent job."""
        with patch("services.job_service.redis_service.cache_get", AsyncMock(return_value=None)):
            job = await job_service.get_job("nonexistent-job")
            assert job is None

    @pytest.mark.asyncio
    async def test_update_job_status_to_processing(self, job_service):
        """Test updating job status to PROCESSING."""
        job_id = "test-job-123"
        existing_job = Job(
            job_id=job_id,
            text="Python is great",
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        with patch.object(job_service, "get_job", AsyncMock(return_value=existing_job)), patch(
            "services.job_service.redis_service.cache_set", AsyncMock()
        ) as mock_cache_set:
            await job_service.update_job_status(job_id, JobStatus.PROCESSING)

            # Verify status was updated
            call_args = mock_cache_set.call_args
            updated_job_data = call_args[0][1]
            assert updated_job_data["status"] == JobStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_update_job_status_to_completed(self, job_service):
        """Test updating job status to COMPLETED with result."""
        job_id = "test-job-123"
        existing_job = Job(
            job_id=job_id,
            text="Python is great",
            status=JobStatus.PROCESSING,
            created_at=datetime.utcnow(),
        )
        result = {"nodes": [], "edges": []}

        with patch.object(job_service, "get_job", AsyncMock(return_value=existing_job)), patch(
            "services.job_service.redis_service.cache_set", AsyncMock()
        ) as mock_cache_set:
            await job_service.update_job_status(job_id, JobStatus.COMPLETED, result=result)

            # Verify status and result were updated
            call_args = mock_cache_set.call_args
            updated_job_data = call_args[0][1]
            assert updated_job_data["status"] == JobStatus.COMPLETED
            assert updated_job_data["result"] == result
            assert updated_job_data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_update_job_status_to_failed(self, job_service):
        """Test updating job status to FAILED with error."""
        job_id = "test-job-123"
        existing_job = Job(
            job_id=job_id,
            text="Python is great",
            status=JobStatus.PROCESSING,
            created_at=datetime.utcnow(),
        )
        error = "API error occurred"

        with patch.object(job_service, "get_job", AsyncMock(return_value=existing_job)), patch(
            "services.job_service.redis_service.cache_set", AsyncMock()
        ) as mock_cache_set:
            await job_service.update_job_status(job_id, JobStatus.FAILED, error=error)

            # Verify status and error were updated
            call_args = mock_cache_set.call_args
            updated_job_data = call_args[0][1]
            assert updated_job_data["status"] == JobStatus.FAILED
            assert updated_job_data["error"] == error
            assert updated_job_data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_update_job_not_found_raises_error(self, job_service):
        """Test that updating a non-existent job raises ValueError."""
        with patch.object(job_service, "get_job", AsyncMock(return_value=None)):
            with pytest.raises(ValueError, match="Job .* not found"):
                await job_service.update_job_status("nonexistent-job", JobStatus.COMPLETED)

    @pytest.mark.asyncio
    async def test_get_queue_length(self, job_service):
        """Test getting queue length."""
        with patch("services.job_service.redis_service.queue_length", AsyncMock(return_value=5)):
            length = await job_service.get_queue_length()
            assert length == 5

    @pytest.mark.asyncio
    async def test_get_next_job(self, job_service):
        """Test getting next job from queue."""
        job_id = "test-job-123"

        with patch(
            "services.job_service.redis_service.queue_pop",
            AsyncMock(return_value={"job_id": job_id}),
        ):
            next_job_id = await job_service.get_next_job(timeout=5)
            assert next_job_id == job_id

    @pytest.mark.asyncio
    async def test_get_next_job_empty_queue(self, job_service):
        """Test getting next job from empty queue."""
        with patch("services.job_service.redis_service.queue_pop", AsyncMock(return_value=None)):
            next_job_id = await job_service.get_next_job(timeout=1)
            assert next_job_id is None

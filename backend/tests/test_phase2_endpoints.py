"""
Tests for Phase 2 API Endpoints
=================================

Tests new endpoints added in Phase 2:
- POST /jobs - Create async extraction job
- GET /jobs/{job_id} - Get job status
- GET /stats - System statistics
- GET /rate-limit-status - Rate limit info
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from models.job import Job, JobStatus
from schemas import ExtractResponse, Edge, Node


client = TestClient(app)


class TestJobEndpoints:
    """Test suite for async job endpoints."""

    def test_create_job_success(self):
        """Test creating a new extraction job."""
        mock_create_job = AsyncMock(return_value="test-job-123")
        mock_get_queue_length = AsyncMock(return_value=3)

        with patch("main.job_service.create_job", mock_create_job), patch(
            "main.job_service.get_queue_length", mock_get_queue_length
        ), patch("main.rate_limit", AsyncMock(return_value=True)):
            response = client.post("/jobs", json={"text": "Python is great for AI"})

            assert response.status_code == 201
            data = response.json()
            assert data["job_id"] == "test-job-123"
            assert data["status"] == "pending"
            assert "Queue position: 3" in data["message"]

    def test_create_job_validation_error(self):
        """Test creating job with invalid input."""
        # Empty text should fail validation
        response = client.post("/jobs", json={"text": ""})

        assert response.status_code == 422  # Validation error
        assert "detail" in response.json()

    def test_create_job_text_too_long(self):
        """Test creating job with text exceeding max length."""
        long_text = "x" * 10001  # Exceeds 10000 char limit

        response = client.post("/jobs", json={"text": long_text})

        assert response.status_code == 422  # Validation error

    def test_get_job_status_pending(self):
        """Test getting status of a pending job."""
        job = Job(
            job_id="test-job-123",
            text="Python is great",
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        with patch("main.job_service.get_job", AsyncMock(return_value=job)):
            response = client.get("/jobs/test-job-123")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "test-job-123"
            assert data["status"] == "pending"
            assert data["progress"] == 0
            assert data["result"] is None

    def test_get_job_status_processing(self):
        """Test getting status of a processing job."""
        job = Job(
            job_id="test-job-123",
            text="Python is great",
            status=JobStatus.PROCESSING,
            created_at=datetime.utcnow(),
        )

        with patch("main.job_service.get_job", AsyncMock(return_value=job)):
            response = client.get("/jobs/test-job-123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"
            assert data["progress"] == 50

    def test_get_job_status_completed(self):
        """Test getting status of a completed job."""
        result = {
            "nodes": [{"id": "python", "label": "Python", "type": "Tech", "confidence": 0.95}],
            "edges": [{"source": "python", "target": "ai", "relation": "used_for"}],
        }

        job = Job(
            job_id="test-job-123",
            text="Python is great",
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            result=result,
        )

        with patch("main.job_service.get_job", AsyncMock(return_value=job)):
            response = client.get("/jobs/test-job-123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["progress"] == 100
            assert data["result"] is not None
            assert len(data["result"]["nodes"]) == 1
            assert len(data["result"]["edges"]) == 1

    def test_get_job_status_failed(self):
        """Test getting status of a failed job."""
        job = Job(
            job_id="test-job-123",
            text="Python is great",
            status=JobStatus.FAILED,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error="API error: Rate limit exceeded",
        )

        with patch("main.job_service.get_job", AsyncMock(return_value=job)):
            response = client.get("/jobs/test-job-123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert data["progress"] == 100
            assert data["error"] == "API error: Rate limit exceeded"

    def test_get_job_status_not_found(self):
        """Test getting status of non-existent job."""
        with patch("main.job_service.get_job", AsyncMock(return_value=None)):
            response = client.get("/jobs/nonexistent-job")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()


class TestStatsEndpoint:
    """Test suite for system statistics endpoint."""

    def test_stats_endpoint(self):
        """Test getting system statistics."""
        # Mock all service calls
        mock_cache_stats = {
            "total_cached_results": 42,
            "cache_ttl_seconds": 86400,
            "cache_ttl_hours": 24.0,
        }

        with patch("main.cache_service.get_stats", AsyncMock(return_value=mock_cache_stats)), patch(
            "main.job_service.get_queue_length", AsyncMock(return_value=5)
        ), patch("main.redis_service.ping", AsyncMock(return_value=True)), patch(
            "main.redis_service.redis", True
        ):
            response = client.get("/stats")

            assert response.status_code == 200
            data = response.json()

            # Check Redis stats
            assert data["redis"]["healthy"] is True
            assert data["redis"]["connected"] is True

            # Check cache stats
            assert data["cache"]["total_cached_results"] == 42
            assert data["cache"]["cache_ttl_hours"] == 24.0

            # Check queue stats
            assert data["queue"]["pending_jobs"] == 5

            # Check extractor info
            assert "extractor" in data
            assert "type" in data["extractor"]


class TestRateLimitEndpoint:
    """Test suite for rate limit status endpoint."""

    def test_rate_limit_status(self):
        """Test getting rate limit status."""
        mock_status = {
            "ip_requests": 5,
            "ip_limit": 10,
            "ip_remaining": 5,
            "ip_resets_in": 45,
            "global_requests": 12,
            "global_limit": 15,
            "global_remaining": 3,
            "global_resets_in": 30,
        }

        with patch("main.get_rate_limit_status", AsyncMock(return_value=mock_status)):
            response = client.get("/rate-limit-status")

            assert response.status_code == 200
            data = response.json()

            assert data["ip_requests"] == 5
            assert data["ip_remaining"] == 5
            assert data["global_requests"] == 12
            assert data["global_remaining"] == 3


class TestExtractWithCache:
    """Test extract endpoint with caching."""

    def test_extract_cache_hit(self):
        """Test extraction with cache hit (no LLM call)."""
        cached_result = ExtractResponse(
            nodes=[Node(id="python", label="Python", type="Tech", confidence=0.95)],
            edges=[Edge(source="python", target="ai", relation="used_for")],
        )

        # Mock cache hit
        with patch(
            "main.cache_service.get_or_compute", AsyncMock(return_value=cached_result)
        ), patch("main.rate_limit", AsyncMock(return_value=True)):
            response = client.post("/extract", json={"text": "Python is used for AI"})

            assert response.status_code == 200
            data = response.json()
            assert len(data["nodes"]) == 1
            assert data["nodes"][0]["label"] == "Python"

    def test_extract_cache_miss(self):
        """Test extraction with cache miss (LLM call)."""
        fresh_result = ExtractResponse(
            nodes=[Node(id="python", label="Python", type="Tech", confidence=0.95)],
            edges=[Edge(source="python", target="ai", relation="used_for")],
        )

        # Mock cache miss + computation
        with patch(
            "main.cache_service.get_or_compute", AsyncMock(return_value=fresh_result)
        ), patch("main.rate_limit", AsyncMock(return_value=True)):
            response = client.post("/extract", json={"text": "Python is amazing for AI"})

            assert response.status_code == 200
            data = response.json()
            assert len(data["nodes"]) == 1

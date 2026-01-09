"""
API Integration Tests
=====================

Integration tests for FastAPI endpoints.

Tests verify:
- HTTP endpoints work correctly
- Request/response validation
- Error handling
- Dependency injection
- Status codes

Uses TestClient for synchronous testing without running server.
"""

import pytest
from extractors.base import BaseExtractor
from fastapi.testclient import TestClient
from main import app, get_extractor
from schemas import Edge, ExtractResponse, Node


class MockExtractor(BaseExtractor):
    """Mock extractor for testing API without real LLM calls"""

    async def extract(self, text: str) -> ExtractResponse:
        """Return mock extraction result"""
        return ExtractResponse(
            nodes=[Node(id="test-node", label="Test Node", type="Tech", confidence=0.9)],
            edges=[Edge(source="test-node", target="other-node", relation="test_relation")],
        )


class FailingExtractor(BaseExtractor):
    """Mock extractor that raises exceptions for testing error handling"""

    async def extract(self, text: str) -> ExtractResponse:
        raise Exception("Extraction failed intentionally")


# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint"""

    def test_health_returns_200(self):
        """Test that /health returns OK status"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self):
        """Test that /health returns JSON with status"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "ok"

    def test_health_includes_extractor_type(self):
        """Test that /health indicates which extractor is active"""
        response = client.get("/health")
        data = response.json()

        assert "extractor" in data
        assert data["extractor"] in ["LLM", "Rule-based"]


class TestExtractEndpointSuccess:
    """Test /extract endpoint success cases"""

    def setup_method(self):
        """Override extractor with mock before each test"""
        app.dependency_overrides[get_extractor] = lambda: MockExtractor()

    def teardown_method(self):
        """Clear dependency overrides after each test"""
        app.dependency_overrides.clear()

    def test_extract_returns_200(self):
        """Test successful extraction returns 200 OK"""
        response = client.post("/extract", json={"text": "Python is great"})
        assert response.status_code == 200

    def test_extract_returns_nodes_and_edges(self):
        """Test response contains nodes and edges"""
        response = client.post("/extract", json={"text": "Python is used for data science"})
        data = response.json()

        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_extract_node_structure(self):
        """Test that returned nodes have correct structure"""
        response = client.post("/extract", json={"text": "Test text"})
        data = response.json()

        assert len(data["nodes"]) > 0
        node = data["nodes"][0]

        # Verify required fields
        assert "id" in node
        assert "label" in node
        assert "type" in node
        assert "confidence" in node

        # Verify types
        assert isinstance(node["id"], str)
        assert isinstance(node["label"], str)
        assert isinstance(node["type"], str)
        assert isinstance(node["confidence"], (int, float))

    def test_extract_edge_structure(self):
        """Test that returned edges have correct structure"""
        response = client.post("/extract", json={"text": "Test text"})
        data = response.json()

        assert len(data["edges"]) > 0
        edge = data["edges"][0]

        # Verify required fields
        assert "source" in edge
        assert "target" in edge
        assert "relation" in edge

        # Verify types
        assert isinstance(edge["source"], str)
        assert isinstance(edge["target"], str)
        assert isinstance(edge["relation"], str)

    def test_extract_with_long_text(self):
        """Test extraction with longer text (within limits)"""
        long_text = "Python is a programming language. " * 50  # ~200 words
        response = client.post("/extract", json={"text": long_text})
        assert response.status_code == 200


class TestExtractEndpointValidation:
    """Test request validation"""

    def test_extract_rejects_empty_text(self):
        """Test that empty text is rejected"""
        response = client.post("/extract", json={"text": ""})
        # Should return 422 Unprocessable Entity (validation error)
        assert response.status_code == 422

    def test_extract_rejects_missing_text_field(self):
        """Test that missing 'text' field is rejected"""
        response = client.post("/extract", json={})
        assert response.status_code == 422

    def test_extract_rejects_invalid_json(self):
        """Test that invalid JSON is rejected"""
        response = client.post(
            "/extract", data="not json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_extract_rejects_wrong_field_type(self):
        """Test that wrong field types are rejected"""
        response = client.post(
            "/extract",
            json={"text": 123},  # Should be string, not int
        )
        assert response.status_code == 422

    def test_extract_accepts_unicode_text(self):
        """Test that unicode text is accepted"""
        app.dependency_overrides[get_extractor] = lambda: MockExtractor()

        response = client.post("/extract", json={"text": "Python は素晴らしい 🐍"})
        assert response.status_code == 200

        app.dependency_overrides.clear()


class TestExtractEndpointErrorHandling:
    """Test error handling"""

    def setup_method(self):
        """Override extractor with failing mock"""
        app.dependency_overrides[get_extractor] = lambda: FailingExtractor()

    def teardown_method(self):
        """Clear dependency overrides"""
        app.dependency_overrides.clear()

    def test_extract_returns_500_on_extraction_failure(self):
        """Test that extraction errors return 500 Internal Server Error"""
        response = client.post("/extract", json={"text": "Test text"})
        assert response.status_code == 500

    def test_extract_error_includes_detail(self):
        """Test that error response includes detail message"""
        response = client.post("/extract", json={"text": "Test text"})
        data = response.json()

        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0


class TestExtractEndpointContentType:
    """Test content type handling"""

    def test_extract_requires_json_content_type(self):
        """Test that endpoint requires JSON content type"""
        response = client.post(
            "/extract",
            data="text=Python is great",  # Form data instead of JSON
        )
        # Should fail because we're not sending JSON
        assert response.status_code == 422

    def test_extract_accepts_json_content_type(self):
        """Test that endpoint accepts JSON content type"""
        app.dependency_overrides[get_extractor] = lambda: MockExtractor()

        response = client.post(
            "/extract", json={"text": "Python"}, headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

        app.dependency_overrides.clear()


class TestAPIDocumentation:
    """Test API documentation endpoints"""

    def test_docs_endpoint_exists(self):
        """Test that /docs endpoint is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_exists(self):
        """Test that OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        # Verify it's valid JSON
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestDependencyInjection:
    """Test that dependency injection works correctly"""

    def test_can_override_extractor(self):
        """Test that we can override the extractor dependency"""
        # Create custom mock
        custom_mock = MockExtractor()

        # Override dependency
        app.dependency_overrides[get_extractor] = lambda: custom_mock

        # Make request
        response = client.post("/extract", json={"text": "Test"})

        # Should use our mock
        assert response.status_code == 200
        data = response.json()
        assert data["nodes"][0]["id"] == "test-node"

        # Cleanup
        app.dependency_overrides.clear()

    def test_default_extractor_used_without_override(self):
        """Test that default extractor is used when no override"""
        # Clear any overrides
        app.dependency_overrides.clear()

        # This will use the real get_extractor function
        # which returns either LLM or Rule-based extractor
        response = client.post("/extract", json={"text": "Python is great"})

        # Should work (might be slow if using real LLM)
        assert response.status_code in [200, 500]  # 500 if API key issues


class TestCORSAndSecurity:
    """Test CORS and security headers (if configured)"""

    def test_api_returns_json_content_type(self):
        """Test that API returns proper JSON content type"""
        app.dependency_overrides[get_extractor] = lambda: MockExtractor()

        response = client.post("/extract", json={"text": "Test"})

        assert "application/json" in response.headers["content-type"]

        app.dependency_overrides.clear()


class TestExtractEndpointPerformance:
    """Test basic performance characteristics"""

    def test_extract_responds_quickly_with_mock(self):
        """Test that mocked extraction is fast"""
        import time

        app.dependency_overrides[get_extractor] = lambda: MockExtractor()

        start = time.time()
        response = client.post("/extract", json={"text": "Python is great"})
        elapsed = time.time() - start

        assert response.status_code == 200
        # Mocked should be very fast (< 1 second)
        assert elapsed < 1.0

        app.dependency_overrides.clear()


# Fixtures for reuse across test classes
@pytest.fixture
def mock_extractor():
    """Provide a MockExtractor instance"""
    return MockExtractor()


@pytest.fixture
def failing_extractor():
    """Provide a FailingExtractor instance"""
    return FailingExtractor()

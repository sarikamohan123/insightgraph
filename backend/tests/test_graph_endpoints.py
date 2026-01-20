"""
Tests for Graph API Endpoints
==============================

Tests REST API endpoints for knowledge graph CRUD operations.
Uses mocks to avoid database and external service dependencies.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from middleware.api_key_auth import require_api_key
from routers.graphs import get_embedding_svc, get_extractor, get_graph_repository
from schemas import Edge as EdgeSchema
from schemas import ExtractResponse
from schemas import Node as NodeSchema


# Mock extractor that returns predictable results
class MockExtractor:
    """Mock extractor for testing."""

    async def extract(self, text: str) -> ExtractResponse:
        return ExtractResponse(
            nodes=[
                NodeSchema(id="node-1", label="Test Node", type="Tech", confidence=0.9),
            ],
            edges=[
                EdgeSchema(source="node-1", target="node-2", relation="related_to"),
            ],
        )


# Mock embedding service
class MockEmbeddingService:
    """Mock embedding service for testing."""

    async def generate_embedding(self, text: str) -> list[float]:
        """Return a mock 768-dimensional embedding."""
        return [0.1] * 768

    async def generate_query_embedding(self, query: str) -> list[float]:
        """Return a mock query embedding."""
        return [0.1] * 768


# Mock API key dependency - always allows access
async def mock_require_api_key():
    """Mock API key check that always passes."""
    pass


# Store for mock graphs (in-memory database)
mock_graphs_store: dict = {}


# Mock repository
class MockGraphRepository:
    """Mock repository for testing without database."""

    async def create_graph(self, source_text: str, extract_result, title=None, description=None, embedding=None):
        """Create a mock graph."""
        graph_id = uuid.uuid4()
        graph = MagicMock()
        graph.id = graph_id
        graph.title = title
        graph.description = description
        graph.source_text = source_text
        graph.created_at = datetime.utcnow()
        graph.updated_at = datetime.utcnow()

        # Create mock nodes
        graph.nodes = [
            MagicMock(
                id=uuid.uuid4(),
                node_id=n.id,
                label=n.label,
                type=n.type,
                confidence=n.confidence,
            )
            for n in extract_result.nodes
        ]

        # Create mock edges with UUID node references
        graph.edges = [
            MagicMock(
                id=uuid.uuid4(),
                source_node_id=graph.nodes[0].id if graph.nodes else uuid.uuid4(),
                target_node_id=uuid.uuid4(),  # Target doesn't exist but needs to be UUID
                relation=e.relation,
            )
            for e in extract_result.edges
        ]

        mock_graphs_store[graph_id] = graph
        return graph

    async def get_graph(self, graph_id: uuid.UUID):
        """Get a mock graph by ID."""
        return mock_graphs_store.get(graph_id)

    async def list_graphs(self, limit: int = 50, offset: int = 0):
        """List mock graphs with pagination."""
        graphs = list(mock_graphs_store.values())
        return graphs[offset : offset + limit]

    async def get_graph_count(self):
        """Get total count of mock graphs."""
        return len(mock_graphs_store)

    async def delete_graph(self, graph_id: uuid.UUID):
        """Delete a mock graph."""
        if graph_id in mock_graphs_store:
            del mock_graphs_store[graph_id]
            return True
        return False

    async def search_graphs(self, query: str, limit: int = 20):
        """Search mock graphs by text."""
        results = []
        for graph in mock_graphs_store.values():
            if query.lower() in graph.source_text.lower():
                results.append(graph)
        return results[:limit]

    async def semantic_search(self, query_embedding: list[float], limit: int = 20, similarity_threshold: float = 0.5):
        """Mock semantic search - returns all graphs with mock similarity scores."""
        results = []
        for graph in list(mock_graphs_store.values())[:limit]:
            results.append((graph, 0.8))  # Mock similarity score
        return results


@pytest.fixture(autouse=True)
def setup_test_dependencies():
    """Set up dependency overrides for all tests."""
    # Clear mock store before each test
    mock_graphs_store.clear()

    # Override dependencies
    app.dependency_overrides[get_extractor] = lambda: MockExtractor()
    app.dependency_overrides[get_graph_repository] = lambda: MockGraphRepository()
    app.dependency_overrides[get_embedding_svc] = lambda: MockEmbeddingService()
    app.dependency_overrides[require_api_key] = mock_require_api_key

    yield

    # Clean up after test
    app.dependency_overrides.clear()
    mock_graphs_store.clear()


def get_test_client():
    """Create AsyncClient with ASGITransport for testing."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_create_graph_endpoint():
    """Test POST /graphs endpoint."""
    async with get_test_client() as client:
        response = await client.post(
            "/graphs",
            json={
                "text": "Python is used for machine learning",
                "title": "ML Graph",
                "description": "A graph about ML",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "ML Graph"
        assert data["description"] == "A graph about ML"
        assert "id" in data
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0


@pytest.mark.asyncio
async def test_list_graphs_endpoint():
    """Test GET /graphs endpoint."""
    async with get_test_client() as client:
        # Create a graph first
        await client.post(
            "/graphs",
            json={"text": "Test graph for listing"},
        )

        # List graphs
        response = await client.get("/graphs")

        assert response.status_code == 200
        data = response.json()
        assert "graphs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["graphs"], list)


@pytest.mark.asyncio
async def test_get_graph_endpoint():
    """Test GET /graphs/{id} endpoint."""
    async with get_test_client() as client:
        # Create a graph
        create_response = await client.post(
            "/graphs",
            json={"text": "Test graph"},
        )
        graph_id = create_response.json()["id"]

        # Get the graph
        response = await client.get(f"/graphs/{graph_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == graph_id
        assert "nodes" in data
        assert "edges" in data


@pytest.mark.asyncio
async def test_get_graph_not_found():
    """Test GET /graphs/{id} with non-existent ID."""
    async with get_test_client() as client:
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/graphs/{fake_id}")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_graph_endpoint():
    """Test DELETE /graphs/{id} endpoint."""
    async with get_test_client() as client:
        # Create a graph
        create_response = await client.post(
            "/graphs",
            json={"text": "Test graph to delete"},
        )
        graph_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(f"/graphs/{graph_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(f"/graphs/{graph_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_search_graphs_endpoint():
    """Test GET /graphs/search endpoint."""
    async with get_test_client() as client:
        # Create graphs with different content
        await client.post("/graphs", json={"text": "Python programming language"})
        await client.post("/graphs", json={"text": "JavaScript web development"})

        # Search for "Python"
        response = await client.get("/graphs/search/?q=Python")

        assert response.status_code == 200
        data = response.json()
        assert "graphs" in data
        assert len(data["graphs"]) >= 1


@pytest.mark.asyncio
async def test_create_graph_with_minimal_data():
    """Test creating a graph with only text (no title/description)."""
    async with get_test_client() as client:
        response = await client.post(
            "/graphs",
            json={"text": "Minimal graph"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["source_text"] == "Minimal graph"
        assert data["title"] is None
        assert data["description"] is None


@pytest.mark.asyncio
async def test_list_graphs_pagination():
    """Test pagination in list graphs endpoint."""
    async with get_test_client() as client:
        # Create multiple graphs
        for i in range(5):
            await client.post("/graphs", json={"text": f"Graph {i}"})

        # Get first page
        response1 = await client.get("/graphs?limit=2&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["graphs"]) == 2

        # Get second page
        response2 = await client.get("/graphs?limit=2&offset=2")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["graphs"]) == 2

        # Ensure pages are different
        assert data1["graphs"][0]["id"] != data2["graphs"][0]["id"]

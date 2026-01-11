"""
Tests for Graph API Endpoints
==============================

Tests REST API endpoints for knowledge graph CRUD operations.
"""

import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_create_graph_endpoint():
    """Test POST /graphs endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
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
    async with AsyncClient(app=app, base_url="http://test") as client:
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
    async with AsyncClient(app=app, base_url="http://test") as client:
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
    async with AsyncClient(app=app, base_url="http://test") as client:
        import uuid

        fake_id = str(uuid.uuid4())
        response = await client.get(f"/graphs/{fake_id}")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_graph_endpoint():
    """Test DELETE /graphs/{id} endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
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
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create graphs with different content
        await client.post("/graphs", json={"text": "Python programming language"})
        await client.post("/graphs", json={"text": "JavaScript web development"})

        # Search for "Python"
        response = await client.get("/graphs/search/?q=Python")

        assert response.status_code == 200
        data = response.json()
        assert "graphs" in data
        assert len(data["graphs"]) >= 1
        assert any("Python" in g["source_text"] for g in data["graphs"])


@pytest.mark.asyncio
async def test_create_graph_with_minimal_data():
    """Test creating a graph with only text (no title/description)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
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
    async with AsyncClient(app=app, base_url="http://test") as client:
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

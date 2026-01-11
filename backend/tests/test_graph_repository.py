"""
Tests for Graph Repository
===========================

Tests CRUD operations for knowledge graphs in PostgreSQL.
"""

import pytest
from models.database import Base, Edge, Graph, Node
from repositories.graph_repository import GraphRepository
from schemas import Edge as EdgeSchema
from schemas import ExtractResponse
from schemas import Node as NodeSchema
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


# Test database URL (use a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://dev:devpass@localhost:5432/insightgraph_test"


@pytest.fixture
async def engine():
    """Create test database engine."""
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def session(engine):
    """Create test database session."""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as sess:
        yield sess


@pytest.fixture
def sample_extract_result():
    """Sample extraction result for testing."""
    return ExtractResponse(
        nodes=[
            NodeSchema(id="python", label="Python", type="Tech", confidence=0.95),
            NodeSchema(id="fastapi", label="FastAPI", type="Tech", confidence=0.9),
        ],
        edges=[
            EdgeSchema(source="python", target="fastapi", relation="used_by"),
        ],
    )


class TestGraphRepository:
    """Test suite for GraphRepository."""

    @pytest.mark.asyncio
    async def test_create_graph(self, session, sample_extract_result):
        """Test creating a graph with nodes and edges."""
        repo = GraphRepository(session)

        graph = await repo.create_graph(
            source_text="Python is used by FastAPI",
            extract_result=sample_extract_result,
            title="Test Graph",
            description="A test graph",
        )

        assert graph.id is not None
        assert graph.title == "Test Graph"
        assert graph.description == "A test graph"
        assert graph.source_text == "Python is used by FastAPI"
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.created_at is not None

    @pytest.mark.asyncio
    async def test_get_graph(self, session, sample_extract_result):
        """Test retrieving a graph by ID."""
        repo = GraphRepository(session)

        # Create a graph
        created_graph = await repo.create_graph(
            source_text="Test text",
            extract_result=sample_extract_result,
        )

        # Retrieve it
        retrieved_graph = await repo.get_graph(created_graph.id)

        assert retrieved_graph is not None
        assert retrieved_graph.id == created_graph.id
        assert len(retrieved_graph.nodes) == 2
        assert len(retrieved_graph.edges) == 1

    @pytest.mark.asyncio
    async def test_get_graph_not_found(self, session):
        """Test getting a non-existent graph."""
        repo = GraphRepository(session)

        import uuid

        fake_id = uuid.uuid4()
        graph = await repo.get_graph(fake_id)

        assert graph is None

    @pytest.mark.asyncio
    async def test_list_graphs(self, session, sample_extract_result):
        """Test listing graphs with pagination."""
        repo = GraphRepository(session)

        # Create 3 graphs
        for i in range(3):
            await repo.create_graph(
                source_text=f"Test text {i}",
                extract_result=sample_extract_result,
                title=f"Graph {i}",
            )

        # List all
        graphs = await repo.list_graphs(limit=10, offset=0)
        assert len(graphs) == 3

        # Test pagination
        graphs_page1 = await repo.list_graphs(limit=2, offset=0)
        assert len(graphs_page1) == 2

        graphs_page2 = await repo.list_graphs(limit=2, offset=2)
        assert len(graphs_page2) == 1

    @pytest.mark.asyncio
    async def test_delete_graph(self, session, sample_extract_result):
        """Test deleting a graph."""
        repo = GraphRepository(session)

        # Create a graph
        graph = await repo.create_graph(
            source_text="Test text",
            extract_result=sample_extract_result,
        )

        # Delete it
        deleted = await repo.delete_graph(graph.id)
        assert deleted is True

        # Verify it's gone
        retrieved = await repo.get_graph(graph.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_graph_not_found(self, session):
        """Test deleting a non-existent graph."""
        repo = GraphRepository(session)

        import uuid

        fake_id = uuid.uuid4()
        deleted = await repo.delete_graph(fake_id)

        assert deleted is False

    @pytest.mark.asyncio
    async def test_search_graphs(self, session, sample_extract_result):
        """Test searching graphs by text."""
        repo = GraphRepository(session)

        # Create graphs with different text
        await repo.create_graph(
            source_text="Python is great for data science",
            extract_result=sample_extract_result,
        )
        await repo.create_graph(
            source_text="JavaScript is used for web development",
            extract_result=sample_extract_result,
        )

        # Search for "Python"
        results = await repo.search_graphs(query="Python", limit=10)
        assert len(results) == 1
        assert "Python" in results[0].source_text

        # Search for "web"
        results = await repo.search_graphs(query="web", limit=10)
        assert len(results) == 1
        assert "JavaScript" in results[0].source_text

    @pytest.mark.asyncio
    async def test_get_graph_count(self, session, sample_extract_result):
        """Test getting total graph count."""
        repo = GraphRepository(session)

        # Initially 0
        count = await repo.get_graph_count()
        assert count == 0

        # Create 3 graphs
        for i in range(3):
            await repo.create_graph(
                source_text=f"Test {i}",
                extract_result=sample_extract_result,
            )

        # Count should be 3
        count = await repo.get_graph_count()
        assert count == 3

    @pytest.mark.asyncio
    async def test_graph_cascade_delete(self, session, sample_extract_result):
        """Test that deleting a graph also deletes its nodes and edges."""
        repo = GraphRepository(session)

        # Create a graph
        graph = await repo.create_graph(
            source_text="Test",
            extract_result=sample_extract_result,
        )

        graph_id = graph.id

        # Verify nodes and edges exist
        from sqlalchemy import select

        nodes_result = await session.execute(select(Node).where(Node.graph_id == graph_id))
        nodes = nodes_result.scalars().all()
        assert len(nodes) == 2

        edges_result = await session.execute(select(Edge).where(Edge.graph_id == graph_id))
        edges = edges_result.scalars().all()
        assert len(edges) == 1

        # Delete graph
        await repo.delete_graph(graph_id)

        # Verify nodes and edges are also deleted
        nodes_result = await session.execute(select(Node).where(Node.graph_id == graph_id))
        nodes = nodes_result.scalars().all()
        assert len(nodes) == 0

        edges_result = await session.execute(select(Edge).where(Edge.graph_id == graph_id))
        edges = edges_result.scalars().all()
        assert len(edges) == 0

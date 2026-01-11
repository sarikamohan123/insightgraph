"""
Graph Repository - Data Access Layer
======================================

Implements the repository pattern for clean separation of business logic
from database operations.

Key Methods:
- create_graph: Save a complete knowledge graph to database
- get_graph: Retrieve graph by ID
- list_graphs: Get all graphs with pagination
- delete_graph: Remove a graph and its nodes/edges
- search_graphs: Find graphs by text content

Why use Repository Pattern?
- Abstracts database details from business logic
- Makes testing easier (can mock repository)
- Can swap database implementations
- Single place to optimize queries
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from models.database import Edge, Graph, Node
from schemas import ExtractResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession


class GraphRepository:
    """
    Data access layer for knowledge graph operations.

    Handles all database CRUD operations for graphs, nodes, and edges.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create_graph(
        self,
        source_text: str,
        extract_result: ExtractResponse,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Graph:
        """
        Save an extracted knowledge graph to database.

        Args:
            source_text: Original input text
            extract_result: Extracted nodes and edges
            title: Optional graph title
            description: Optional graph description

        Returns:
            Saved Graph object with ID and timestamps
        """
        # Create graph record
        graph = Graph(
            title=title,
            description=description,
            source_text=source_text,
            graph_metadata={"node_count": len(extract_result.nodes), "edge_count": len(extract_result.edges)},
        )
        self.session.add(graph)
        await self.session.flush()  # Get graph ID without committing

        # Create nodes with mapping from node_id to database ID
        node_id_map = {}  # Maps node.id (e.g., "python") to UUID
        for node_data in extract_result.nodes:
            node = Node(
                graph_id=graph.id,
                node_id=node_data.id,
                label=node_data.label,
                type=node_data.type,
                confidence=node_data.confidence,
                properties={},
            )
            self.session.add(node)
            await self.session.flush()  # Get node UUID
            node_id_map[node_data.id] = node.id

        # Create edges
        for edge_data in extract_result.edges:
            # Find source and target node UUIDs
            source_uuid = node_id_map.get(edge_data.source)
            target_uuid = node_id_map.get(edge_data.target)

            if source_uuid and target_uuid:
                edge = Edge(
                    graph_id=graph.id,
                    source_node_id=source_uuid,
                    target_node_id=target_uuid,
                    relation=edge_data.relation,
                    properties={},
                )
                self.session.add(edge)

        await self.session.commit()
        await self.session.refresh(graph)

        return graph

    async def get_graph(self, graph_id: UUID) -> Optional[Graph]:
        """
        Retrieve a graph by ID with all its nodes and edges.

        Args:
            graph_id: UUID of the graph

        Returns:
            Graph object if found, None otherwise
        """
        result = await self.session.execute(select(Graph).where(Graph.id == graph_id))
        graph = result.scalar_one_or_none()

        if graph:
            # Eagerly load relationships
            await self.session.refresh(graph, ["nodes", "edges"])

        return graph

    async def list_graphs(self, limit: int = 50, offset: int = 0) -> List[Graph]:
        """
        Get all graphs with pagination.

        Args:
            limit: Max number of graphs to return
            offset: Number of graphs to skip

        Returns:
            List of Graph objects (newest first)
        """
        result = await self.session.execute(
            select(Graph).order_by(desc(Graph.created_at)).limit(limit).offset(offset)
        )
        graphs = result.scalars().all()

        # Eagerly load relationships for each graph
        for graph in graphs:
            await self.session.refresh(graph, ["nodes", "edges"])

        return list(graphs)

    async def delete_graph(self, graph_id: UUID) -> bool:
        """
        Delete a graph and all its nodes and edges.

        Cascade delete is handled by database constraints.

        Args:
            graph_id: UUID of the graph to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(select(Graph).where(Graph.id == graph_id))
        graph = result.scalar_one_or_none()

        if not graph:
            return False

        await self.session.delete(graph)
        await self.session.commit()
        return True

    async def search_graphs(self, query: str, limit: int = 20) -> List[Graph]:
        """
        Search graphs by text content (simple substring search).

        Args:
            query: Search term
            limit: Max results

        Returns:
            List of matching graphs
        """
        # Simple case-insensitive substring search
        # For production, consider full-text search or pgvector
        result = await self.session.execute(
            select(Graph)
            .where(Graph.source_text.ilike(f"%{query}%"))
            .order_by(desc(Graph.created_at))
            .limit(limit)
        )
        graphs = result.scalars().all()

        for graph in graphs:
            await self.session.refresh(graph, ["nodes", "edges"])

        return list(graphs)

    async def get_graph_count(self) -> int:
        """
        Get total number of graphs in database.

        Returns:
            Count of graphs
        """
        result = await self.session.execute(select(Graph))
        return len(result.scalars().all())

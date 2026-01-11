"""
Graph CRUD API Endpoints
=========================

RESTful API for managing knowledge graphs.

Endpoints:
- POST   /graphs         - Create a new graph from text
- GET    /graphs         - List all graphs (paginated)
- GET    /graphs/{id}    - Get a specific graph
- DELETE /graphs/{id}    - Delete a graph
- GET    /graphs/search  - Search graphs by text
"""

from typing import Annotated
from uuid import UUID

from extractors.base import BaseExtractor
from extractors.llm_based import LLMExtractor
from extractors.rule_based import RuleBasedExtractor
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.graph_schemas import (
    GraphCreateRequest,
    GraphListResponse,
    GraphResponse,
)
from repositories.graph_repository import GraphRepository
from services.db_service import get_db_session
from services.llm_service import GeminiService
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings

# Create router
router = APIRouter(prefix="/graphs", tags=["Graphs"])


# Dependency to get database session
async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async with get_db_session() as session:
        yield session


# Dependency to get repository
def get_graph_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> GraphRepository:
    """Get graph repository with injected session."""
    return GraphRepository(session)


# Dependency to get extractor (same as main.py)
def get_extractor() -> BaseExtractor:
    """Get extractor based on settings."""
    if settings.use_llm_extractor:
        llm_service = GeminiService()
        return LLMExtractor(llm_service)
    else:
        return RuleBasedExtractor()


@router.post(
    "",
    response_model=GraphResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge graph",
    responses={
        201: {"description": "Graph created successfully"},
        500: {"description": "Extraction or database error"},
    },
)
async def create_graph(
    req: GraphCreateRequest,
    extractor: Annotated[BaseExtractor, Depends(get_extractor)],
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
):
    """
    Extract entities and relationships from text and save to database.

    This endpoint:
    1. Extracts knowledge graph from text using LLM or rule-based extractor
    2. Saves the graph, nodes, and edges to PostgreSQL
    3. Returns the saved graph with database IDs

    Args:
        req: Request with text and optional title/description
        extractor: Injected extractor (LLM or rule-based)
        repo: Injected graph repository

    Returns:
        Saved graph with all nodes and edges
    """
    try:
        # Extract entities and relationships
        extract_result = await extractor.extract(req.text)

        # Save to database
        graph = await repo.create_graph(
            source_text=req.text,
            extract_result=extract_result,
            title=req.title,
            description=req.description,
        )

        return graph

    except Exception as e:
        print(f"[ERROR] Graph creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph creation failed: {str(e)[:200]}",
        ) from e


@router.get(
    "",
    response_model=GraphListResponse,
    summary="List all knowledge graphs",
    responses={
        200: {"description": "List of graphs retrieved successfully"},
    },
)
async def list_graphs(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    limit: int = Query(50, ge=1, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """
    Get all knowledge graphs with pagination.

    Returns graphs ordered by creation date (newest first).

    Args:
        repo: Injected graph repository
        limit: Max results (1-100)
        offset: Skip N results

    Returns:
        List of graphs with pagination info
    """
    try:
        graphs = await repo.list_graphs(limit=limit, offset=offset)
        total = await repo.get_graph_count()

        return GraphListResponse(
            graphs=graphs,
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        print(f"[ERROR] Failed to list graphs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list graphs: {str(e)[:200]}",
        ) from e


@router.get(
    "/{graph_id}",
    response_model=GraphResponse,
    summary="Get a specific knowledge graph",
    responses={
        200: {"description": "Graph found"},
        404: {"description": "Graph not found"},
    },
)
async def get_graph(
    graph_id: UUID,
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
):
    """
    Retrieve a knowledge graph by its ID.

    Returns the complete graph with all nodes and edges.

    Args:
        graph_id: UUID of the graph
        repo: Injected graph repository

    Returns:
        Complete graph with nodes and edges
    """
    try:
        graph = await repo.get_graph(graph_id)

        if not graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Graph {graph_id} not found",
            )

        return graph

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get graph: {str(e)[:200]}",
        ) from e


@router.delete(
    "/{graph_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a knowledge graph",
    responses={
        204: {"description": "Graph deleted successfully"},
        404: {"description": "Graph not found"},
    },
)
async def delete_graph(
    graph_id: UUID,
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
):
    """
    Delete a knowledge graph and all its nodes and edges.

    Args:
        graph_id: UUID of the graph to delete
        repo: Injected graph repository

    Returns:
        No content (204) on success
    """
    try:
        deleted = await repo.delete_graph(graph_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Graph {graph_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to delete graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete graph: {str(e)[:200]}",
        ) from e


@router.get(
    "/search/",
    response_model=GraphListResponse,
    summary="Search knowledge graphs",
    responses={
        200: {"description": "Search results retrieved"},
    },
)
async def search_graphs(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """
    Search knowledge graphs by text content.

    Performs case-insensitive substring search on source text.

    Args:
        repo: Injected graph repository
        q: Search query
        limit: Max results

    Returns:
        List of matching graphs
    """
    try:
        graphs = await repo.search_graphs(query=q, limit=limit)

        return GraphListResponse(
            graphs=graphs,
            total=len(graphs),
            limit=limit,
            offset=0,
        )

    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)[:200]}",
        ) from e

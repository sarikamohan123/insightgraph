"""
Graph CRUD API Endpoints
=========================

RESTful API for managing knowledge graphs.

Endpoints:
- POST   /graphs                - Create a new graph from text
- GET    /graphs                - List all graphs (paginated)
- GET    /graphs/{id}           - Get a specific graph
- DELETE /graphs/{id}           - Delete a graph
- GET    /graphs/search/        - Search graphs by text (keyword)
- GET    /graphs/search/semantic - Semantic search by meaning (Phase 5)
"""

from typing import Annotated
from uuid import UUID

from config import settings
from extractors.base import BaseExtractor
from extractors.llm_based import LLMExtractor
from extractors.rule_based import RuleBasedExtractor
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.database import User
from models.graph_schemas import (
    EdgeResponse,
    GraphCreateRequest,
    GraphListResponse,
    GraphResponse,
    GraphVisibilityUpdate,
    NodeResponse,
    SearchMode,
    SemanticSearchResponse,
    SemanticSearchResult,
)
from repositories.graph_repository import GraphRepository
from routers.auth import get_current_user, require_current_user
from services.db_service import get_db_session
from services.embedding_service import EmbeddingService, get_embedding_service
from services.llm_service import GeminiService
from sqlalchemy.ext.asyncio import AsyncSession

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


# Dependency to get embedding service
def get_embedding_svc() -> EmbeddingService:
    """Get embedding service for semantic search."""
    return get_embedding_service()


@router.post(
    "",
    response_model=GraphResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge graph",
    responses={
        201: {"description": "Graph created successfully"},
        401: {"description": "Authentication required - provide Bearer token"},
        500: {"description": "Extraction or database error"},
    },
)
async def create_graph(
    req: GraphCreateRequest,
    extractor: Annotated[BaseExtractor, Depends(get_extractor)],
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding_svc)],
    current_user: Annotated[User, Depends(require_current_user)],
):
    """
    Extract entities and relationships from text and save to database.

    This endpoint:
    1. Extracts knowledge graph from text using LLM or rule-based extractor
    2. Generates semantic embedding for the text (Phase 5)
    3. Saves the graph, nodes, edges, and embedding to PostgreSQL
    4. Returns the saved graph with database IDs

    Args:
        req: Request with text and optional title/description
        extractor: Injected extractor (LLM or rule-based)
        repo: Injected graph repository
        embedding_service: Injected embedding service

    Returns:
        Saved graph with all nodes and edges
    """
    try:
        # Extract entities and relationships
        extract_result = await extractor.extract(req.text)

        # Generate semantic embedding for search (Phase 5)
        embedding = None
        try:
            embedding = await embedding_service.generate_embedding(req.text)
        except Exception as e:
            # Log but don't fail if embedding generation fails
            print(f"[WARN] Embedding generation failed (graph will be saved without): {e}")

        # Save to database with embedding and owner
        graph = await repo.create_graph(
            source_text=req.text,
            extract_result=extract_result,
            title=req.title,
            description=req.description,
            embedding=embedding,
            user_id=current_user.id,
            is_public=req.is_public,
        )

        return GraphResponse(
            id=graph.id,
            title=graph.title,
            description=graph.description,
            source_text=graph.source_text,
            nodes=[
                NodeResponse(
                    id=node.id,
                    node_id=node.node_id,
                    label=node.label,
                    type=node.type,
                    confidence=node.confidence,
                )
                for node in graph.nodes
            ],
            edges=[
                EdgeResponse(
                    id=edge.id,
                    source_node_id=edge.source_node_id,
                    target_node_id=edge.target_node_id,
                    relation=edge.relation,
                )
                for edge in graph.edges
            ],
            is_public=graph.is_public,
            user_id=graph.user_id,
            created_at=graph.created_at,
            updated_at=graph.updated_at,
        )

    except Exception as e:
        print(f"[ERROR] Graph creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph creation failed: {str(e)[:200]}",
        ) from e


@router.get(
    "",
    response_model=GraphListResponse,
    summary="List knowledge graphs",
    responses={
        200: {"description": "List of graphs retrieved successfully"},
    },
)
async def list_graphs(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    current_user: Annotated[User | None, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """
    Get knowledge graphs with pagination.

    - Unauthenticated users: Only see public graphs
    - Authenticated users: See public graphs + their own private graphs

    Returns graphs ordered by creation date (newest first).

    Args:
        repo: Injected graph repository
        current_user: Optional authenticated user
        limit: Max results (1-100)
        offset: Skip N results

    Returns:
        List of graphs with pagination info
    """
    try:
        if current_user:
            # Authenticated: show public + own graphs
            graphs = await repo.list_graphs_for_user(
                user_id=current_user.id, limit=limit, offset=offset
            )
            total = await repo.get_graph_count_for_user(current_user.id)
        else:
            # Unauthenticated: show only public graphs
            graphs = await repo.list_public_graphs(limit=limit, offset=offset)
            total = await repo.get_public_graph_count()

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
        401: {"description": "Authentication required - provide Bearer token"},
        403: {"description": "Not authorized to delete this graph"},
        404: {"description": "Graph not found"},
    },
)
async def delete_graph(
    graph_id: UUID,
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    current_user: Annotated[User, Depends(require_current_user)],
):
    """
    Delete a knowledge graph and all its nodes and edges.

    Users can only delete their own graphs.

    Args:
        graph_id: UUID of the graph to delete
        repo: Injected graph repository
        current_user: Authenticated user

    Returns:
        No content (204) on success
    """
    try:
        # First check if graph exists and user owns it
        graph = await repo.get_graph(graph_id)

        if not graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Graph {graph_id} not found",
            )

        # Check ownership - only the owner can delete their graph
        # Legacy graphs (no owner) cannot be deleted by regular users
        if graph.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This is a legacy graph with no owner. Cannot be deleted.",
            )
        if graph.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this graph",
            )

        await repo.delete_graph(graph_id)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to delete graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete graph: {str(e)[:200]}",
        ) from e


@router.patch(
    "/{graph_id}/visibility",
    response_model=GraphResponse,
    summary="Toggle graph visibility",
    responses={
        200: {"description": "Graph visibility updated"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to modify this graph"},
        404: {"description": "Graph not found"},
    },
)
async def update_graph_visibility(
    graph_id: UUID,
    req: GraphVisibilityUpdate,
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    current_user: Annotated[User, Depends(require_current_user)],
):
    """
    Update the visibility of a graph (public/private).

    Only the graph owner can change visibility.

    Args:
        graph_id: UUID of the graph to update
        req: New visibility status
        repo: Injected graph repository
        current_user: Authenticated user

    Returns:
        Updated graph
    """
    try:
        # Check if graph exists
        graph = await repo.get_graph(graph_id)

        if not graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Graph {graph_id} not found",
            )

        # Check ownership
        if graph.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this graph",
            )

        # Update visibility
        updated_graph = await repo.update_graph_visibility(graph_id, req.is_public)

        return GraphResponse(
            id=updated_graph.id,
            title=updated_graph.title,
            description=updated_graph.description,
            source_text=updated_graph.source_text,
            nodes=[
                NodeResponse(
                    id=node.id,
                    node_id=node.node_id,
                    label=node.label,
                    type=node.type,
                    confidence=node.confidence,
                )
                for node in updated_graph.nodes
            ],
            edges=[
                EdgeResponse(
                    id=edge.id,
                    source_node_id=edge.source_node_id,
                    target_node_id=edge.target_node_id,
                    relation=edge.relation,
                )
                for edge in updated_graph.edges
            ],
            is_public=updated_graph.is_public,
            user_id=updated_graph.user_id,
            created_at=updated_graph.created_at,
            updated_at=updated_graph.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to update graph visibility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update visibility: {str(e)[:200]}",
        ) from e


@router.get(
    "/search/",
    response_model=GraphListResponse,
    summary="Search knowledge graphs (keyword or semantic)",
    responses={
        200: {"description": "Search results retrieved"},
    },
)
async def search_graphs(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding_svc)],
    q: str = Query(..., min_length=1, description="Search query"),
    mode: SearchMode = Query(SearchMode.KEYWORD, description="Search mode"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """
    Search knowledge graphs by text content or semantic similarity.

    Supports two modes:
    - keyword: Case-insensitive substring search (fast, exact matches)
    - semantic: AI-powered similarity search (finds related content)

    Args:
        repo: Injected graph repository
        embedding_service: Injected embedding service
        q: Search query
        mode: Search mode (keyword or semantic)
        limit: Max results

    Returns:
        List of matching graphs
    """
    try:
        if mode == SearchMode.SEMANTIC:
            # Semantic search using embeddings
            query_embedding = await embedding_service.generate_query_embedding(q)
            results = await repo.semantic_search(
                query_embedding=query_embedding,
                limit=limit,
                similarity_threshold=0.3,  # Lower threshold for unified search
            )
            graphs = [graph for graph, _ in results]
        else:
            # Keyword search (existing behavior)
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


@router.get(
    "/search/semantic",
    response_model=SemanticSearchResponse,
    summary="Semantic search for knowledge graphs",
    responses={
        200: {"description": "Semantic search results with similarity scores"},
    },
)
async def semantic_search_graphs(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding_svc)],
    q: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity"),
):
    """
    Search knowledge graphs using semantic similarity.

    This endpoint:
    1. Generates an embedding for your search query
    2. Finds graphs with similar embeddings using cosine similarity
    3. Returns results ordered by relevance with similarity scores

    Better than keyword search for:
    - Finding related concepts (e.g., "ML" matches "machine learning")
    - Handling synonyms and paraphrases
    - Understanding intent rather than exact matches

    Args:
        repo: Injected graph repository
        embedding_service: Injected embedding service
        q: Search query
        limit: Max results
        threshold: Minimum similarity score (0-1)

    Returns:
        List of matching graphs with similarity scores
    """
    try:
        # Generate embedding for query
        query_embedding = await embedding_service.generate_query_embedding(q)

        # Search by similarity
        results = await repo.semantic_search(
            query_embedding=query_embedding,
            limit=limit,
            similarity_threshold=threshold,
        )

        # Format response with similarity scores
        search_results = [
            SemanticSearchResult(
                graph=GraphResponse(
                    id=graph.id,
                    title=graph.title,
                    description=graph.description,
                    source_text=graph.source_text,
                    nodes=[
                        NodeResponse(
                            id=node.id,
                            node_id=node.node_id,
                            label=node.label,
                            type=node.type,
                            confidence=node.confidence,
                        )
                        for node in graph.nodes
                    ],
                    edges=[
                        EdgeResponse(
                            id=edge.id,
                            source_node_id=edge.source_node_id,
                            target_node_id=edge.target_node_id,
                            relation=edge.relation,
                        )
                        for edge in graph.edges
                    ],
                    created_at=graph.created_at,
                    updated_at=graph.updated_at,
                ),
                similarity_score=score,
            )
            for graph, score in results
        ]

        return SemanticSearchResponse(
            results=search_results,
            total=len(search_results),
            query=q,
            search_mode="semantic",
        )

    except Exception as e:
        print(f"[ERROR] Semantic search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)[:200]}",
        ) from e

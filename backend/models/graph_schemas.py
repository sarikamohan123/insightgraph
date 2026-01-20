"""
Graph API Response Schemas
============================

Pydantic models for API responses (different from database models).

Why separate schemas from database models?
- Database models (SQLAlchemy) focus on persistence
- API schemas (Pydantic) focus on validation and serialization
- Keeps concerns separated (Single Responsibility Principle)
- Can expose different fields to API vs database
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class SearchMode(str, Enum):
    """Search mode options for graph search."""

    KEYWORD = "keyword"
    SEMANTIC = "semantic"


class NodeResponse(BaseModel):
    """Response model for a single node in a graph."""

    id: UUID = Field(..., description="Database UUID")
    node_id: str = Field(..., description="Node identifier (e.g., 'python')")
    label: str = Field(..., description="Display name (e.g., 'Python')")
    type: str = Field(..., description="Node type (Tech, Concept, Person)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

    class Config:
        from_attributes = True  # Enable ORM mode (was orm_mode in Pydantic v1)


class EdgeResponse(BaseModel):
    """Response model for a single edge in a graph."""

    id: UUID = Field(..., description="Database UUID")
    source_node_id: UUID = Field(..., description="Source node UUID")
    target_node_id: UUID = Field(..., description="Target node UUID")
    relation: str = Field(..., description="Relationship type (e.g., 'used_for')")

    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    """Response model for a complete knowledge graph."""

    id: UUID = Field(..., description="Graph UUID")
    title: str | None = Field(None, description="Optional graph title")
    description: str | None = Field(None, description="Optional description")
    source_text: str = Field(..., description="Original input text")
    nodes: list[NodeResponse] = Field(default_factory=list, description="Extracted entities")
    edges: list[EdgeResponse] = Field(default_factory=list, description="Relationships")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class GraphListResponse(BaseModel):
    """Response model for list of graphs with pagination."""

    graphs: list[GraphResponse] = Field(..., description="List of graphs")
    total: int = Field(..., description="Total number of graphs")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Offset")


class GraphCreateRequest(BaseModel):
    """Request model for creating a graph."""

    text: str = Field(
        ...,
        description="Text to extract knowledge graph from",
        min_length=1,
        max_length=10000,
        examples=["Python is used for data science and machine learning"],
    )
    title: str | None = Field(None, description="Optional title for the graph", max_length=255)
    description: str | None = Field(None, description="Optional description", max_length=1000)


# =========================================================================
# Semantic Search Schemas (Phase 5)
# =========================================================================


class SemanticSearchResult(BaseModel):
    """Single semantic search result with similarity score."""

    graph: GraphResponse
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score (0-1, higher is more similar)",
    )


class SemanticSearchResponse(BaseModel):
    """Response for semantic search endpoint."""

    results: list[SemanticSearchResult] = Field(..., description="Search results with scores")
    total: int = Field(..., description="Number of results")
    query: str = Field(..., description="Original search query")
    search_mode: str = Field(default="semantic", description="Search mode used")

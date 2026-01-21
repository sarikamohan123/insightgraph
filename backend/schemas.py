"""
Pydantic Schemas
================

Request/response models for API validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============================================
# Extraction Schemas
# ============================================

class Node(BaseModel):
    id: str
    label: str
    type: str
    confidence: float = 0.0


class Edge(BaseModel):
    source: str
    target: str
    relation: str


class ExtractResponse(BaseModel):
    nodes: list[Node]
    edges: list[Edge]


# ============================================
# Authentication Schemas (Phase 6)
# ============================================

class UserRegister(BaseModel):
    """Registration request schema."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User data returned in responses."""

    id: UUID
    email: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""

    user_id: UUID | None = None
    email: str | None = None

"""
Database Models - SQLAlchemy ORM
=================================

Defines the database schema for storing knowledge graphs.

Schema Design:
- graphs: Metadata about each knowledge graph (title, source text, timestamps)
- nodes: Entities extracted from text (Python, AI, etc.)
- edges: Relationships between nodes (used_for, implements, etc.)

All tables use UUID primary keys for better scalability and security.
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """
    User account for authentication.

    Stores user credentials and profile information.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    graphs = relationship("Graph", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class Graph(Base):
    """
    Knowledge graph metadata.

    Represents a complete extraction result from a single text input.
    Contains references to all nodes and edges in the graph.
    """

    __tablename__ = "graphs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=True)  # Optional user-provided title
    description = Column(Text, nullable=True)  # Optional description
    source_text = Column(Text, nullable=False)  # Original input text
    graph_metadata = Column(JSON, nullable=True)  # Flexible storage for extra data

    # Owner (Phase 6 - Authentication)
    # Nullable for backward compatibility with existing graphs
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Semantic search embedding (Phase 5)
    # 768 dimensions for Gemini embedding-001 model
    embedding = Column(Vector(768), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="graphs")
    nodes = relationship("Node", back_populates="graph", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="graph", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Graph(id={self.id}, title={self.title}, nodes={len(self.nodes)}, edges={len(self.edges)})>"


class Node(Base):
    """
    Entity (node) in a knowledge graph.

    Represents an extracted entity like "Python", "AI", "FastAPI", etc.
    """

    __tablename__ = "nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("graphs.id"), nullable=False)

    # Node data from extraction
    node_id = Column(String(255), nullable=False)  # e.g., "python", "fastapi"
    label = Column(String(255), nullable=False)  # Display name: "Python", "FastAPI"
    type = Column(String(50), nullable=False)  # "Tech", "Concept", "Person", etc.
    confidence = Column(Float, nullable=False, default=1.0)  # 0.0-1.0

    # Additional properties (JSONB for flexibility)
    properties = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    graph = relationship("Graph", back_populates="nodes")

    def __repr__(self):
        return f"<Node(id={self.id}, label={self.label}, type={self.type})>"


class Edge(Base):
    """
    Relationship (edge) between two nodes in a knowledge graph.

    Represents connections like "Python used_for AI" or "FastAPI implements REST".
    """

    __tablename__ = "edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("graphs.id"), nullable=False)

    # Source and target nodes
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)

    # Relationship type
    relation = Column(String(100), nullable=False)  # e.g., "used_for", "implements"

    # Additional properties (JSONB for flexibility)
    properties = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    graph = relationship("Graph", back_populates="edges")
    source_node = relationship("Node", foreign_keys=[source_node_id])
    target_node = relationship("Node", foreign_keys=[target_node_id])

    def __repr__(self):
        return f"<Edge(id={self.id}, relation={self.relation})>"

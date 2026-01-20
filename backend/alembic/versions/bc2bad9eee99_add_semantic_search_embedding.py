"""add_semantic_search_embedding

Revision ID: bc2bad9eee99
Revises: c2a0d09f419f
Create Date: 2026-01-16 16:16:45.354356

Phase 5: Semantic Search with pgvector
- Enable pgvector extension
- Add embedding column (768 dimensions for Gemini embedding-001)
- Create index for fast similarity search
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "bc2bad9eee99"
down_revision: str | None = "c2a0d09f419f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Step 1: Enable pgvector extension
    # Note: This requires superuser or the extension must be available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Step 2: Add embedding column to graphs table
    # 768 dimensions matches Gemini embedding-001 model output
    op.add_column("graphs", sa.Column("embedding", Vector(768), nullable=True))

    # Step 3: Create index for fast cosine similarity search
    # Using ivfflat index for approximate nearest neighbor (ANN) search
    # lists=100 is good for datasets up to ~100k rows
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_graphs_embedding
        ON graphs
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    # Remove index first
    op.execute("DROP INDEX IF EXISTS idx_graphs_embedding")

    # Remove embedding column
    op.drop_column("graphs", "embedding")

    # Note: We don't drop the vector extension as other tables might use it

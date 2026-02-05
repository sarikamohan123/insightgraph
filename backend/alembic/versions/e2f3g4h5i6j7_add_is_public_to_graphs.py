"""add_is_public_to_graphs

Revision ID: e2f3g4h5i6j7
Revises: d1a2b3c4d5e6
Create Date: 2026-02-05

Add is_public boolean field to graphs table for public/private visibility.
- Public graphs are visible to all visitors (read-only)
- Private graphs are only visible to their owner
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2f3g4h5i6j7"
down_revision: str | None = "d1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add is_public column with default False (private by default)
    op.add_column(
        "graphs",
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Create index for faster filtering by public status
    op.create_index("idx_graphs_is_public", "graphs", ["is_public"])


def downgrade() -> None:
    # Remove index
    op.drop_index("idx_graphs_is_public", table_name="graphs")

    # Remove is_public column
    op.drop_column("graphs", "is_public")

"""add_user_authentication

Revision ID: d1a2b3c4d5e6
Revises: bc2bad9eee99
Create Date: 2026-01-20

Phase 6: User Authentication
- Create users table for storing user accounts
- Add user_id foreign key to graphs table for ownership
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1a2b3c4d5e6"
down_revision: str | None = "bc2bad9eee99"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Step 1: Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("username", sa.String(100), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # Step 2: Add user_id column to graphs table
    # Nullable to allow existing graphs without owners (backward compatibility)
    op.add_column(
        "graphs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Step 3: Create foreign key constraint
    op.create_foreign_key(
        "fk_graphs_user_id",
        "graphs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",  # If user is deleted, graphs become orphaned (not deleted)
    )

    # Step 4: Create index for faster lookups by user
    op.create_index("idx_graphs_user_id", "graphs", ["user_id"])


def downgrade() -> None:
    # Remove index
    op.drop_index("idx_graphs_user_id", table_name="graphs")

    # Remove foreign key
    op.drop_constraint("fk_graphs_user_id", "graphs", type_="foreignkey")

    # Remove user_id column from graphs
    op.drop_column("graphs", "user_id")

    # Drop users table
    op.drop_table("users")

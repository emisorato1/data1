"""Add deleted_at to conversations and cursor pagination index.

Revision ID: 003
Revises: 002
Create Date: 2026-02-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Composite index for cursor-based pagination:
    # WHERE user_id = ? AND deleted_at IS NULL ORDER BY updated_at DESC, id DESC
    op.create_index(
        "ix_conversations_cursor",
        "conversations",
        ["user_id", sa.text("updated_at DESC"), sa.text("id DESC")],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_conversations_cursor", table_name="conversations")
    op.drop_column("conversations", "deleted_at")

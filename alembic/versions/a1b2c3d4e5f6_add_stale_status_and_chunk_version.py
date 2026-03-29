"""add_stale_status_and_chunk_version

Adds 'stale' value to document status for re-indexing support,
and adds 'version' column to document_chunks for atomic swap.

Revision ID: a1b2c3d4e5f6
Revises: ceb63265e137
Create Date: 2026-03-25 14:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "ceb63265e137"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add version column to document_chunks (default 1 for existing rows)
    op.add_column(
        "document_chunks",
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    # Add index on (document_id, version) for efficient cleanup queries
    op.create_index(
        "ix_document_chunks_document_id_version",
        "document_chunks",
        ["document_id", "version"],
    )


def downgrade() -> None:
    op.drop_index("ix_document_chunks_document_id_version", table_name="document_chunks")
    op.drop_column("document_chunks", "version")

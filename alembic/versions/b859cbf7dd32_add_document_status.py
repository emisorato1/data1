"""add_document_status

Revision ID: b859cbf7dd32
Revises: 15c80ebae43c
Create Date: 2026-03-05 10:06:11.414210
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b859cbf7dd32"
down_revision: str | None = "15c80ebae43c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("status", sa.String(20), server_default="pending", nullable=False))


def downgrade() -> None:
    op.drop_column("documents", "status")

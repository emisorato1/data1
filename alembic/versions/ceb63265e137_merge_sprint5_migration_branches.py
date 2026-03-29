"""merge_sprint5_migration_branches

Revision ID: ceb63265e137
Revises: 9f3c7a12d9ab, yyy_add_feedback_table
Create Date: 2026-03-10 10:53:20.948246
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "ceb63265e137"
down_revision: str | None = ("9f3c7a12d9ab", "yyy_add_feedback_table")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

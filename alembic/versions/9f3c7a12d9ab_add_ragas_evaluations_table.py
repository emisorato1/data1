"""add_ragas_evaluations_table

Revision ID: 9f3c7a12d9ab
Revises: b859cbf7dd32
Create Date: 2026-03-06 14:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9f3c7a12d9ab"
down_revision: str | None = "b859cbf7dd32"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ragas_evaluations",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("dag_run_id", sa.String(length=255), nullable=True),
        sa.Column("dataset_path", sa.Text(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("faithfulness", sa.Float(), nullable=False),
        sa.Column("answer_relevancy", sa.Float(), nullable=False),
        sa.Column("context_precision", sa.Float(), nullable=False),
        sa.Column("context_recall", sa.Float(), nullable=False),
        sa.Column(
            "thresholds",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "below_thresholds",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "sample_results",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ragas_evaluations_created_at", "ragas_evaluations", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ragas_evaluations_created_at", table_name="ragas_evaluations")
    op.drop_table("ragas_evaluations")

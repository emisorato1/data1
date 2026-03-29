"""add_hash_chain_to_audit_logs

Revision ID: xxx_add_hash_chain_to_audit_logs
Revises:
Create Date: 2026-03-06 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "xxx_add_hash_chain_to_audit_logs"
down_revision = "b859cbf7dd32"  # Just put the last one found
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("hash_chain", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_logs", "hash_chain")

"""add_is_pinned_and_is_favorite_to_conversations

Revision ID: 646bcaa46a68
Revises: a1b2c3d4e5f6
Create Date: 2026-03-25 12:17:10.034953
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '646bcaa46a68'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('is_pinned', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('conversations', sa.Column('is_favorite', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('conversations', 'is_favorite')
    op.drop_column('conversations', 'is_pinned')

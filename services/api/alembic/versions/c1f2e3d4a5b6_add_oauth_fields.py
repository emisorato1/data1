"""add oauth fields to users

Revision ID: c1f2e3d4a5b6
Revises: a6e234523e27
Create Date: 2026-01-23 09:53:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1f2e3d4a5b6'
down_revision: Union[str, Sequence[str], None] = 'a6e234523e27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add OAuth fields to users table."""
    # Add auth_provider column with default 'local' for existing users
    op.add_column('users', sa.Column('auth_provider', sa.String(length=50), nullable=False, server_default='local'))
    
    # Add google_id column (nullable, unique for OAuth users)
    op.add_column('users', sa.Column('google_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)
    
    # Add avatar_url column for profile picture
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    
    # Add full_name column for display name
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    
    # Add updated_at column for tracking updates
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Make password_hash nullable for OAuth-only users
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(length=255),
                    nullable=True)


def downgrade() -> None:
    """Remove OAuth fields from users table."""
    # Restore password_hash to NOT NULL (requires all users to have passwords)
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(length=255),
                    nullable=False)
    
    # Remove added columns
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'full_name')
    op.drop_column('users', 'avatar_url')
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'auth_provider')

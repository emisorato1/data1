"""Seed admin user: admin@banco.com

Revision ID: 005
Revises: 004
Create Date: 2026-03-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Passwords: admin123!
    # Hash generado con bcrypt (rounds=12)
    op.execute(
        sa.text("""
        INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser)
        VALUES (1000, 'admin@banco.com',
                '$2b$12$UA6R2c23z8qPEPwJSCzoHehYFGof7B48RcnPz/laSKL4TFz9hbx8.',
                'Admin Sistema', true, true)
        ON CONFLICT (email) DO NOTHING
        """)
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM users WHERE email = 'admin@banco.com'"))

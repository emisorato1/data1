"""Refresh token generation and hashing.

Refresh tokens are opaque random strings stored hashed (SHA-256) in the DB.
TTL: 7 days. Rotation: each use invalidates the previous token.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

REFRESH_TOKEN_EXPIRE_DAYS = 7
_TOKEN_BYTES = 32  # 256-bit entropy


def generate_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token."""
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_token(raw_token: str) -> str:
    """Produce a SHA-256 hex digest of the raw token for DB storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def refresh_token_expires_at() -> datetime:
    """Calculate the expiration datetime for a new refresh token."""
    return datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

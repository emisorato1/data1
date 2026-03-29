"""JWT access token creation and decoding.

Algorithm: HS256 (symmetric). Tokens carry sub, exp, iat, role claims.
Access tokens live 15 minutes.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.config.settings import settings

_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15


def create_access_token(
    user_id: int,
    role: str,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        user_id: The user's database ID (becomes ``sub`` claim).
        role: ``"admin"`` or ``"user"``.
        expires_delta: Custom expiry. Defaults to 15 minutes.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "role": role,
    }
    return jwt.encode(  # type: ignore[no-any-return]
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded payload dict with ``sub``, ``exp``, ``iat``, ``role``.

    Raises:
        jwt.ExpiredSignatureError: Token has expired.
        jwt.InvalidTokenError: Token is malformed or signature is invalid.
    """
    return jwt.decode(  # type: ignore[no-any-return]
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[_ALGORITHM],
    )

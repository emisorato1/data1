"""FastAPI dependency injection container."""

import logging

import jwt
from fastapi import Cookie, Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.infrastructure.database.models.user import User
from src.infrastructure.database.session import get_db
from src.infrastructure.security.jwt import decode_access_token
from src.shared.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

__all__ = ["get_current_user", "get_db", "get_redis"]


async def get_redis(request: Request) -> Redis:  # type: ignore[type-arg]
    """Retrieve the Redis client from app.state (set during lifespan)."""
    redis: Redis = request.app.state.redis  # type: ignore[type-arg]
    return redis


async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate JWT from HTTPOnly cookie and return the authenticated User.

    Reads the ``access_token`` cookie, decodes the JWT, loads the user
    from the database, and verifies the account is active.

    Raises:
        AuthenticationError: If the token is missing, invalid, expired,
            or the user is inactive/not found.
    """
    if not access_token:
        raise AuthenticationError(message="Not authenticated.")

    # Decode JWT
    try:
        payload = decode_access_token(access_token)
    except jwt.ExpiredSignatureError:
        raise AuthenticationError(message="Token has expired.") from None
    except jwt.InvalidTokenError:
        raise AuthenticationError(message="Invalid token.") from None

    # Extract user_id from sub claim
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError(message="Invalid token payload.")

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise AuthenticationError(message="Invalid token payload.") from None

    # Load user from DB
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError(message="User not found.")

    if not user.is_active:
        raise AuthenticationError(message="Account is disabled.")

    return user  # type: ignore[no-any-return]

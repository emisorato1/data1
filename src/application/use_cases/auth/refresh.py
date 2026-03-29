"""Use case: Refresh — rota refresh token y emite nuevo access token.

Security: si se detecta reuso de un token ya revocado, se revocan TODOS
los refresh tokens del usuario (posible robo de token).
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.auth_dtos import AuthUserResponse
from src.infrastructure.database.models.user import RefreshToken, User
from src.infrastructure.security.jwt import create_access_token
from src.infrastructure.security.refresh_token import (
    generate_refresh_token,
    hash_token,
    refresh_token_expires_at,
)
from src.shared.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


async def refresh(
    raw_refresh_token: str | None,
    db: AsyncSession,
) -> tuple[AuthUserResponse, str, str]:
    """Rotate refresh token and issue a new access token.

    Args:
        raw_refresh_token: The raw refresh token from the cookie.
        db: Async database session.

    Returns:
        Tuple of (user_response, new_access_token, new_raw_refresh_token).

    Raises:
        AuthenticationError: If the token is missing, invalid, expired,
            or already revoked (reuse detection).
    """
    if not raw_refresh_token:
        raise AuthenticationError(message="Refresh token is required.")

    token_hash_value = hash_token(raw_refresh_token)
    now = datetime.now(UTC)

    # 1. Buscar el refresh token en DB
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash_value)
    result = await db.execute(stmt)
    stored_token = result.scalar_one_or_none()

    if stored_token is None:
        logger.warning("refresh_failed: token not found")
        raise AuthenticationError(message="Invalid refresh token.")

    # 2. Detectar reuso (token ya revocado = posible robo)
    if stored_token.revoked_at is not None:
        logger.warning(
            "refresh_reuse_detected: user_id=%s token_id=%s — revoking all tokens",
            stored_token.user_id,
            stored_token.id,
        )
        # Revocar TODOS los tokens del usuario
        revoke_all = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == stored_token.user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await db.execute(revoke_all)
        await db.flush()
        raise AuthenticationError(message="Refresh token reuse detected. All sessions revoked.")

    # 3. Verificar expiracion
    if stored_token.expires_at < now:
        logger.warning("refresh_failed: expired token user_id=%s", stored_token.user_id)
        # Revocar el token expirado
        stored_token.revoked_at = now
        await db.flush()
        raise AuthenticationError(message="Refresh token has expired.")

    # 4. Revocar el token actual (rotacion)
    stored_token.revoked_at = now

    # 5. Cargar el usuario
    user_stmt = select(User).where(User.id == stored_token.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        logger.warning("refresh_failed: user inactive or not found id=%s", stored_token.user_id)
        await db.flush()
        raise AuthenticationError(message="User account is disabled.")

    # 6. Generar nuevo par de tokens
    role = "admin" if user.is_superuser else "user"
    new_access_token = create_access_token(user_id=user.id, role=role)

    new_raw_refresh = generate_refresh_token()
    new_refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_raw_refresh),
        expires_at=refresh_token_expires_at(),
    )
    db.add(new_refresh_record)
    await db.flush()

    logger.info("refresh_success: user_id=%s", user.id)

    user_response = AuthUserResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=role,
    )

    return user_response, new_access_token, new_raw_refresh

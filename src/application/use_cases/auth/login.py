"""Use case: Login — valida credenciales y emite tokens."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.auth_dtos import AuthUserResponse
from src.infrastructure.database.models.user import RefreshToken, User
from src.infrastructure.security.jwt import create_access_token
from src.infrastructure.security.password import verify_password
from src.infrastructure.security.refresh_token import (
    generate_refresh_token,
    hash_token,
    refresh_token_expires_at,
)
from src.shared.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


async def login(
    email: str,
    password: str,
    db: AsyncSession,
) -> tuple[AuthUserResponse, str, str]:
    """Authenticate user and generate token pair.

    Args:
        email: User email.
        password: Plain-text password.
        db: Async database session.

    Returns:
        Tuple of (user_response, access_token, raw_refresh_token).

    Raises:
        AuthenticationError: If credentials are invalid.
    """
    # 1. Buscar usuario por email
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning("login_failed: user not found email=%s", email)
        raise AuthenticationError(message="Invalid email or password.")

    # 2. Verificar que la cuenta este activa
    if not user.is_active:
        logger.warning("login_failed: inactive user id=%s", user.id)
        raise AuthenticationError(message="Account is disabled.")

    # 3. Verificar password con bcrypt
    if not verify_password(password, user.hashed_password):
        logger.warning("login_failed: bad password user_id=%s", user.id)
        raise AuthenticationError(message="Invalid email or password.")

    # 4. Determinar rol
    role = "admin" if user.is_superuser else "user"

    # 5. Generar access token
    access_token = create_access_token(user_id=user.id, role=role)

    # 6. Generar refresh token y almacenar hash en DB
    raw_refresh = generate_refresh_token()
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=refresh_token_expires_at(),
    )
    db.add(refresh_record)
    await db.flush()

    logger.info("login_success: user_id=%s role=%s", user.id, role)

    user_response = AuthUserResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=role,
    )

    return user_response, access_token, raw_refresh

"""Use case: Logout — revoca refresh token en DB."""

import logging
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.user import RefreshToken
from src.infrastructure.security.refresh_token import hash_token

logger = logging.getLogger(__name__)


async def logout(
    raw_refresh_token: str | None,
    db: AsyncSession,
) -> None:
    """Revoke the refresh token so it cannot be reused.

    Args:
        raw_refresh_token: The raw refresh token from the cookie.
        db: Async database session.

    Note:
        This operation is idempotent — calling it with an already-revoked
        or missing token does not raise an error.
    """
    if not raw_refresh_token:
        return

    token_hash = hash_token(raw_refresh_token)
    now = datetime.now(UTC)

    # Revocar el token (marcar revoked_at)
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    result = await db.execute(stmt)
    await db.flush()

    if result.rowcount:  # type: ignore[attr-defined]
        # Obtener user_id para logging
        lookup = select(RefreshToken.user_id).where(RefreshToken.token_hash == token_hash)
        row = (await db.execute(lookup)).scalar_one_or_none()
        logger.info("logout_success: user_id=%s", row)
    else:
        logger.debug("logout: token not found or already revoked")

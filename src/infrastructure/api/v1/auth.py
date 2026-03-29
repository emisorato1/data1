"""Auth endpoints: login, logout, refresh.

Tokens are delivered via HTTPOnly cookies (prevents XSS token theft).
Response body contains user info only, never raw tokens.
"""

from typing import Any, Literal

from fastapi import APIRouter, Cookie, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.auth_dtos import LoginRequest
from src.application.use_cases.auth.login import login as execute_login
from src.application.use_cases.auth.logout import logout as execute_logout
from src.application.use_cases.auth.refresh import refresh as execute_refresh
from src.config.settings import settings
from src.infrastructure.api.dependencies import get_db
from src.infrastructure.security.jwt import ACCESS_TOKEN_EXPIRE_MINUTES
from src.infrastructure.security.refresh_token import REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Cookie settings
_SECURE = settings.is_production
_SAMESITE: Literal["lax", "strict", "none"] = "lax"
_ACCESS_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
_REFRESH_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # seconds
_REFRESH_PATH = "/api/v1/auth"  # refresh cookie scoped to auth endpoints


def _envelope(data: Any, status_code: int = 200) -> JSONResponse:
    """Wrap response in standard {data, error, meta} envelope."""
    return JSONResponse(
        status_code=status_code,
        content={"data": data, "error": None, "meta": {}},
    )


def _set_auth_cookies(
    response: JSONResponse,
    access_token: str,
    refresh_token: str,
) -> None:
    """Set access_token and refresh_token as HTTPOnly cookies."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=_SECURE,
        samesite=_SAMESITE,
        max_age=_ACCESS_MAX_AGE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_SECURE,
        samesite=_SAMESITE,
        max_age=_REFRESH_MAX_AGE,
        path=_REFRESH_PATH,
    )


def _clear_auth_cookies(response: JSONResponse) -> None:
    """Clear auth cookies by setting max_age=0."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path=_REFRESH_PATH)


@router.post("/login")
async def login_endpoint(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Authenticate user and set JWT cookies.

    Returns user info in the response body.
    Access token (15min) and refresh token (7d) are set as HTTPOnly cookies.
    """
    user_response, access_token, raw_refresh = await execute_login(
        email=body.email,
        password=body.password,
        db=db,
    )

    response = _envelope(user_response.model_dump())
    _set_auth_cookies(response, access_token, raw_refresh)
    return response


@router.post("/logout")
async def logout_endpoint(
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Invalidate refresh token and clear cookies."""
    await execute_logout(raw_refresh_token=refresh_token, db=db)

    response = _envelope({"message": "Logged out successfully."})
    _clear_auth_cookies(response)
    return response


@router.post("/refresh")
async def refresh_endpoint(
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Rotate refresh token and issue new access token.

    The old refresh token is revoked. If a revoked token is reused,
    all tokens for that user are revoked (theft detection).
    """
    user_response, new_access, new_refresh = await execute_refresh(
        raw_refresh_token=refresh_token,
        db=db,
    )

    response = _envelope(user_response.model_dump())
    _set_auth_cookies(response, new_access, new_refresh)
    return response

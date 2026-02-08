from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import settings

from app.application.services.auth_service import AuthService
from app.domain.enums.role_name import RoleName
from app.infrastructure.db.repositories.role_repo import RoleRepository
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.db.session import get_db
from app.infrastructure.http.google_oauth import google_oauth_client

from app.presentation.http.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.presentation.http.schemas.oauth import (
    GoogleAuthUrlResponse,
    GoogleCallbackRequest,
)
from app.presentation.http.deps.auth import get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        tenant_id=user.tenant_id,
        role=user.role.name if getattr(user, "role", None) else str(user.role_id),
        is_active=user.is_active,
        auth_provider=getattr(user, "auth_provider", "local"),
        avatar_url=getattr(user, "avatar_url", None),
        full_name=getattr(user, "full_name", None),
    )


@router.post("/register", response_model=UserResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    service = AuthService(user_repo, role_repo)

    # 1) tenant por defecto si no viene del front
    tenant_id: UUID = payload.tenant_id or UUID("00000000-0000-0000-0000-000000000000")

    try:
        user = await service.register(
            email=payload.email, 
            password=payload.password, 
            tenant_id=tenant_id,
            role_name=payload.role,  # Pasar el rol opcional
        )
        return _to_user_response(user)
    except ValueError as e:
        if str(e) == "EMAIL_ALREADY_REGISTERED":
            raise HTTPException(status_code=409, detail="EMAIL_ALREADY_REGISTERED")
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login_json(
    payload: LoginRequest, 
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Login en JSON: {email, password}"""
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    service = AuthService(user_repo, role_repo)

    try:
        token, user = await service.login(email=payload.email, password=payload.password)
        
        # Set HttpOnly Cookie
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRES_MINUTES * 60,
        )
        
        return TokenResponse(access_token=None, user=_to_user_response(user))
    except ValueError as e:
        if str(e) == "INVALID_CREDENTIALS":
            raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")
        if str(e) == "USER_INACTIVE":
            raise HTTPException(status_code=403, detail="USER_INACTIVE")
        raise




# ============================================================================
# Google OAuth 2.0 Endpoints
# ============================================================================


@router.get("/google/url", response_model=GoogleAuthUrlResponse)
async def get_google_auth_url():
    """
    Get Google OAuth authorization URL.
    
    The client should redirect the user to this URL to start the OAuth flow.
    Store the returned state token to validate the callback.
    """
    auth_url, state = google_oauth_client.get_authorization_url()
    return GoogleAuthUrlResponse(auth_url=auth_url, state=state)


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(
    payload: GoogleCallbackRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.
    
    Exchange the authorization code for user info and create/link user account.
    Returns JWT token for authenticated session.
    """
    try:
        # Exchange code for user info
        google_user = await google_oauth_client.authenticate(payload.code)
        
        # Verify email is verified by Google
        if not google_user.verified_email:
            raise HTTPException(
                status_code=400,
                detail="GOOGLE_EMAIL_NOT_VERIFIED",
            )
        
        # Login or register user
        user_repo = UserRepository(db)
        role_repo = RoleRepository(db)
        service = AuthService(user_repo, role_repo)
        
        token, user = await service.google_login(google_user=google_user)

        # Set HttpOnly Cookie
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRES_MINUTES * 60,
        )

        return TokenResponse(access_token=None, user=_to_user_response(user))
        
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "USER_INACTIVE":
            raise HTTPException(status_code=403, detail="USER_INACTIVE")
        # Token exchange or user info failed
        raise HTTPException(status_code=400, detail=f"GOOGLE_AUTH_FAILED: {error_msg}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/logout")
async def logout(response: Response):
    """Limpia la cookie de sesión."""
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )
    return {"message": "Logout exitoso"}


@router.get("/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user)):
    """Devuelve el usuario actual (alias de /session para compatibilidad)."""
    return _to_user_response(user)

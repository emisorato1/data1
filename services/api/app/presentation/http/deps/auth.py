from __future__ import annotations

from typing import Callable
from functools import wraps

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


# ============================================================================
# Core Authentication Dependencies
# ============================================================================

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """
    Obtiene el usuario actual desde la cookie o el header Authorization.
    Lanza 401 si no hay token válido.
    """
    # 1. Intentar leer de Cookie
    token = request.cookies.get(settings.COOKIE_NAME)
    
    # 2. Si no hay cookie, intentar Header (Bearer)
    if not token and creds:
        token = creds.credentials

    if not token:
        raise HTTPException(status_code=401, detail="NOT_AUTHENTICATED")
    
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="USER_NOT_FOUND")

    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """
    Similar a get_current_user pero retorna None si no hay token.
    Útil para rutas públicas que pueden tener comportamiento diferente si hay usuario.
    """
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token and creds:
        token = creds.credentials

    if not token:
        return None
    
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        return user
    except Exception:
        return None


# ============================================================================
# Role-Based Access Control Dependencies
# ============================================================================

def require_role(*allowed_roles: str) -> Callable:
    """
    Factory para crear dependencias que requieren roles específicos.
    
    Uso:
        @router.get("/admin-only")
        async def admin_route(user = Depends(require_role("admin"))):
            ...
        
        @router.get("/private-or-admin")
        async def private_route(user = Depends(require_role("private", "admin"))):
            ...
    """
    async def role_checker(
        user = Depends(get_current_user),
    ):
        # Obtener el nombre del rol del usuario
        user_role = user.role.name if hasattr(user.role, "name") else str(user.role_id)
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"FORBIDDEN: Role '{user_role}' not in allowed roles {allowed_roles}",
            )
        return user
    
    return role_checker


# Dependencias predefinidas para roles comunes
require_admin = require_role("admin")
require_private = require_role("private", "admin")  # private o admin
require_public = require_role("public", "private", "admin")  # cualquier usuario autenticado

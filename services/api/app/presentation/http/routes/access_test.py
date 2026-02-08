# /app/presentation/http/routes/access_test.py
"""
Rutas de prueba para verificar el control de acceso basado en roles.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.http.deps.auth import (
    get_current_user,
    get_current_user_optional,
    require_role,
    require_admin,
    require_private,
)

router = APIRouter(prefix="/access-test", tags=["access-test"])


@router.get("/public")
async def public_route(user=Depends(get_current_user_optional)):
    """
    Ruta pública - no requiere autenticación.
    Si hay usuario logueado, muestra su info.
    """
    if user:
        return {
            "message": "Ruta pública - Usuario autenticado",
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.name if hasattr(user.role, "name") else str(user.role_id),
            "tenant_id": str(user.tenant_id),
        }
    return {
        "message": "Ruta pública - Sin autenticación",
        "user_id": None,
    }


@router.get("/authenticated")
async def authenticated_route(user=Depends(get_current_user)):
    """
    Ruta que requiere autenticación (cualquier rol).
    """
    return {
        "message": "Ruta autenticada - Acceso concedido",
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.name if hasattr(user.role, "name") else str(user.role_id),
        "tenant_id": str(user.tenant_id),
    }


@router.get("/private")
async def private_route(user=Depends(require_private)):
    """
    Ruta privada - requiere rol 'private' o 'admin'.
    Usuarios con rol 'public' recibirán 403.
    """
    return {
        "message": "Ruta privada - Acceso concedido",
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.name if hasattr(user.role, "name") else str(user.role_id),
        "access_level": "private",
    }


@router.get("/admin")
async def admin_route(user=Depends(require_admin)):
    """
    Ruta de administrador - requiere rol 'admin'.
    Usuarios con rol 'public' o 'private' recibirán 403.
    """
    return {
        "message": "Ruta de admin - Acceso concedido",
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.name if hasattr(user.role, "name") else str(user.role_id),
        "access_level": "admin",
    }


@router.get("/custom-roles")
async def custom_roles_route(user=Depends(require_role("admin", "private"))):
    """
    Ejemplo de ruta con roles personalizados usando require_role().
    """
    return {
        "message": "Ruta con roles personalizados - Acceso concedido",
        "user_id": str(user.id),
        "allowed_roles": ["admin", "private"],
        "your_role": user.role.name if hasattr(user.role, "name") else str(user.role_id),
    }

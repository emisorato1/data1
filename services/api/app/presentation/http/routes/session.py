from fastapi import APIRouter, Depends
from app.application.services.auth_service import AuthService
from app.infrastructure.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/session")
async def session(db: AsyncSession = Depends(get_db), user=Depends(AuthService.current_user)):
    # devolvé lo mínimo que el front necesita
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.name if getattr(user, "role", None) else None,
        "tenant_id": str(user.tenant_id),
        "is_active": user.is_active,
    }
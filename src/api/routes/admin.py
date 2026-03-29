from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.services.audit_service import AuditService
from src.infrastructure.api.dependencies import get_current_user
from src.infrastructure.database.models.user import User
from src.infrastructure.database.session import get_db


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify that the authenticated user has admin privileges.

    Raises:
        HTTPException 403: If the user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user


router = APIRouter(prefix="/admin/audit-logs", tags=["Admin Audit Logs"])


@router.get("", response_model=list[dict])
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Obtiene los logs de auditoria con paginacion (Solo Admin)."""
    audit_service = AuditService(session)
    logs = await audit_service.get_logs(limit=limit, offset=offset)

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "hash_chain": log.hash_chain,
            "status": log.status,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.post("/verify")
async def verify_audit_chain(
    session: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Verifica la integridad criptografica de la cadena de hashes de los logs."""
    audit_service = AuditService(session)
    is_valid = await audit_service.verify_chain()

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Audit log integrity check failed. Chain is broken.",
        )

    return {"status": "ok", "message": "Audit log chain is valid and intact."}

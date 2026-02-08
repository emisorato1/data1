from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.db.deps import get_db
from app.infrastructure.db.repositories.message_repo import MessageRepository
from app.infrastructure.http.rag_client import RagClient
from app.application.services.message_service import MessageService
from app.presentation.http.deps.auth import get_current_user
from app.presentation.http.schemas.message import (
    MessageCreateRequest,
    MessageRunResponse,
    MessageResponse,
    MessageSourceResponse,
)

router = APIRouter(prefix="/messages", tags=["messages"])


def to_message_response(m) -> MessageResponse:
    return MessageResponse(
        id=m.id,
        session_id=m.session_id,
        user_role=m.user_role,
        direction=m.direction,
        content=m.content,
        sources=[
            MessageSourceResponse(
                source_name=s.source_name,
                snippet=s.snippet,
                url=s.url,
                score=s.score,
            )
            for s in (m.sources or [])
        ],
    )


@router.post("/run", response_model=MessageRunResponse, status_code=status.HTTP_201_CREATED)
async def run_message(
    payload: MessageCreateRequest, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Ejecuta un mensaje contra el agente RAG. Requiere autenticación."""
    try:
        rag = RagClient(base_url=getattr(settings, "RAG_BASE_URL", "http://rag-generation:2024"))
        svc = MessageService(msg_repo=MessageRepository(db), rag=rag)

        # Extraer rol del usuario autenticado
        user_role = current_user.role.name if hasattr(current_user.role, "name") else str(current_user.role_id)

        user_msg, assistant_msg = await svc.send_and_receive(
            session_id=payload.session_id,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            user_role=user_role,
            content=payload.content,
        )

        return MessageRunResponse(
            user_message=to_message_response(user_msg),
            assistant_message=to_message_response(assistant_msg),
        )
    except Exception as e:
        # cuando algo falla (rag caído, timeout, etc.)
        import traceback
        print(f"RAG ERROR: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"RAG_CALL_FAILED: {type(e).__name__}: {str(e)}")
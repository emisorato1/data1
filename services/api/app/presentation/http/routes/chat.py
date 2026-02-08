# presentation/http/routes/chat.py
from __future__ import annotations

import json
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.application.services.chat_service import ChatService
from app.presentation.http.schemas.chat import ChatRequest
from app.presentation.http.deps.auth import get_current_user_optional

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


def _resolve_session_id(payload: ChatRequest, session_id_qs: Optional[UUID]) -> UUID:
    """
    El front manda session_id por querystring.
    Pero dejamos compatibilidad por si también viene en el body.
    """
    sid = session_id_qs or getattr(payload, "session_id", None)
    if not sid:
        raise HTTPException(status_code=422, detail="session_id is required (query or body)")
    return sid


@router.post("")
async def chat(
    payload: ChatRequest,
    session_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    sid = _resolve_session_id(payload, session_id)
    
    # Extraer user_id y tenant_id del usuario autenticado (para long-term memory)
    user_id = current_user.id if current_user else None
    tenant_id = current_user.tenant_id if current_user else None
    
    return await ChatService(db).execute(
        session_id=sid,
        user_role=payload.user_role,
        message=payload.message,
        user_id=user_id,
        tenant_id=tenant_id,
    )


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    session_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    sid = _resolve_session_id(payload, session_id)
    
    # Extraer user_id y tenant_id del usuario autenticado (para long-term memory)
    user_id = current_user.id if current_user else None
    tenant_id = current_user.tenant_id if current_user else None

    async def event_gen():
        # Evento inicial (para que el front sepa que arrancó)
        yield f"data: {json.dumps({'content': '', 'done': False, 'status': 'thinking'})}\n\n"

        async for chunk in ChatService(db).execute_stream(
            session_id=sid,
            user_role=payload.user_role,
            message=payload.message,
            user_id=user_id,
            tenant_id=tenant_id,
        ):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ✅ Router legacy para assistant-ui (ruta vieja)
legacy_router = APIRouter(prefix="/chatbot/chat", tags=["chat-legacy"])


@legacy_router.post("/stream")
async def legacy_chat_stream(
    payload: ChatRequest,
    session_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    return await chat_stream(payload, session_id=session_id, db=db, current_user=current_user)

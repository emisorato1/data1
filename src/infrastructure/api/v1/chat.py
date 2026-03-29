"""Conversation CRUD + chat streaming endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from src.application.dtos.rag_dtos import (
    CreateConversationRequest,
    RenameConversationRequest,
    SendMessageRequest,
)
from src.application.use_cases.rag.conversations import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    update_conversation,
)
from src.application.use_cases.rag.stream_response import (
    prepare_chat_context,
    stream_rag_events,
)
from src.infrastructure.api.dependencies import get_current_user, get_db
from src.infrastructure.database.models.user import User
from src.infrastructure.database.repositories.conversation_repository import (
    ConversationRepository,
)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def _envelope(data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"data": data, "error": None, "meta": {}},
    )


@router.post(
    "",
    summary="Create a new conversation",
    status_code=201,
)
async def create_conversation_endpoint(
    body: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Create a new conversation. Returns the conversation with its thread_id (= id)."""
    result = await create_conversation(
        user_id=current_user.id,
        title=body.title,
        db=db,
        repo=ConversationRepository(db),
    )
    return _envelope(result.model_dump(mode="json"), status_code=201)


@router.get(
    "",
    summary="List conversations with cursor pagination",
)
async def list_conversations_endpoint(
    cursor: str | None = Query(None, description="Opaque cursor for next page"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """List active conversations for the current user, ordered by most recent activity."""
    page = await list_conversations(
        user_id=current_user.id,
        cursor=cursor,
        limit=limit,
        db=db,
        repo=ConversationRepository(db),
    )
    return _envelope(page.model_dump(mode="json"))


@router.get(
    "/{conversation_id}",
    summary="Get conversation detail with messages",
)
async def get_conversation_endpoint(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Get a single conversation with all its messages."""
    result = await get_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        db=db,
        repo=ConversationRepository(db),
    )
    return _envelope(result.model_dump(mode="json"))


@router.patch(
    "/{conversation_id}",
    summary="Update conversation (rename, pin, favorite)",
)
async def update_conversation_endpoint(
    conversation_id: uuid.UUID,
    body: RenameConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Update a conversation. Only the owner can update."""
    result = await update_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        db=db,
        repo=ConversationRepository(db),
        title=body.title,
        is_pinned=body.is_pinned,
        is_favorite=body.is_favorite,
    )
    return _envelope(result.model_dump(mode="json"))


@router.delete(
    "/{conversation_id}",
    summary="Soft-delete conversation",
    status_code=204,
)
async def delete_conversation_endpoint(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Soft-delete a conversation. Only the owner can delete."""
    await delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        db=db,
        repo=ConversationRepository(db),
    )
    return JSONResponse(status_code=204, content=None)


# ── Chat SSE streaming ───────────────────────────────────────


@router.post(
    "/{conversation_id}/messages",
    summary="Send message and stream RAG response via SSE",
)
async def send_message_endpoint(
    conversation_id: uuid.UUID,
    body: SendMessageRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    """Send a user message and receive the RAG response as an SSE stream.

    SSE events emitted:
    - ``event: token``  -- incremental content (``{"content": "..."}``)
    - ``event: done``   -- final event (``{"sources": [...], "message_id": "..."}``)
    - ``event: error``  -- error event (``{"code": "...", "message": "..."}``)
    """
    # Phase 1 - validate conversation & persist user message.
    # Runs BEFORE creating EventSourceResponse so that NotFoundError
    # propagates to FastAPI's exception handlers (not inside SSE generator).
    repo = ConversationRepository(db)
    await prepare_chat_context(
        conversation_id=conversation_id,
        user_id=current_user.id,
        message=body.message,
        db=db,
        repo=repo,
        background_tasks=background_tasks,
    )

    # Phase 2 - stream RAG response as SSE events.
    rag_graph = request.app.state.rag_graph

    async def event_generator():
        async for sse_event in stream_rag_events(
            conversation_id=conversation_id,
            user_id=current_user.id,
            message=body.message,
            db=db,
            rag_graph=rag_graph,
        ):
            yield sse_event

    return EventSourceResponse(event_generator())

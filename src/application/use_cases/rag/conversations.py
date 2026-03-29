"""Use cases for conversation CRUD operations."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.rag_dtos import (
    ConversationDetail,
    ConversationSummary,
    MessageResponse,
)
from src.domain.repositories.conversation_repository import ConversationRepositoryBase
from src.infrastructure.api.schemas.pagination import CursorPage
from src.shared.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


async def create_conversation(
    user_id: int,
    title: str | None,
    db: AsyncSession,
    repo: ConversationRepositoryBase,
) -> ConversationSummary:
    """Create a new conversation (thread) for the given user."""
    conversation = await repo.create(user_id=user_id, title=title)
    await db.commit()
    await db.refresh(conversation)
    logger.info("conversation_created user_id=%s id=%s", user_id, conversation.id)
    return ConversationSummary.model_validate(conversation)  # type: ignore[no-any-return]


async def list_conversations(
    user_id: int,
    cursor: str | None,
    limit: int,
    db: AsyncSession,
    repo: ConversationRepositoryBase,
) -> CursorPage[ConversationSummary]:
    """List active conversations for a user with cursor-based pagination."""
    try:
        rows = await repo.list_by_user(user_id=user_id, cursor=cursor, limit=limit)
    except ValueError as e:
        raise ValidationError(message=str(e)) from e

    # Convert ORM objects to DTOs before passing to CursorPage
    items = [ConversationSummary.model_validate(r) for r in rows]

    return CursorPage[ConversationSummary].create(
        items=items,
        limit=limit,
        cursor_field="updated_at",
        id_field="id",
    )


async def get_conversation(
    conversation_id: uuid.UUID,
    user_id: int,
    db: AsyncSession,
    repo: ConversationRepositoryBase,
) -> ConversationDetail:
    """Get conversation detail with messages."""
    conversation = await repo.get_by_id(conversation_id, user_id)
    if conversation is None:
        raise NotFoundError(message="Conversation not found.")

    # Sort messages by created_at ascending for chronological order
    sorted_messages = sorted(conversation.messages, key=lambda m: m.created_at)
    messages = [MessageResponse.model_validate(m) for m in sorted_messages]

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages,
    )


async def update_conversation(
    conversation_id: uuid.UUID,
    user_id: int,
    db: AsyncSession,
    repo: ConversationRepositoryBase,
    title: str | None = None,
    is_pinned: bool | None = None,
    is_favorite: bool | None = None,
) -> ConversationSummary:
    """Update a conversation. Only the owner can update."""
    conversation = await repo.update(
        conversation_id, user_id, title=title, is_pinned=is_pinned, is_favorite=is_favorite
    )
    if conversation is None:
        raise NotFoundError(message="Conversation not found.")
    await db.commit()
    await db.refresh(conversation)
    logger.info("conversation_updated id=%s", conversation_id)
    return ConversationSummary.model_validate(conversation)  # type: ignore[no-any-return]


async def delete_conversation(
    conversation_id: uuid.UUID,
    user_id: int,
    db: AsyncSession,
    repo: ConversationRepositoryBase,
) -> None:
    """Soft-delete a conversation. Only the owner can delete."""
    deleted = await repo.soft_delete(conversation_id, user_id)
    if not deleted:
        raise NotFoundError(message="Conversation not found.")
    await db.commit()
    logger.info("conversation_soft_deleted id=%s user_id=%s", conversation_id, user_id)

"""SQLAlchemy implementation of ConversationRepository."""

import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.repositories.conversation_repository import ConversationRepositoryBase
from src.infrastructure.api.schemas.pagination import decode_cursor
from src.infrastructure.database.models.conversation import Conversation


class ConversationRepository(ConversationRepositoryBase):
    async def rename(self, conversation_id: uuid.UUID, user_id: int, new_title: str) -> Conversation | None:
        # Kept for interface backward compatibility
        return await self.update(conversation_id, user_id, title=new_title)

    """Postgres-backed conversation repository with cursor pagination."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: int, title: str | None = None) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def list_by_user(
        self,
        user_id: int,
        cursor: str | None = None,
        limit: int = 20,
    ) -> list[Conversation]:
        """Keyset pagination: WHERE (updated_at, id) < cursor ORDER BY updated_at DESC, id DESC."""
        query = select(Conversation).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )

        if cursor:
            cursor_ts, cursor_id = decode_cursor(cursor)
            query = query.where(
                or_(
                    Conversation.updated_at < cursor_ts,
                    and_(
                        Conversation.updated_at == cursor_ts,
                        Conversation.id < uuid.UUID(cursor_id),
                    ),
                )
            )

        query = query.order_by(
            Conversation.updated_at.desc(),
            Conversation.id.desc(),
        )
        # +1 to detect has_more
        query = query.limit(limit + 1)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, conversation_id: uuid.UUID, user_id: int) -> Conversation | None:
        query = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                    Conversation.deleted_at.is_(None),
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def update(
        self,
        conversation_id: uuid.UUID,
        user_id: int,
        title: str | None = None,
        is_pinned: bool | None = None,
        is_favorite: bool | None = None,
    ) -> Conversation | None:
        conversation = await self._get_owned(conversation_id, user_id)
        if conversation is None:
            return None
        if title is not None:
            conversation.title = title
        if is_pinned is not None:
            conversation.is_pinned = is_pinned
        if is_favorite is not None:
            conversation.is_favorite = is_favorite
        await self.session.flush()
        return conversation

    async def soft_delete(self, conversation_id: uuid.UUID, user_id: int) -> bool:
        conversation = await self._get_owned(conversation_id, user_id)
        if conversation is None:
            return False
        conversation.deleted_at = func.now()
        await self.session.flush()
        return True

    # ── Private helpers ───────────────────────────────────────

    async def _get_owned(self, conversation_id: uuid.UUID, user_id: int) -> Conversation | None:
        """Fetch a conversation owned by user_id, excluding soft-deleted."""
        query = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

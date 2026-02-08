from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.orm.message import MessageORM
from app.infrastructure.db.orm.message_source import MessageSourceORM


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user_message(self, *, session_id: UUID, user_role: str, content: str) -> MessageORM:
        msg = MessageORM(
            session_id=session_id,
            user_role=user_role,
            direction="user",
            content=content,
            meta={},
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def create_assistant_message(
        self,
        *,
        session_id: UUID,
        user_role: str,
        content: str,
        sources: list[dict],
        meta: dict | None = None,
    ) -> MessageORM:
        msg = MessageORM(
            session_id=session_id,
            user_role=user_role,
            direction="assistant",
            content=content,
            meta=meta or {},
        )

        for s in sources or []:
            msg.sources.append(
                MessageSourceORM(
                    source_name=str(s.get("source_name") or s.get("source") or "unknown"),
                    snippet=s.get("snippet"),
                    url=s.get("url"),
                    score=float(s.get("score")) if s.get("score") is not None else None,
                )
            )

        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def list_by_session_id(self, session_id: str) -> list[MessageORM]:
        stmt = (
            select(MessageORM)
            .where(MessageORM.session_id == session_id)
            .order_by(MessageORM.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()   
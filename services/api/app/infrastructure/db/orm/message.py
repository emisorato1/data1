from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class MessageORM(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # para agrupar mensajes sin tener Conversation todavía
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    # "public" | "private" | "admin" (por ahora)
    user_role: Mapped[str] = mapped_column(String(32), nullable=False)

    # "user" | "assistant"
    direction: Mapped[str] = mapped_column(String(16), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # opcional: guardar payload crudo que vuelve del rag, útil para debug
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sources: Mapped[list["MessageSourceORM"]] = relationship(
        "MessageSourceORM",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
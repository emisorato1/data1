"""Modelo de base de datos para los recuerdos episodicos."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models.base import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.user import User


class EpisodicMemory(Base):
    """Almacena recuerdos episodicos extraidos de las conversaciones."""

    __tablename__ = "episodic_memories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    memory_type: Mapped[str] = mapped_column(
        Enum(
            "preferencia_usuario",
            "hecho_mencionado",
            "contexto_laboral",
            "instruccion_explicita",
            name="memory_type_enum",
        ),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)  # Gemini embedding size 768
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="episodic_memories")

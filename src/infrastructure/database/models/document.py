"""Modelos de documentos y chunks con embeddings halfvec(768)."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.user import User


class AreaFuncional(enum.StrEnum):
    """Areas funcionales del banco."""

    riesgos = "riesgos"
    corporativo = "corporativo"
    tesoreria = "tesoreria"
    cumplimiento = "cumplimiento"
    operaciones = "operaciones"
    tecnologia = "tecnologia"
    rrhh = "rrhh"
    legal = "legal"
    general = "general"


class DocumentStatus(enum.StrEnum):
    """Estado de procesamiento del documento."""

    pending = "pending"
    indexing = "indexing"
    indexed = "indexed"
    failed = "failed"
    stale = "stale"


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        doc="ID de OpenText (DTREE.DataID)",
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text)
    file_type: Mapped[str | None] = mapped_column(String(50))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    file_hash: Mapped[str | None] = mapped_column(String(64))
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"), nullable=False)
    area: Mapped[AreaFuncional] = mapped_column(
        Enum(AreaFuncional, name="area_funcional", create_constraint=False, native_enum=True),
        server_default="general",
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"))
    classification_level: Mapped[str | None] = mapped_column(String(50), server_default=text("'internal'"))
    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))

    # Relationships
    uploader: Mapped["User | None"] = relationship(foreign_keys=[uploaded_by])
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # EMBEDDING: halfvec(768) - Gemini text-embedding-004 con Matryoshka
    embedding = mapped_column(HALFVEC(768), nullable=True)

    area: Mapped[AreaFuncional] = mapped_column(
        Enum(AreaFuncional, name="area_funcional", create_constraint=False, native_enum=True),
        server_default="general",
    )
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"), nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="chunks")

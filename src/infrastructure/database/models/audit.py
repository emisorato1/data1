"""Modelos de auditoria y eventos de seguridad para compliance bancario."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class SecurityEventType(enum.StrEnum):
    """Tipos de eventos de seguridad del pipeline RAG."""

    prompt_injection = "prompt_injection"
    jailbreak = "jailbreak"
    pii_detected = "pii_detected"
    hallucination = "hallucination"
    topic_out_of_bounds = "topic_out_of_bounds"
    rate_limit = "rate_limit"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    session_id: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[int | None] = mapped_column(BigInteger)
    old_value: Mapped[dict | None] = mapped_column(JSONB)
    new_value: Mapped[dict | None] = mapped_column(JSONB)
    details: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    ip_address = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text)
    request_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), server_default=text("'success'"))
    error_message: Mapped[str | None] = mapped_column(Text)
    hash_chain: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    event_type: Mapped[SecurityEventType] = mapped_column(
        Enum(SecurityEventType, name="security_event_type", create_constraint=False, native_enum=True),
        nullable=False,
    )
    input_text: Mapped[str | None] = mapped_column(Text)
    rule_id: Mapped[str | None] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20), server_default=text("'medium'"))
    details: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    session_id: Mapped[str | None] = mapped_column(String(255))
    ip_address = mapped_column(INET, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    dag_run_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'pending'"))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

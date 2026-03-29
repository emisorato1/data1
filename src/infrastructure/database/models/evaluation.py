"""Modelos para evaluaciones batch de calidad RAG con RAGAS."""

from __future__ import annotations

import uuid  # noqa: TC003 - Required at runtime by SQLAlchemy Mapped[]
from datetime import datetime  # noqa: TC003 - Required at runtime by SQLAlchemy Mapped[]

from sqlalchemy import DateTime, Float, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class RagasEvaluation(Base):
    __tablename__ = "ragas_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    dag_run_id: Mapped[str | None] = mapped_column(String(255))
    dataset_path: Mapped[str] = mapped_column(Text, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    faithfulness: Mapped[float] = mapped_column(Float, nullable=False)
    answer_relevancy: Mapped[float] = mapped_column(Float, nullable=False)
    context_precision: Mapped[float] = mapped_column(Float, nullable=False)
    context_recall: Mapped[float] = mapped_column(Float, nullable=False)
    thresholds: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    below_thresholds: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    sample_results: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

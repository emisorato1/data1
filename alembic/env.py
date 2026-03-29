"""Alembic env.py — configurado para autodiscovery de modelos SQLAlchemy."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

from src.infrastructure.database.models import (  # noqa: E402, F401 — after load_dotenv
    AuditLog,
    Base,
    Conversation,
    Document,
    DocumentChunk,
    DTree,
    DTreeACL,
    DTreeAncestors,
    Kuaf,
    KuafChildren,
    Message,
    PipelineRun,
    RagasEvaluation,
    RefreshToken,
    SecurityEvent,
    User,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_sync_url() -> str:
    """Obtener DATABASE_URL y convertir a driver sync (psycopg) para Alembic."""
    url = os.environ.get(
        "DATABASE_URL",
        config.get_main_option("sqlalchemy.url", ""),
    )
    if not url:
        raise RuntimeError("DATABASE_URL is required for Alembic migrations")
    # Alembic usa driver sync — normalizar cualquier variante a psycopg
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def run_migrations_offline() -> None:
    """Generar SQL sin conectar a la BD."""
    context.configure(
        url=_get_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecutar migraciones contra la BD."""
    connectable = create_engine(_get_sync_url())

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

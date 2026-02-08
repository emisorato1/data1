from __future__ import annotations

import os
import sys
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # services/api
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.infrastructure.db.base import Base  # noqa: E402
import app.infrastructure.db.orm  # noqa: F401,E402
from app.core.config import settings  # noqa: E402

target_metadata = Base.metadata

db_url = settings.DATABASE_URL
if not db_url:
    raise RuntimeError("DATABASE_URL no está definido. Revisá tu .env.")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Configura el contexto y corre migraciones usando una conexión (sync) provista por run_sync()."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode usando AsyncEngine."""
    connectable = create_async_engine(
        db_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Alembic es sync internamente, por eso se usa run_sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
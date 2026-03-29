# T1-S1-04: Configurar Alembic y schema base

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco, Agus) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T2-S2-01 (auth necesita tabla users) |
| Depende de | T1-S1-02, T1-S1-03 |
| Skill | `database-setup/SKILL.md` + `database-setup/references/sql-schema.md` |
| Estimacion | L (4-8h) |

## Contexto

Las migraciones de base de datos son fundamentales para que el equipo trabaje con un schema consistente. Esta spec crea las tablas minimas para que T2 pueda arrancar auth en Sprint 2.

## Spec

Configurar Alembic para manejar migraciones y crear la migracion inicial con las tablas fundamentales del sistema. Los modelos SQLAlchemy deben alinearse con el ERD autorativo en `database-setup/SKILL.md`.

## Acceptance Criteria

- [x] Alembic inicializado con `alembic init`
- [x] `alembic.ini` configurado para leer DATABASE_URL de env
- [x] `alembic/env.py` configurado para autodiscovery de modelos SQLAlchemy
- [x] Migracion inicial con tablas: `users`, `refresh_tokens`, `conversations`, `messages`
- [x] `alembic upgrade head` ejecuta sin errores contra Docker Postgres
- [x] `alembic downgrade -1` revierte correctamente
- [x] Modelos SQLAlchemy correspondientes creados en `src/infrastructure/database/models/`
- [x] `Base` model con `TimestampMixin` (created_at, updated_at)

## Archivos a crear/modificar

- `alembic.ini` (crear)
- `alembic/env.py` (crear)
- `alembic/versions/001_initial_schema.py` (crear)
- `src/infrastructure/database/models/base.py` (crear)
- `src/infrastructure/database/models/user.py` (crear)
- `src/infrastructure/database/session.py` (crear)

## Decisiones de diseno

- Solo tablas fundamentales en esta migracion: users, refresh_tokens, conversations, messages
- Tablas de RAG (documents, chunks, embeddings) van en Sprint 2 (T1-S2-01)
- Async sessions por defecto (asyncpg)

## Out of scope

- Tablas de documentos, chunks, embeddings (spec T1-S2-01)
- Tablas OpenText sinteticas (spec T3-S3-01)
- Seed data (spec T1-S2-01)
- Repositorios (se crean cuando se necesitan en T2-S2-01)

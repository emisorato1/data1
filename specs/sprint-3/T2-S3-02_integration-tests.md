# T2-S3-02: Tests de integracion API (auth + conversations)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Branko) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | T2-S2-01, T2-S2-03 |
| Skill | `testing-strategy/SKILL.md` + `testing-strategy/references/mocking-strategies.md` |
| Estimacion | L (4-8h) |

## Contexto

Suite de tests que valida los endpoints ya implementados. Asegura que el flujo auth + conversations funcione correctamente antes de integrar con frontend.

## Spec

Crear suite de tests de integracion usando TestClient de FastAPI con Docker Postgres, cubriendo auth flow completo, CRUD de conversaciones, y streaming SSE.

## Acceptance Criteria

- [ ] Test suite ejecutable con `pytest tests/integration/`
- [ ] Cobertura: auth flow completo (login -> refresh -> logout)
- [ ] Cobertura: conversations CRUD (crear, listar, detalle, renombrar, borrar)
- [ ] Cobertura: chat SSE (enviar mensaje, recibir stream)
- [ ] Usa TestClient de FastAPI con DB de test (Docker Postgres)
- [ ] Fixtures: usuario autenticado, conversacion con mensajes
- [ ] Coverage > 70% para modulos de API
- [ ] Integrado en CI pipeline

## Archivos a crear/modificar

- `tests/integration/test_auth_flow.py` (crear o expandir)
- `tests/integration/test_conversations_crud.py` (crear)
- `tests/integration/test_chat_sse.py` (crear o expandir)
- `tests/conftest.py` (modificar — fixtures globales)
- `.github/workflows/ci.yml` (modificar — agregar tests)

## Decisiones de diseno

- Docker Postgres en tests (no SQLite): comportamiento identico a produccion, pgvector disponible
- Fixtures con factory pattern: flexible, composable, evita dependencias entre tests
- Coverage 70% como minimo: balance entre cobertura y velocidad de desarrollo

## Out of scope

- Tests E2E con frontend (Sprint 4)
- Tests de performance/carga (post-MVP)
- Tests de seguridad/pentesting (post-MVP)

# T2-S2-03: API de conversaciones

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Ema) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T5-S4-01 (sidebar historial) |
| Depende de | T2-S2-01 |
| Skill | `api-design/SKILL.md` + `api-design/references/cursor-pagination.md` |
| Estimacion | L (4-8h) |

## Contexto

Endpoints CRUD para gestionar conversaciones del usuario. El frontend necesita listar, crear y reactivar conversaciones. Cada conversacion es un thread_id de LangGraph.

## Spec

Implementar endpoints REST para el ciclo de vida completo de conversaciones con cursor-based pagination y aislamiento por usuario.

## Acceptance Criteria

- [x] `POST /api/v1/conversations` - Crear nueva conversacion (retorna thread_id)
- [x] `GET /api/v1/conversations` - Listar conversaciones del usuario con cursor-based pagination
- [x] `GET /api/v1/conversations/{id}` - Detalle con mensajes
- [x] `PATCH /api/v1/conversations/{id}` - Renombrar conversacion
- [x] `DELETE /api/v1/conversations/{id}` - Soft delete
- [x] Solo el owner puede acceder a sus conversaciones (filtro por user_id)
- [x] Response con metadata de paginacion: `next_cursor`, `has_more`
- [x] Tests de integracion con DB real (via Docker)

## Archivos a crear/modificar

- `src/infrastructure/api/v1/chat.py` (crear)
- `src/application/use_cases/rag/conversations.py` (crear)
- `src/application/dtos/rag_dtos.py` (crear)
- `src/infrastructure/database/repositories/conversation_repository.py` (crear)
- `src/domain/repositories/conversation_repository.py` (crear — interface)
- `tests/integration/test_conversations_api.py` (crear)

## Decisiones de diseno

- Cursor-based sobre offset pagination: performance estable con datasets grandes, no salta items
- Soft delete: permite recovery y cumple requisitos de auditoria bancaria
- thread_id = conversation_id: mapeo directo con LangGraph checkpointer

## Out of scope

- Endpoint de chat/streaming (spec T2-S3-01)
- Busqueda de conversaciones por texto (post-MVP)
- Compartir conversaciones entre usuarios (post-MVP)

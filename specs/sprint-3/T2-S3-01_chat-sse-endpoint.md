# T2-S3-01: Endpoint de chat con streaming SSE

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Branko) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T5-S3-02 (Chat UI) |
| Depende de | T4-S2-03 |
| Skill | `api-design/SKILL.md` + `api-design/references/concurrency-patterns.md` |
| Estimacion | L (4-8h) |

## Contexto

El endpoint principal que conecta frontend con el grafo RAG. El streaming SSE permite que los tokens aparezcan incrementalmente en el UI mientras el LLM genera, mejorando drasticamente la UX percibida.

## Spec

Implementar endpoint de chat que recibe una pregunta, la procesa a traves del grafo LangGraph, y retorna la respuesta como stream de Server-Sent Events.

## Acceptance Criteria

- [x] `POST /api/v1/conversations/{id}/messages` - Envia pregunta, retorna stream SSE
- [x] Formato SSE: `event: token\ndata: {"content": "..."}\n\n`
- [x] Evento final: `event: done\ndata: {"sources": [...], "message_id": "..."}\n\n`
- [x] Evento error: `event: error\ndata: {"code": "...", "message": "..."}\n\n`
- [x] Requiere autenticacion (JWT)
- [x] Mensaje guardado en tabla `messages` al completar generacion
- [x] Timeout configurable (default 60s)
- [x] Test de integracion que valida flujo SSE completo

## Archivos a crear/modificar

- `src/infrastructure/api/v1/chat.py` (modificar — agregar endpoint de mensajes)
- `src/application/use_cases/rag/stream_response.py` (crear)
- `tests/integration/test_chat_sse.py` (crear)

## Decisiones de diseno

- SSE sobre WebSockets: mas simple, compatible con HTTP/2, suficiente para chat unidireccional
- Guardar mensaje al completar (no al inicio): si falla generacion, no queda mensaje vacio
- Timeout 60s: consultas RAG complejas pueden tomar tiempo, pero no infinito

## Out of scope

- WebSockets (no necesarios para MVP)
- Rate limiting en chat (spec T2-S4-01)
- Cancel de requests en progreso (post-MVP)

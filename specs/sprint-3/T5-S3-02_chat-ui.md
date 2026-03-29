# T5-S3-02: Chat UI con streaming SSE

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T5-S4-02 (citaciones + polish) |
| Depende de | T5-S3-01, T2-S3-01 |
| Skill | `frontend/SKILL.md` + `frontend/references/chat-components.md` |
| Estimacion | L (4-8h) |

## Contexto

La interfaz principal de chat del sistema. Los tokens deben aparecer incrementalmente mientras el LLM genera, creando una experiencia fluida similar a ChatGPT.

## Spec

Implementar componente de chat con lista de mensajes, input de texto, y streaming SSE que muestre tokens incrementalmente con rendering de Markdown.

## Acceptance Criteria

- [ ] Componente chat: lista de mensajes (user + assistant) con auto-scroll
- [ ] Input de texto + boton enviar (+ Enter para enviar)
- [ ] Streaming: tokens aparecen incrementalmente mientras el LLM genera
- [ ] Indicador de "pensando" mientras espera primera respuesta
- [ ] Markdown rendering en respuestas del assistant
- [ ] Responsive: funcional en desktop y mobile
- [ ] Manejo de errores: muestra mensaje si la API falla

## Archivos a crear/modificar

- `frontend/app/(chat)/page.tsx` (crear)
- `frontend/components/chat/message-list.tsx` (crear)
- `frontend/components/chat/message-input.tsx` (crear)
- `frontend/components/chat/message-bubble.tsx` (crear)
- `frontend/lib/sse-client.ts` (crear — cliente SSE)
- `frontend/lib/api.ts` (crear — API client)

## Decisiones de diseno

- EventSource API nativa + fetch con ReadableStream: mas control que librerias SSE
- Markdown rendering con react-markdown: ligero, extensible con plugins
- Auto-scroll con IntersectionObserver: performance, no scroll en cada token

## Out of scope

- Citaciones clicables (spec T5-S4-02)
- Historial de conversaciones en sidebar (spec T5-S4-01)
- Feedback (thumbs up/down) (post-MVP)
- File upload en chat (post-MVP)

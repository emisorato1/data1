# T5-S4-02: Citaciones + polish UI

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | Demo MVP |
| Depende de | T5-S3-02 |
| Skill | `frontend/references/chat-components.md` |
| Estimacion | L (4-8h) |

## Contexto

Visualizacion de fuentes y polish general para demo. Las citaciones son una feature diferenciadora del sistema: permiten al usuario verificar la informacion en el documento original. El polish general asegura una demo profesional.

## Spec

Implementar citaciones como chips clicables que expanden panel con detalle de la fuente, mas polish general de UI para demo.

## Acceptance Criteria

- [x] Citaciones como chips clicables `[1]`, `[2]` en la respuesta
- [x] Click en citacion -> expande panel con nombre de documento, pagina, extracto
- [x] Boton de logout funcional
- [x] Loading states en todas las interacciones
- [x] Empty states (sin conversaciones, sin mensajes)
- [x] Favicon + titulo de la app

## Archivos a crear/modificar

- `frontend/components/chat/citation-chip.tsx` (crear)
- `frontend/components/chat/source-panel.tsx` (crear)
- `frontend/components/chat/message-bubble.tsx` (modificar — integrar citaciones)
- `frontend/app/layout.tsx` (modificar — favicon, titulo)
- `frontend/public/favicon.ico` (crear)

## Decisiones de diseno

- Citaciones inline como chips: no interrumpen la lectura, clicables para mas detalle
- Panel lateral (no modal): permite ver respuesta y fuente al mismo tiempo
- Loading skeletons: UX profesional, indica progreso

## Out of scope

- Dark mode (post-MVP)
- Widget de feedback (post-MVP)
- Descarga de documentos citados (post-MVP)
- Animaciones avanzadas (post-MVP)

# T5-S4-01: Sidebar de historial de conversaciones

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | T2-S2-03 |
| Skill | `frontend/SKILL.md` > Seccion "Historial" |
| Estimacion | M (2-4h) |

## Contexto

Navegacion entre conversaciones pasadas. Los usuarios necesitan poder volver a consultas anteriores y continuar conversaciones, similar a la experiencia de ChatGPT.

## Spec

Implementar sidebar izquierda con lista de conversaciones del usuario, navegacion entre ellas, y boton de nueva conversacion.

## Acceptance Criteria

- [x] Sidebar izquierda con lista de conversaciones (titulo + fecha)
- [x] Click en conversacion -> carga mensajes anteriores
- [x] Boton "Nueva conversacion"
- [x] Scroll infinito o paginacion si hay muchas conversaciones
- [x] Conversacion activa resaltada visualmente

## Archivos a crear/modificar

- `frontend/components/sidebar/conversation-list.tsx` (crear)
- `frontend/components/sidebar/conversation-item.tsx` (crear)
- `frontend/app/(chat)/layout.tsx` (modificar — integrar sidebar)
- `frontend/lib/api.ts` (modificar — agregar endpoints de conversaciones)

## Decisiones de diseno

- Scroll infinito sobre paginacion: mejor UX para listas de conversaciones
- Titulo auto-generado: primera query como titulo (se puede renombrar despues)
- Sidebar colapsable en mobile: responsive design

## Out of scope

- Busqueda de conversaciones (post-MVP)
- Drag-and-drop para reordenar (post-MVP)
- Carpetas/tags de conversaciones (post-MVP)

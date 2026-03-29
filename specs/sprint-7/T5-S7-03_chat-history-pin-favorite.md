# T5-S7-03: Sistema de Fijación de Chats (Pin) y Favoritos

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Alta |
| Estado | pending |
| Bloqueante para | - |
| Depende de | - |
| Skill | `frontend/SKILL.md` + `chat-memory/SKILL.md` |
| Estimacion | M (4-6h) |

> POST-06

## Contexto

Los usuarios necesitan una forma de mantener conversaciones importantes fácilmente accesibles y clasificar sus chats. Actualmente el historial es puramente cronológico, lo que dificulta recuperar sesiones relevantes antiguas.

## Spec

Implementar dos mecanismos de gestión del historial en el frontend:
1. **Fijar Chats (Pin)**: Permitir mantener chats específicos siempre al principio de la lista en el sidebar.
2. **Favoritos**: Permitir marcar chats como favoritos para filtrarlos fácilmente.

Esto requiere actualizar el modelo de datos de las sesiones en el backend y reflejar los cambios en la UI del sidebar.

## Acceptance Criteria

- [ ] Botón de "Pin" (chincheta) visible en cada ítem del historial en el sidebar.
- [ ] Botón de "Favorito" (estrella) visible en la cabecera del chat activo y en el ítem del historial.
- [ ] Los chats fijados aparecen en una sección separada "Fijados" en la parte superior del sidebar.
- [ ] El resto de los chats mantiene su orden cronológico debajo de la sección de fijados.
- [ ] Añadir control en el sidebar (ej. Toggle o Tabs) para alternar entre "Todos" y "Favoritos".
- [ ] Al seleccionar "Favoritos", el sidebar solo muestra los chats marcados con estrella (respetando si están fijados o no).
- [ ] El estado de fijación y favorito debe persistir en el backend (requiere actualización del esquema de la BD).
- [ ] Sincronización en tiempo real del estado de favorito entre la cabecera del chat y el sidebar.

## Archivos a crear/modificar

- `frontend/src/components/chat/Sidebar.tsx` (modificar)
- `frontend/src/components/chat/HistoryItem.tsx` (modificar)
- `frontend/src/components/chat/ChatHeader.tsx` (modificar)
- `backend/app/models/session.py` (modificar: añadir campos `is_pinned`, `is_favorite`)
- `backend/app/schemas/session.py` (modificar)
- `backend/app/api/endpoints/sessions.py` (modificar: endpoints para toggle pin/favorite y filtro)

## Decisiones de diseno

- **Sección Separada para Pines**: Evita confusión visual si solo se cambiara el ordenamiento.
- **Doble presencia del botón Favorito**: Ponerlo en la cabecera del chat facilita marcarlo mientras se lee, ponerlo en el sidebar facilita la gestión en lote.
- **Backend Persistencia**: Esencial para que las preferencias se mantengan entre sesiones y dispositivos.

## Out of scope

- Carpetas personalizadas para agrupar chats.
- Ordenamiento manual (drag and drop) de los chats fijados.

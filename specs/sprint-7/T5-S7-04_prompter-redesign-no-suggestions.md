# T5-S7-04: Rediseño Estructural del Prompter y Eliminación de Sugerencias

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | - |
| Skill | `frontend/SKILL.md` |
| Estimacion | M (4h) |

> POST-06

## Contexto

El diseño actual del área de entrada de texto (prompter) carece de protagonismo cuando se inicia un chat nuevo, haciéndolo parecer un elemento secundario (footer). Además, las tarjetas de consultas sugeridas están desactualizadas y distraen.

## Spec

Se requiere una refactorización del componente del prompter para darle mayor presencia en la pantalla de inicio del chat, así como la eliminación del componente de sugerencias de consultas iniciales.

## Acceptance Criteria

- [x] Eliminar el componente de `SuggestedQueries` renderizado en el `EmptyState` del chat.
- [x] En un nuevo chat vacío, el prompter debe estar centrado (vertical y horizontalmente) en el área principal de contenido.
- [x] El `min-height` del prompter debe aumentar a 110px. aproximadamente, y su padding/tipografía ajustarse para mayor legibilidad y sensación de amplitud.
- [x] El botón de enviar tiene que estar dentro del prompter abajo a la derecha con un tamaño de 36x36px.
- [x] Al enviarse el primer mensaje (y poblarse el historial), el prompter debe transicionar hacia su posición original en el footer.
- [x] El parrafo "Las respuestas se generan a partir de la base documental interna del banco." debe estar centrado debajo del prompter con tamaño 31px de alto.
- [x] La pantalla de inicio de un chat nuevo solo debe mostrar el prompter centralizado.
- [x] Implementar animaciones suaves (CSS transitions/framer-motion) para el desplazamiento del prompter del centro al footer.
- [x] Mantener la responsividad del diseño centrado en dispositivos móviles (evitar superposiciones con el teclado virtual).

## Archivos a crear/modificar

- `frontend/src/app/chat/page.tsx` (modificar)
- `frontend/src/components/chat/ChatInput.tsx` (modificar)
- `frontend/src/components/chat/EmptyState.tsx` (modificar)
- `frontend/src/components/chat/SuggestedQueries.tsx` (eliminar)
- `frontend/src/styles/components/chat-input.css` o equivalente de Tailwind (modificar)

## Decisiones de diseno

- **Centrado Inicial**: Da foco total a la acción principal del usuario (hacer la pregunta).
- **Eliminación de Sugerencias**: Simplifica la interfaz inicial y reduce la carga cognitiva, permitiendo al prompter centrado destacar sin distracciones.
- **Transición Suave**: Evita saltos bruscos en el layout que pueden desorientar al usuario.

## Out of scope

- Rediseño general del chat de historial.
- Cambio en el motor de renderizado de Markdown/respuestas del LLM.

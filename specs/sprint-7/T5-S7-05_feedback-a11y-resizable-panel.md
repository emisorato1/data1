# T5-S7-05: Accesibilidad Feedback (Like/Dislike) y Panel Lateral Ajustable

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | - |
| Depende de | - |
| Skill | `frontend/SKILL.md` + `observability/SKILL.md` |
| Estimacion | M (6h) |

> POST-06

## Contexto

El sistema de feedback actual de respuestas (Like/Dislike) es poco accesible, requiriendo un "hover" para aparecer y con un área interactiva muy pequeña. Además, el panel lateral de fuentes no es personalizable, lo que dificulta leer documentos extensos.

## Spec

Se requiere realizar ajustes de accesibilidad y usabilidad (UX) enfocados en el panel de lectura de documentos (fuentes) y las interacciones de feedback en los mensajes del bot.

## Acceptance Criteria

- [x] Aumentar el tamaño base (padding/dimensiones) de los botones Like/Dislike para un mejor alcance táctil y accesibilidad (min 44x44px).
- [x] Renderizar permanentemente los botones Like/Dislike junto a cada respuesta del sistema, eliminando la dependencia del `:hover`.
- [x] Asegurar que el layout del `MessageBubble` se adapte correctamente a estos botones más grandes y siempre visibles (ajuste de márgenes/paddings).
- [x] Implementar la funcionalidad "resizable" (redimensionable) en el panel lateral de fuentes.
- [x] El usuario debe poder arrastrar el divisor (`gutter`) entre el chat y el panel de fuentes para modificar el ancho del panel.
- [x] Establecer límites lógicos: ancho mínimo (ej. 250px) y ancho máximo (ej. 70% del viewport) para el panel de fuentes.
- [x] Persistir el ancho preferido del usuario en `localStorage` o cookies para futuras sesiones.
- [x] Verificar que la telemetría de feedback en Langfuse siga registrando correctamente las interacciones con los nuevos botones.

## Archivos a crear/modificar

- `frontend/src/components/chat/MessageActions.tsx` (modificar)
- `frontend/src/components/chat/MessageBubble.tsx` (modificar)
- `frontend/src/components/chat/SourcesPanel.tsx` (modificar)
- `frontend/src/layouts/ChatLayout.tsx` (modificar: introducir layout dividido si no existe, o añadir `react-resizable-panels`)
- `frontend/src/hooks/useResizablePanel.ts` (crear o integrar en el layout)

## Decisiones de diseno

- **Botones Visibles Permanentes**: Aumenta significativamente la tasa de feedback (crítico para RAGAS y mejora continua del LLM).
- **Panel Resizable (Persistente)**: Respeta la preferencia del usuario si tiene un monitor panorámico o prefiere leer el PDF en grande.
- **Límites de Ancho**: Previene layouts "rotos" (ej. un panel de fuentes de 10px de ancho).

## Out of scope

- Rediseño de los iconos de Like/Dislike (se mantienen los actuales, solo cambian tamaño/visibilidad).
- Pop-over de feedback textual obligatorio al dar "Dislike" (eso iría en otra spec).
- "Snap" automático del panel a posiciones predefinidas.

## Registro de implementación

| Campo | Detalle |
|-------|---------|
| Fecha | 2026-03-19 |
| Branch | `56-t5-s7-05_feedback-a11y-resizable-panel` |
| Tests | 42 passed, 0 failed |
| Lint | ESLint 0 errors, TypeScript 0 errors |

### Archivos modificados (reales vs spec)

| Spec planteaba | Archivo real | Acción |
|---------------|-------------|--------|
| `MessageActions.tsx` | `FeedbackWidget.tsx` | Modificado — botones 44x44px, iconos w-5 h-5, aria-labels en español |
| `MessageBubble.tsx` | `message-bubble.tsx` | Modificado — feedback siempre visible, copy solo en hover |
| `SourcesPanel.tsx` | `source-panel.tsx` | Modificado — width dinámica, gutter resize con role="separator" |
| `ChatLayout.tsx` | `app/(chat)/chat/page.tsx` | Modificado — integración useResizablePanel |
| `useResizablePanel.ts` | `hooks/useResizablePanel.ts` | **Creado** — hook custom (mouse/touch drag, min 250px, max 70%vw, localStorage) |

### Infraestructura de testing (nueva)

- `vitest.config.ts` — configuración con jsdom + @vitejs/plugin-react
- `vitest.setup.ts` — setup con jest-dom matchers
- `package.json` — agregadas devDependencies: vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom, @vitejs/plugin-react

### Decisión técnica

Se optó por hook custom `useResizablePanel` en lugar de instalar `react-resizable-panels` para evitar nueva dependencia. El caso de uso (un solo divisor horizontal con min/max y persistencia) no justifica la librería.

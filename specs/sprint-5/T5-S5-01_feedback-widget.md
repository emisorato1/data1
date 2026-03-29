# T5-S5-01: Widget feedback thumbs up/down por respuesta

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | - |
| Depende de | T5-S4-02 (done), T1-S2-03 (done) |
| Skill | `frontend/SKILL.md` |
| Estimacion | M (2-4h) |

## Contexto

User feedback is essential for RAG quality improvement. Each response needs a simple mechanism for users to rate quality, which feeds into RAGAS evaluation and model tuning.

## Spec

Add thumbs up/down feedback buttons to each chat response in the frontend, with an optional text feedback field, connected to a backend API endpoint.

## Acceptance Criteria

- [x] Iconos thumbs up/down visibles en cada respuesta del asistente
- [x] Click en thumbs envia feedback al backend via `POST /api/v1/feedback`
- [x] Campo de texto opcional que aparece tras dar feedback negativo
- [x] Visual feedback: icono seleccionado cambia de color/estilo
- [x] Un solo feedback por respuesta (toggle, no acumulativo)
- [x] Backend endpoint `POST /api/v1/feedback` con campos: message_id, rating (positive/negative), comment
- [x] Tabla `feedback` creada via Alembic migration
- [x] Feedback enviado a Langfuse como score del trace correspondiente
- [x] Tests del componente React y del endpoint

## Archivos a crear/modificar

- `frontend/src/components/chat/FeedbackWidget.tsx` (crear)
- `src/api/routes/feedback.py` (crear)
- `src/api/schemas/feedback.py` (crear)
- `src/domain/models/feedback.py` (crear)
- `alembic/versions/xxx_add_feedback_table.py` (crear)
- `tests/unit/test_feedback_endpoint.py` (crear)

## Decisiones de diseno

- **Thumbs up/down sobre rating numerico**: Mas simple, mayor tasa de respuesta de usuarios.
- **Texto opcional solo en negativo**: Reduce friccion. Solo se pide detalle cuando hay problema.
- **Langfuse integration**: Permite correlacionar feedback con trazas RAG para debugging.

## Out of scope

- Dashboard de feedback agregado (spec T5-S8-01)
- Alertas automaticas por feedback negativo recurrente
- A/B testing de respuestas

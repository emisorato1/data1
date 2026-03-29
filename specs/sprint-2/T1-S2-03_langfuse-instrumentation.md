# T1-S2-03: Langfuse instrumentacion para el equipo

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Agus) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - (mejora observabilidad para todos) |
| Depende de | T1-S1-06 |
| Skill | `observability/SKILL.md` + `observability/references/logging-config.md` |
| Estimacion | M (2-4h) |

## Contexto

Con Langfuse ya desplegado (T1-S1-06), ahora hay que instrumentar el codigo de la aplicacion. Todo el equipo necesita poder trazar sus componentes para debuggear el pipeline RAG.

## Spec

Configurar Langfuse client en la app, structlog como logger por defecto, y callbacks para trazar automaticamente LangChain/LangGraph. Producir un documento interno de "como instrumentar tu codigo".

## Acceptance Criteria

- [x] Langfuse client inicializado en app startup (FastAPI lifespan)
- [x] Decorator `@observe` disponible para instrumentar funciones
- [x] structlog configurado como logger por defecto:
  - [x] JSON en produccion
  - [x] Coloreado en desarrollo
- [x] Contexto automatico en logs: `request_id`, `user_id`, `trace_id`
- [x] Middleware FastAPI que inyecta `request_id` en cada request
- [x] Callback de Langfuse para LangChain/LangGraph configurado (traza automatica de LLM calls)
- [x] Documentacion interna: "como instrumentar tu codigo" (1 pager para el equipo)

## Archivos a crear/modificar

- `src/infrastructure/observability/langfuse_client.py` (crear)
- `src/infrastructure/observability/metrics.py` (crear — base)
- `src/infrastructure/api/middleware/logging.py` (crear)
- `src/config/settings.py` (modificar — agregar config Langfuse)

## Decisiones de diseno

- structlog sobre logging estandar: JSON estructurado, contexto automatico, compatible con Cloud Logging
- Langfuse callback handler: traza automatica sin instrumentar cada LLM call manualmente
- request_id como UUID por request: correlaciona logs con trazas de Langfuse

## Out of scope

- Metricas Prometheus (spec T1-S3-03)
- Dashboard custom en Langfuse
- Cost tracking por query (se agrega cuando el pipeline este completo)
- RAGAS evaluation (post-MVP)

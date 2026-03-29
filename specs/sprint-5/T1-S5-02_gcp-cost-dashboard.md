# T1-S5-02: Dashboard costos Vertex AI en GCP Monitoring

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Agus) |
| Prioridad | Media |
| Estado | pending |
| Bloqueante para | - |
| Depende de | INFRA-S5-02 |
| Skill | `observability/SKILL.md` |
| Estimacion | M (2-4h) |

## Contexto

Vertex AI costs (Gemini API calls for embeddings and generation) can grow rapidly. The team needs visibility into API usage costs to optimize and budget correctly.

## Spec

Configure GCP Monitoring dashboards and alerts for Vertex AI usage, including token consumption, request counts, latency, and estimated costs.

## Acceptance Criteria

- [ ] Dashboard GCP Monitoring "Vertex AI Costs" con metricas:
  - Requests por modelo (embedding vs generation)
  - Tokens consumidos (input + output) por hora/dia
  - Latencia p50, p95, p99 por tipo de request
  - Costo estimado basado en pricing de Vertex AI
- [ ] Alerta si costo diario excede threshold configurable
- [ ] Alerta si latencia p95 excede 10 segundos
- [ ] Dashboard configurado via Terraform (spec INFRA-S5-02) o JSON export
- [ ] Documentacion de como acceder y leer el dashboard

## Archivos a crear/modificar

- `docs/monitoring/vertex-ai-dashboard.md` (crear)
- Configuracion en INFRA-S5-02 (itmind-infrastructure)

## Decisiones de diseno

- **GCP Monitoring nativo sobre Grafana**: Ya esta desplegado (T1-S3-03), no requiere infra adicional.
- **Metricas de Vertex AI son nativas**: `aiplatform.googleapis.com/prediction/*` disponibles sin instrumentacion custom.
- **Costo estimado calculado**: GCP no provee costo directo en metricas, se calcula con formula basada en tokens x precio por modelo.

## Out of scope

- Provisioning de dashboards Terraform (spec INFRA-S5-02)
- Optimizacion de costos (requiere data historica)
- Dashboard de Langfuse (ya desplegado)

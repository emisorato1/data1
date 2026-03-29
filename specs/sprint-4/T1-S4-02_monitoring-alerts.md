# T1-S4-02: Monitoring y alertas en Google Cloud

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Agus) |
| Prioridad | Media |
| Estado | pending |
| Bloqueante para | - |
| Depende de | T1-S3-03 |
| Skill | `observability/references/sli-slo-management.md` |
| Estimacion | L (4-8h) |

## Contexto

Visibilidad basica del sistema en staging/produccion usando Google Cloud Operations. Sin dashboards y alertas, no hay forma de saber si el sistema esta degradado antes de que los usuarios lo reporten.

## Spec

Crear dashboards en Cloud Monitoring y configurar alerting policies para metricas criticas del sistema y de Airflow.

## Acceptance Criteria

- [ ] Dashboard en Cloud Monitoring con: latencia p50/p95, requests/sec, error rate, DB connections
- [ ] Dashboard de Airflow DAGs: success rate, duracion promedio, DAGs fallidos (via Airflow metrics o logs)
- [ ] Alerting policy: error rate > 5% durante 5 minutos -> notificacion
- [ ] Alerting policy: latencia p95 > 10s durante 5 minutos -> notificacion
- [ ] Logs accesibles via Cloud Logging (filtro por service, severity, trace_id)

## Archivos a crear/modificar

- `infra/monitoring/dashboards/` (crear — JSON exports de dashboards)
- `infra/monitoring/alerts/` (crear — alerting policies)

## Decisiones de diseno

- Dashboards como codigo (JSON): versionados, reproducibles entre entornos
- Alertas conservadoras (5min window): evita false positives por spikes temporales
- Cloud Logging sin agente extra: GKE envia logs automaticamente

## Out of scope

- SLOs formales (post-MVP)
- Alertas via PagerDuty/OpsGenie (post-MVP, notificacion por email suficiente)
- Dashboard de costos (post-MVP)

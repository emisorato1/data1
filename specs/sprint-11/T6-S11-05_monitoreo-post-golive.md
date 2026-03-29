# IA-33: Monitoreo activo y resolucion incidencias

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, Agus, team) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-PS-01 |
| Depende de | T6-S11-04 |
| Skill | `observability/SKILL.md` |
| Estimacion | XL (8+h) |

## Contexto

Post go-live, the team provides active monitoring and incident resolution for the first week. This ensures any production issues are caught and resolved quickly.

## Spec

Execute active monitoring of the production system, responding to incidents, tracking system health metrics, and ensuring stability during the first week of operation.

## Acceptance Criteria

- [ ] Monitoreo 24/7 primera semana (rotacion de equipo)
- [ ] Dashboard produccion monitoreado continuamente
- [ ] Incidencias resueltas en SLA: critico < 1h, alto < 4h, medio < 24h
- [ ] Metricas de calidad RAG monitoreadas: faithfulness, latencia, error rate
- [ ] Feedback de usuarios recopilado y categorizado
- [ ] Reporte diario de status produccion
- [ ] Escalation path documentado y comunicado
- [ ] Al menos 5 dias sin incidencias criticas antes de reducir monitoreo

## Archivos a crear/modificar

- `docs/operations/monitoring-report-week1.md` (crear)
- `docs/operations/incident-log.md` (crear)

## Decisiones de diseno

- **Rotacion de equipo**: No una persona 24/7.
- **SLA definidos**: Expectativas claras de respuesta.
- **5 dias estabilidad**: Criteria para reducir monitoreo.

## Out of scope

- SLA contractuales, on-call permanente, NOC setup

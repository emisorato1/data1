# T1-S9-01: Load testing con K6/Locust

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Agus) |
| Prioridad | Alta |
| Estado | pending |
| Bloqueante para | T6-S10-04 |
| Depende de | T1-S4-01 (done) |
| Skill | `testing-strategy/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

The system must handle concurrent users in production. Load testing validates performance under expected and peak loads, identifying bottlenecks.

## Spec

Implement and execute load tests using K6 or Locust, targeting key API endpoints with realistic usage patterns.

## Acceptance Criteria

- [ ] Scripts load testing para endpoints: chat, documents, auth
- [ ] Escenarios: normal (20 users), peak (50 users), stress (100 users)
- [ ] Metricas: latency p50/p95/p99, throughput, error rate
- [ ] Target: p95 < 5s chat, p95 < 1s REST, error rate < 1%
- [ ] Identificacion bottlenecks con profiling
- [ ] Reporte load testing con graficas y recomendaciones
- [ ] Optimizaciones si targets no se cumplen
- [ ] Re-test post-optimizacion

## Archivos a crear/modificar

- `tests/load/k6_chat_test.js` (crear) o `tests/load/locustfile.py`
- `tests/load/scenarios/` (crear)
- `docs/testing/load-test-report.md` (crear)

## Decisiones de diseno

- **K6 preferido**: Menor overhead, scripteable JS, mejor SSE testing.
- **Realistic scenarios**: 80% queries, 15% doc ops, 5% admin.
- **Testing en QAS**: No DEV ni PRD.

## Out of scope

- Chaos engineering
- Global load testing
- Automated perf regression CI

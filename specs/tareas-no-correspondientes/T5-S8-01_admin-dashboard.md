# T5-S8-01: Admin dashboard (metricas RAG, gestion docs, logs)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Alta |
| Estado | pending |
| Bloqueante para | - |
| Depende de | T5-S7-01, T1-S5-02 |
| Skill | `frontend/SKILL.md` + `frontend/references/admin-dashboard.md` |
| Estimacion | XL (8+h) — POST-20 |

## Contexto

Admins need visibility into system health: RAG quality metrics, document indexing overview, query volumes, feedback aggregates, and audit logs.

## Spec

Build admin dashboard page in Next.js with sections for RAG metrics, document overview, user activity, and system health.

## Acceptance Criteria

- [ ] Nueva pagina `/admin` accesible solo con rol admin
- [ ] Seccion "RAG Quality": metricas RAGAS recientes (faithfulness, relevancy, precision)
- [ ] Seccion "Documents": conteo por status, documentos recientes, top errores
- [ ] Seccion "Activity": queries por hora/dia, usuarios activos, feedback ratio
- [ ] Seccion "System": latencia promedio, uptime, version desplegada
- [ ] Graficos con recharts o chart.js
- [ ] Filtro por rango de fechas
- [ ] Auto-refresh cada 60 segundos
- [ ] Responsive design
- [ ] API endpoints admin para metricas agregadas

## Archivos a crear/modificar

- `frontend/src/app/admin/page.tsx` (crear)
- `frontend/src/components/admin/RagMetricsCard.tsx` (crear)
- `frontend/src/components/admin/DocumentsOverview.tsx` (crear)
- `frontend/src/components/admin/ActivityChart.tsx` (crear)
- `frontend/src/components/admin/SystemHealth.tsx` (crear)
- `src/api/routes/admin.py` (modificar)
- `src/application/services/metrics_service.py` (crear)

## Decisiones de diseno

- **Dashboard in-app sobre Grafana**: Admin necesita contexto de la app.
- **Recharts**: Lightweight, React-native.
- **API dedicados**: Datos se agregan en backend.

## Out of scope

- Real-time WebSocket updates
- Alerting desde dashboard
- Export CSV/PDF

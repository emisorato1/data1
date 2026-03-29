# T5-S8-02: Vista estado pipelines Airflow (docs en indexacion)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Media |
| Estado | pending |
| Bloqueante para | - |
| Depende de | T5-S7-01 |
| Skill | `frontend/SKILL.md` |
| Estimacion | M (2-4h) — POST-23 |

## Contexto

When documents are being indexed, users want to know the progress: which step is the pipeline on, how long has it been running, any errors.

## Spec

Add pipeline status visualization to the document management page, showing Airflow DAG run status for documents in indexing.

## Acceptance Criteria

- [ ] Status detallado visible en pagina de documentos para docs en `indexing`
- [ ] Steps visualizados: validate -> chunk -> embed -> store (con estado de cada uno)
- [ ] Indicador de progreso (step actual highlighted)
- [ ] Tiempo transcurrido desde inicio de indexacion
- [ ] Si hay error: muestra en cual step fallo con mensaje descriptivo
- [ ] Polling cada 10 segundos mientras hay docs en indexing
- [ ] Backend endpoint que consulta Airflow REST API para status del DAG run

## Archivos a crear/modificar

- `frontend/src/components/documents/PipelineStatusView.tsx` (crear)
- `src/api/routes/documents.py` (modificar)
- `src/infrastructure/airflow/dag_status_service.py` (crear)

## Decisiones de diseno

- **Consulta Airflow REST API**: Fuente de verdad para estado real.
- **Polling 10s**: Indexacion tarda minutos.
- **Visual steps**: Mas informativo que spinner generico.

## Out of scope

- Cancelacion de pipeline desde UI
- Logs de Airflow (accesibles via Airflow UI)

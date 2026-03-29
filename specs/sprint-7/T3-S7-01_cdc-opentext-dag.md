# T3-S7-01: CDC OpenText DAG (polling + event-driven ready)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-S10-03 |
| Depende de | T3-S6-02 |
| Skill | `security-mirror/SKILL.md` + `rag-indexing/SKILL.md` |
| Estimacion | XL (8+h) |

> POST-09/25 (fusionados: mismo CDC DAG)

## Contexto

Documents and permissions in OpenText change over time. The platform needs to stay synchronized. This DAG implements Change Data Capture: detecting new/modified/deleted documents in OpenText and updating the local index and permissions accordingly. POST-09 (sync permissions) and POST-25 (CDC DAG) are merged as they describe the same pipeline.

## Spec

Create Airflow DAG `cdc_opentext` that synchronizes documents and permissions from OpenText Content Server, supporting both polling mode (initial) and event-driven mode (Pub/Sub, future).

## Acceptance Criteria

- [ ] DAG `cdc_opentext` en `dags/sync/cdc_opentext.py`
- [ ] Tasks: `detect_changes` -> `sync_documents` -> `sync_permissions` -> `trigger_reindex` -> `update_sync_status`
- [ ] Modo polling: compara timestamps OpenText vs local para detectar cambios
- [ ] Tabla `sync_status` con ultimo sync exitoso por tipo (documents, permissions)
- [ ] Documentos nuevos: descarga a GCS + trigger DAG rag_indexing
- [ ] Documentos modificados: marca chunks como stale + trigger re-indexacion
- [ ] Documentos eliminados: soft delete local + cleanup chunks/embeddings
- [ ] Permisos: actualiza tablas `opentext_permissions` y `opentext_group_members`
- [ ] Invalidacion de cache Redis de permisos tras sync
- [ ] Configurable: schedule (default: cada 6 horas), batch size, parallelism
- [ ] Abstraccion para modo event-driven futuro (interface que polling implementa)
- [ ] Tests con datos sinteticos que simulan cambios en OpenText

## Archivos a crear/modificar

- `dags/sync/cdc_opentext.py` (crear)
- `dags/sync/__init__.py` (crear)
- `src/infrastructure/opentext/change_detector.py` (crear)
- `src/infrastructure/opentext/sync_service.py` (crear)
- `alembic/versions/xxx_add_sync_status_table.py` (crear)
- `tests/unit/test_cdc_opentext.py` (crear)

## Decisiones de diseno

- **Polling first, event-driven ready**: OpenText event webhooks dependen de Pub/Sub (INFRA-S7-01), polling funciona sin dependencia
- **POST-09 y POST-25 fusionados**: Ambos describen el mismo pipeline de sincronizacion, no tiene sentido separarlos
- **Batch processing**: Procesa cambios en batches para eficiencia, no uno a uno
- **Interface abstracta**: `ChangeDetector` protocol permite swappear polling por event-driven sin cambiar el DAG

## Out of scope

- Pub/Sub subscription real (infraestructura en INFRA-S7-01, integracion en fase posterior)
- Sincronizacion en real-time (polling cada 6h es suficiente para fase inicial)
- Manejo de conflictos complejos (last-write-wins)

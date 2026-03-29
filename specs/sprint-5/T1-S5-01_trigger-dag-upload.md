# T1-S5-01: Trigger Airflow DAG rag_indexing desde upload

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco) |
| Prioridad | Alta |
| Estado | pending |
| Bloqueante para | T5-S7-01 |
| Depende de | T2-S5-02, T1-S2-02 (done) |
| Skill | `rag-indexing/SKILL.md` |
| Estimacion | M (2-4h) |

## Contexto

The existing Airflow DAG `rag_indexing` runs manually or via API. After document upload and storage, the system must automatically trigger the indexing pipeline to process the new document.

## Spec

Implement Airflow REST API trigger from the document upload service that kicks off `rag_indexing` DAG with the document_id as configuration parameter.

## Acceptance Criteria

- [ ] Servicio `AirflowTriggerService` que invoca Airflow REST API
- [ ] Trigger del DAG `rag_indexing` con conf `{"document_id": "xxx"}`
- [ ] Update de `documents.status` a `indexing` tras trigger exitoso
- [ ] Manejo de errores: si Airflow no responde, status queda en `pending` para retry
- [ ] Configuracion de Airflow API URL y auth via environment variables
- [ ] Retry con backoff exponencial (max 3 intentos)
- [ ] Tests unitarios con mock de Airflow API

## Archivos a crear/modificar

- `src/infrastructure/airflow/trigger_service.py` (crear)
- `src/infrastructure/airflow/__init__.py` (crear)
- `tests/unit/test_airflow_trigger.py` (crear)

## Decisiones de diseno

- **REST API sobre CLI**: Mas limpio, no requiere acceso directo al scheduler, compatible con Airflow en K8s.
- **Async fire-and-forget**: El upload response no espera a que termine la indexacion, solo confirma el trigger.
- **Status tracking**: El DAG actualiza `documents.status` a `indexed` o `failed` al terminar (logica ya en DAG existente).

## Out of scope

- Modificaciones al DAG rag_indexing (ya funciona, solo se trigerea)
- Webhook de callback (el DAG ya actualiza status directamente)

# T3-S7-02: DAG re-indexacion batch cron semanal/diario

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | - |
| Depende de | T3-S2-03 (done) |
| Skill | `rag-indexing/SKILL.md` |
| Estimacion | M (2-4h) |

> POST-24

## Contexto

Over time, embedding models or chunking strategies may be updated. A batch re-indexing DAG allows re-processing all documents (or a subset) to refresh the vector store with updated embeddings or improved chunks.

## Spec

Create Airflow DAG `rag_reindexing_batch` that re-processes documents on a configurable schedule, supporting full and incremental re-indexing modes.

## Acceptance Criteria

- [x] DAG `rag_reindexing_batch` en `dags/indexing/rag_reindexing.py`
- [x] Schedule configurable via Airflow Variable (default: `@weekly`)
- [x] Modo full: re-indexa todos los documentos con status `indexed`
- [x] Modo incremental: re-indexa solo documentos marcados como `stale` (por CDC u otros)
- [x] Tasks: `select_documents` -> `batch_reindex` -> `update_status` -> `cleanup_old_chunks`
- [x] Batch processing: procesa N documentos en paralelo (configurable, default: 10)
- [x] Cleanup: elimina chunks antiguos despues de re-indexar exitosamente
- [x] No interrumpe queries en curso (re-indexa en paralelo, swap atomico)
- [x] Tests de estructura del DAG y logica de seleccion

## Archivos a crear/modificar

- `dags/indexing/rag_reindexing.py` (crear)
- `tests/unit/test_dag_reindexing.py` (crear)

## Decisiones de diseno

- **Swap atomico**: Nuevos chunks se crean con version incrementada, viejo version se elimina tras verificacion
- **Incremental como default**: Full re-indexing es costoso, incremental cubre el 90% de los casos
- **Reutiliza IndexingService**: El pipeline de indexacion es el mismo, solo cambia la seleccion de documentos

## Out of scope

- Re-indexing con modelo de embedding diferente (cambio de modelo requiere decision de equipo)
- A/B testing de embeddings
- Re-indexing automatico por cambio de configuracion

## Registro de implementacion

**Fecha:** 2026-03-25
**Implementado por:** Claude Opus 4.6

### Archivos creados
- `dags/indexing/rag_reindexing.py` — DAG `rag_reindexing_batch` con 4 tasks
- `tests/unit/test_dag_reindexing.py` — 22 tests (estructura, tasks, config, seleccion, cleanup, update_status)
- `alembic/versions/a1b2c3d4e5f6_add_stale_status_and_chunk_version.py` — Migracion: columna `version` en `document_chunks` + indice compuesto

### Archivos modificados
- `src/infrastructure/database/models/document.py` — Agregado `stale` a `DocumentStatus` enum + columna `version` a `DocumentChunk`

### Decisiones de implementacion
- **Swap atomico via version column**: Chunks nuevos se insertan con `version = current_max + 1`, chunks viejos se eliminan en `cleanup_old_chunks` solo tras exito. Queries en curso no se ven afectadas porque leen ambas versiones temporalmente.
- **Batch size via Airflow Variable**: `reindex_batch_size` (default 10), leido en runtime por `select_documents`.
- **Schedule via Airflow Variable**: `reindex_schedule` (default `@weekly`), leido en parse time con fallback.
- **Reutiliza componentes**: `LoaderFactory`, `AdaptiveChunker`, `GeminiEmbeddingService` — mismos que `rag_indexing`.
- **Patron de tests**: Sigue el mismo patron que `test_dag_indexing.py` con `pytest.importorskip` para ambientes sin Airflow.

### Calidad
- ruff check: 0 errores
- ruff format: OK
- mypy: 0 errores
- pytest: 653 passed, 30 skipped (2 fallos pre-existentes no relacionados)

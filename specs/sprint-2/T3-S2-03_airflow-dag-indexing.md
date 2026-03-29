# T3-S2-03: Airflow DAG de indexacion

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T3-S4-01 (dataset demo) |
| Depende de | T1-S2-02, T3-S2-02 |
| Skill | `rag-indexing/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

DAG de Airflow que orquesta el pipeline de indexacion completo. Es el mecanismo principal para cargar documentos en el sistema. Los operadores pueden ejecutarlo manualmente desde la UI de Airflow, y en el futuro la API lo dispara automaticamente.

## Spec

Crear DAG `rag_indexing` en Airflow que ejecute el pipeline completo usando `IndexingService` como libreria, con manejo de errores, retry automatico y trazabilidad.

## Acceptance Criteria

- [x] DAG `rag_indexing` en `dags/indexing/` con tasks:
  - `validate_file` -> `load_and_chunk` -> `generate_embeddings` -> `store_in_pgvector` -> `update_status`
- [x] Ejecutable manualmente desde Airflow UI (para carga de documentos por operadores)
- [x] Triggerable via Airflow REST API con `document_id` o `file_path` como conf
- [x] Cada task usa los componentes de la libreria directamente (no duplica logica)
- [x] Manejo de errores: si un task falla, el document status se marca como `failed`
- [x] Retry automatico configurable por task (default: 2 retries con backoff exponencial)
- [ ] Trazabilidad: cada task emite logs a Langfuse (pendiente: requiere Langfuse SDK sync adapter)
- [x] DAG visible y ejecutable desde Airflow UI
- [x] Test del DAG con DagBag parsing + estructura (16 tests)

## Archivos a crear/modificar

- `dags/indexing/rag_indexing.py` (crear)
- `dags/indexing/__init__.py` (crear)
- `tests/unit/test_dag_indexing.py` (crear)

## Decisiones de diseno

- Tasks como wrappers de componentes individuales (LoaderFactory, AdaptiveChunker, GeminiEmbeddingService, PgVectorStore): logica centralizada, DAG solo orquesta
- TaskFlow API de Airflow 3: decoradores @task, mas Pythonic que operators clasicos
- Retry por task (no por DAG): granularidad fina, no re-ejecuta pasos exitosos
- **Sync psycopg para DB** en lugar de AsyncSession: Airflow 3 usa SQLAlchemy 1.4.x internamente y no es compatible con SA 2.x AsyncSession. Los tasks usan `psycopg.connect()` directo para operaciones de DB (pipeline_runs, document_chunks, documents)
- **asyncio.run() para embeddings**: El Gemini SDK (`google-genai`) es async-native, asi que el task `generate_embeddings` usa `asyncio.run()` como bridge
- **XCom para datos entre tasks**: Los chunks serializados (text + metadata + token_count) y embeddings se pasan via XCom. Para documentos grandes (>500 chunks) podria necesitarse XCom con backend de S3/GCS
- **No usa IndexingService.index_document() directamente**: Porque es un unico metodo async que ejecuta todo atomicamente, lo cual impide retry granular por etapa y requiere AsyncSession (SA 2.x incompatible con el container Airflow)

## Notas de auditoria

- Langfuse tracing pendiente: el SDK actual (`langfuse>=2.50.0`) esta instalado pero la integracion per-task requiere un adapter sync. Se deja como follow-up
- Los tests de DAG estructura (16 tests en `test_dag_indexing.py`) se skipean via `pytest.importorskip("airflow")` cuando airflow no esta en el venv

## Out of scope

- DAG de re-indexacion batch (post-MVP)
- DAG de CDC OpenText (post-MVP)
- Trigger automatico desde API de upload (post-MVP)

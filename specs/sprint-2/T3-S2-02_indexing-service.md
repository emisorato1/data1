# T3-S2-02: Indexing service como modulo reutilizable

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T3-S2-03 |
| Depende de | T3-S2-01 |
| Skill | `rag-indexing/SKILL.md` + `rag-indexing/references/indexing-service.md` |
| Estimacion | L (4-8h) |

## Contexto

Logica de indexacion como servicio Python desacoplado, invocable desde Airflow DAGs y potencialmente desde API en el futuro. Coordina todo el pipeline: validar -> cargar -> chunkar -> embeddings -> store.

## Spec

Implementar `IndexingService` que orqueste el pipeline completo de indexacion de forma transaccional, con tracking de estado en `pipeline_runs` y logging stdlib.

## Acceptance Criteria

- [x] `IndexingService` en `src/application/services/` que coordina: validar -> cargar -> chunkar -> embeddings -> store
- [x] Transaccional: si falla embeddings, no queda documento a medias en DB (el caller maneja `session.commit()` / `session.rollback()`, alineado con `PgVectorStore` que NO commitea)
- [x] Metadata del documento almacenada en tabla `documents`: nombre, tipo, paginas, fecha_indexacion, hash SHA-256 (columnas existentes: `filename`, `file_type`, `file_size`, `file_hash`, `metadata` JSONB)
- [x] Acepta como input un path a archivo (para Airflow DAGs)
- [x] Actualiza tabla `pipeline_runs` con estado del pipeline: crear row al inicio (`running`, `started_at`), actualizar al final (`completed`/`failed`, `finished_at`, `error_message`)
- [x] `LoaderFactory` que selecciona `PDFLoader` o `DOCXLoader` segun MIME type del archivo (usa `FileValidator` existente para detectar tipo)
- [x] `DocumentRepository` (ABC en domain + impl en infrastructure) con metodos: `create()`, `get_by_id()`, `find_by_hash()`, `update_after_indexing()`
- [x] Transformacion de `Chunk` objects al formato tuple que espera `PgVectorStore.add_chunks`: `(chunk_index, content, embedding, area, token_count, metadata)`
- [x] Deteccion de duplicados por `file_hash` (SHA-256) antes de indexar
- [x] Callback `on_progress` para tracking de progreso por etapa
- [x] Tests de integracion con mocks (loaders, embeddings, DB)

## Archivos a crear/modificar

- `src/infrastructure/rag/loaders/factory.py` (crear) — `LoaderFactory` que selecciona loader por MIME type
- `src/infrastructure/rag/loaders/__init__.py` (modificar) — re-exportar `LoaderFactory`
- `src/domain/repositories/document_repository.py` (modificar) — agregar `DocumentRepositoryBase` ABC
- `src/infrastructure/database/repositories/document_repository.py` (crear) — impl SQLAlchemy de `DocumentRepositoryBase`
- `src/application/services/indexing_service.py` (crear) — `IndexingService` orquestador
- `src/application/services/__init__.py` (modificar) — re-exportar `IndexingService`
- `tests/unit/test_loader_factory.py` (crear)
- `tests/integration/test_indexing_service.py` (crear)

## Decisiones de diseno

- **Service en application layer**: orquesta infraestructura, no contiene logica de negocio
- **Transaccional con DB rollback**: consistencia de datos es critica para busqueda. El `IndexingService` opera dentro de una session pero NO commitea — el caller (Airflow DAG o endpoint) es responsable del commit/rollback
- **Path como input** (no bytes): compatible con Airflow que trabaja con filesystem
- **Logging con `logging` stdlib**: patron dominante en el codebase (12+ archivos). NO usar structlog (solo 1 archivo lo usa). Migracion a structlog es decision global fuera de esta spec
- **`embed_documents`**: el metodo real de `GeminiEmbeddingService` es `embed_documents(texts, *, on_progress)`, NO `embed_batch` como indica la skill reference
- **Formato tuple para `PgVectorStore.add_chunks`**: el store espera `(chunk_index, content, embedding, area, token_count, metadata)`, NO `(Chunk, embedding)` como indica la skill reference. El servicio debe transformar los `Chunk` objects
- **`chunk_count` no existe en tabla `documents`**: no agregar columna nueva. Si se necesita el count, consultar via `COUNT(*)` en `document_chunks`. La metadata JSONB puede almacenar info adicional de indexacion
- **`pipeline_runs` ciclo de vida**: `pending` (creado por Airflow) -> `running` (IndexingService arranca) -> `completed`/`failed` (IndexingService termina). Columnas: `status`, `started_at`, `finished_at`, `error_message`
- **Sin `document_processor.py` en domain**: no hay logica de negocio pura separable de la orquestacion. La validacion ya la hace `FileValidator`, el chunking ya lo hace `AdaptiveChunker`. Crear un domain service vacio seria overengineering

## Notas de auditoria

> Correcciones aplicadas tras auditar la spec original contra las skills y el codebase:
> 1. **Langfuse removido de AC**: movido a out of scope. No hay ningun patron de Langfuse en el codebase (T1-S2-03 es la spec de instrumentacion). Forzarlo aqui generaria codigo fragil
> 2. **`embed_batch` -> `embed_documents`**: el metodo real de `GeminiEmbeddingService` se llama `embed_documents`, no `embed_batch`
> 3. **Formato de `add_chunks` corregido**: `PgVectorStore` espera tuples `(chunk_index, content, embedding, area, token_count, metadata)`, no `(Chunk, embedding)`
> 4. **`DocumentRepository` agregado**: no existia ningun repository para documentos. Agregado a archivos a crear
> 5. **`LoaderFactory` agregado**: no existia factory de loaders. Agregado a archivos a crear
> 6. **`document_processor.py` eliminado**: no hay logica de negocio pura separable. La orquestacion completa va en el application service
> 7. **Logging: structlog -> logging stdlib**: alineado con patron dominante del codebase (12+ archivos vs 1)
> 8. **`chunk_count` en `documents`**: columna no existe, no se agrega. Usar metadata JSONB o COUNT query
> 9. **`pipeline_runs` detallado**: definido ciclo de vida de estados y que columnas se actualizan en cada transicion

## Out of scope

- Trigger desde API (post-MVP, spec POST-04)
- Re-indexacion de documentos modificados (post-MVP)
- Indexacion incremental (post-MVP)
- Logging con Langfuse (spec T1-S2-03 — instrumentacion Langfuse es responsabilidad de T1, no de T3)
- Migracion de logging stdlib a structlog (decision global del equipo)

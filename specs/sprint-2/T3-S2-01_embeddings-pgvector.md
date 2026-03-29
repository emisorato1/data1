# T3-S2-01: Gemini embeddings + pgvector storage

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T3-S2-02, T4-S2-01 |
| Depende de | T1-S2-01, T3-S1-02 |
| Skill | `rag-indexing/SKILL.md` + `rag-indexing/references/gemini-embeddings.md` + `rag-indexing/references/embedding-normalization.md` + `rag-indexing/references/batch-embedding-caveats.md` + `rag-indexing/references/gemini-task-types.md` |
| Estimacion | L (4-8h) |

## Contexto

Vectorizar chunks y almacenarlos en pgvector. Es el puente entre indexacion (T3) y retrieval (T4). Sin embeddings almacenados, el sistema no puede buscar.

La tabla `document_chunks` y su indice HNSW ya existen (migracion `002_rag_domain.py`). Esta spec implementa el servicio de embeddings y el store que escriben en esa tabla.

## Spec

Implementar el servicio de embeddings con Gemini, normalizacion L2, batch processing con retry, y almacenamiento en `document_chunks.embedding` con `halfvec(768)`.

## Acceptance Criteria

- [x] Servicio de embeddings usando SDK `google-genai` (nuevo) con `client.aio.models.embed_content()` (async nativo)
- [x] Soporte dual de task_type: `RETRIEVAL_DOCUMENT` para indexacion y `RETRIEVAL_QUERY` para busqueda
- [x] Normalizacion L2 aplicada post-embedding (obligatoria porque usamos `output_dimensionality=768` < 3072 nativo, Matryoshka truncado)
- [x] Batch embedding (max 100 textos por request) con validacion de count en respuesta
- [x] Storage en `document_chunks.embedding` (columna `halfvec(768)` existente, NO tabla separada)
- [x] Retry con backoff exponencial (tenacity) para errores de API Gemini
- [x] Indice HNSW funcional (query de similitud retorna resultados ordenados por distancia coseno)
- [x] Tests: embed single + embed batch + normalizacion verificada + store/retrieve por similitud

## Archivos a crear/modificar

- `src/infrastructure/rag/embeddings/gemini_embeddings.py` (crear) — servicio de embeddings
- `src/infrastructure/rag/embeddings/normalization.py` (crear) — normalize_l2 y normalize_l2_batch
- `src/infrastructure/rag/vector_store/pgvector_store.py` (crear) — PgVectorStore con add_chunks y similarity_search
- `tests/integration/test_embeddings_pgvector.py` (crear)

## Decisiones de diseno

- **Modelo**: Usar `gemini-embedding-001` como default (sucesor de `text-embedding-004`). Configurable via `settings.gemini_embedding_model`. Si `gemini-embedding-001` no esta disponible en el tier gratuito, fallback a `text-embedding-004` (ambos soportan 768d con `output_dimensionality`)
- **SDK**: Usar `google-genai` (nuevo, ya instalado como dependencia transitiva de `langchain-google-genai`). API async nativa via `client.aio.models.embed_content()`. NO usar el SDK viejo `google.generativeai` (no esta instalado)
- **halfvec**: obligatorio por ADR-009, -50% memoria vs float32
- **Normalizacion L2**: obligatoria cuando `output_dimensionality < dimension_nativa` (Matryoshka truncado pierde norma unitaria). Implementar con numpy para batch (eficiente) y math.sqrt para single
- **Batch 100**: limite seguro por batch-embedding-caveats (bug de ordering >300 textos). Validar que `len(response.embeddings) == len(batch)` en cada request
- **Task types**: El servicio expone `embed_documents(texts)` con `RETRIEVAL_DOCUMENT` y `embed_query(text)` con `RETRIEVAL_QUERY`. Nunca mezclar task types (degrada retrieval)
- **Config via `EmbedContentConfig`**: usar `types.EmbedContentConfig(task_type=..., output_dimensionality=768)`

## Notas de auditoria

> Correcciones aplicadas tras auditar la spec original contra las skills:
> 1. **Tabla renombrada**: `chunk_embeddings` -> `document_chunks.embedding` (la tabla real del schema)
> 2. **Archivo renombrado**: `gemini_embedder.py` -> `gemini_embeddings.py` (alineado con skill)
> 3. **Archivo agregado**: `normalization.py` (separacion de responsabilidad)
> 4. **Task type dual**: Agregado `RETRIEVAL_QUERY` ademas de `RETRIEVAL_DOCUMENT`
> 5. **SDK actualizado**: De `google.generativeai` (viejo, no instalado) a `google-genai` (nuevo, disponible, async nativo)
> 6. **Modelo actualizado**: De `text-embedding-004` fijo a `gemini-embedding-001` como default (configurable)
> 7. **Referencia de batch caveats**: Agregada como skill reference

## Out of scope

- BM25/tsvector (spec T4-S2-01)
- Reranking (spec T4-S2-02)
- Cache de embeddings (post-MVP)
- Rate limiting avanzado con ventana de RPM/TPM (post-MVP, el retry con backoff es suficiente por ahora)

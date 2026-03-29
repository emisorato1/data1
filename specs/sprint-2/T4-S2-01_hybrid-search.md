# T4-S2-01: Hybrid Search (vector + BM25)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi, Lautaro) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T4-S2-02 |
| Depende de | T1-S2-01 |
| Skill | `rag-retrieval/SKILL.md` > Seccion "Busqueda Hibrida" |
| Estimacion | L (4-8h) |

## Contexto

Motor de busqueda que combina similaridad vectorial con busqueda textual. La busqueda hibrida mejora +15% la relevancia vs solo vector, especialmente para terminos exactos como codigos y nombres de normativas bancarias.

## Spec

Implementar busqueda hibrida con vector search (pgvector cosine), BM25 (PostgreSQL tsvector), y fusion con RRF (Reciprocal Rank Fusion).

## Acceptance Criteria

- [x] Busqueda vectorial: query -> Gemini embedding (task_type `RETRIEVAL_QUERY`) -> cosine similarity en pgvector
- [x] Busqueda BM25: `ts_vector` + `ts_query` en PostgreSQL sobre texto de chunks
- [x] Fusion con RRF (Reciprocal Rank Fusion), k=60
- [x] Parametros configurables: `top_k` (default 20), `rrf_k`, pesos vector/bm25
- [x] Filtro por `user_id` inyectado (seguridad basica, sin OpenText aun)
- [x] Retorna lista de chunks con score, metadata, y texto
- [x] Tests con datos indexados: verifica que busqueda hibrida supera solo-vector

## Archivos a crear/modificar

- `src/infrastructure/rag/retrieval/hybrid_search.py` (crear)
- `src/infrastructure/rag/retrieval/models.py` (crear — DTOs de resultado)
- `alembic/versions/003_bm25_indexes.py` (crear — indice GIN para tsvector)
- `tests/integration/test_hybrid_search.py` (crear)

## Decisiones de diseno

- RRF sobre weighted sum: mas robusto cuando las distribuciones de scores difieren
- k=60: valor estandar en la literatura, buen balance entre diversidad y precision
- PostgreSQL tsvector nativo sobre ElasticSearch: una dependencia menos, suficiente para MVP

## Out of scope

- Reranking (spec T4-S2-02)
- Cache semantico de queries (post-MVP)
- Filtros por area funcional (se agrega cuando Security Mirror este listo)
- Query expansion/rewriting (post-MVP)

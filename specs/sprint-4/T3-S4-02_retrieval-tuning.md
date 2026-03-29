# T3-S4-02: Tuning de retrieval

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | T3-S4-01 |
| Skill | `rag-retrieval/SKILL.md` + `database-setup/references/ef-search-tuning.md` |
| Estimacion | L (4-8h) |

## Contexto

Optimizar parametros de busqueda con el dataset real de demo. Los defaults pueden no ser optimos para los documentos bancarios especificos del proyecto. Este tuning mejora directamente la calidad de las respuestas.

## Spec

Crear set de queries de evaluacion, ajustar parametros de HNSW, RRF y reranking, y documentar parametros finales con metricas.

## Acceptance Criteria

- [x] Set de 10+ queries de evaluacion con respuestas esperadas
- [x] Tuning de `ef_search` en HNSW (trade-off precision vs latencia)
- [x] Ajuste de pesos RRF (vector vs BM25)
- [x] Ajuste de `top_k` para reranking
- [x] Documentar parametros finales y metricas de calidad (precision@5, recall@10)

## Archivos a crear/modificar

- `scripts/eval_queries.json` (creado — 12 queries de evaluacion con doc patterns esperados)
- `scripts/tune_retrieval.py` (creado — script de tuning con grid search: ef_search, pesos RRF, top_k)
- `src/config/settings.py` (modificado — parametros retrieval_ef_search, retrieval_vector_weight, retrieval_bm25_weight, retrieval_rrf_k, retrieval_top_k, reranker_top_k)
- `src/infrastructure/rag/retrieval/hybrid_search.py` (modificado — from_settings() factory method)
- `src/application/graphs/nodes/retrieve.py` (modificado — SET LOCAL hnsw.ef_search + settings.retrieval_top_k/rrf_k)
- `src/application/graphs/nodes/rerank.py` (modificado — settings.reranker_top_k en lugar de hardcoded 5)

## Decisiones de diseno

- Evaluacion manual con queries curadas: mas rapido y relevante que benchmarks genericos
- Documentar parametros: reproducibilidad, permite volver a tunear con nuevos datos

## Out of scope

- Evaluacion automatizada con RAGAS (post-MVP)
- A/B testing de configuraciones (post-MVP)
- Tuning automatico (post-MVP)

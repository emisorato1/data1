# T4-S2-02: Reranking con Vertex AI

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Lautaro) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T4-S3-02 (integracion E2E) |
| Depende de | T4-S2-01 |
| Skill | `rag-retrieval/SKILL.md` > Seccion "Reranking" |
| Estimacion | M (2-4h) |

## Contexto

Segunda pasada de relevancia sobre los resultados de hybrid search. El reranker usa un modelo cross-encoder que evalua la relevancia de cada chunk contra la query original, mejorando significativamente la precision del top-K final.

## Spec

Implementar reranking con Vertex AI Ranking API que tome los top-20 de hybrid search y produzca un top-5 reordenado por relevancia.

## Acceptance Criteria

- [x] Cliente Vertex AI Ranking API (`semantic-ranker-512@latest`)
- [x] Input: query + top-20 chunks de hybrid search
- [x] Output: chunks reordenados por relevancia, top-5 seleccionados
- [x] Fallback: si Vertex AI falla, usar orden de RRF directamente
- [x] Latencia target: < 500ms para reranking de 20 documentos
- [x] Logging de scores pre/post reranking en Langfuse
- [x] Tests con mock de Vertex AI

## Archivos a crear/modificar

- `src/infrastructure/rag/retrieval/reranker.py` (crear)
- `tests/unit/test_reranker.py` (crear)

## Decisiones de diseno

- Vertex AI Ranking sobre Cohere: ecosistema Google unificado (ADR-008), excelente espanol
- Fallback a RRF: resiliencia, el sistema sigue funcionando si Vertex AI tiene problemas
- Top-20 -> Top-5: reduce tokens de contexto para generacion, mejora precision

## Out of scope

- Reranking custom con modelo propio (post-MVP)
- A/B testing de rerankers (post-MVP)
- Metricas de impacto del reranking (se agrega con evaluacion RAGAS)

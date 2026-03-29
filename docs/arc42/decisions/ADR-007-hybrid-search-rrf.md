# ADR-007: Búsqueda Híbrida Vector + BM25 + RRF

## Status

**Accepted**

## Date

2026-02-13

## Context

El sistema RAG necesita recuperar los chunks más relevantes para una pregunta del usuario. Los documentos bancarios contienen:
- Texto denso con terminología específica (regulaciones BCRA, normativas internas)
- Códigos y números de referencia exactos (ej. "Comunicación A 7632")
- Tablas con datos numéricos
- Jerga bancaria en español

La búsqueda debe balancear comprensión semántica con coincidencia exacta de términos.

## Considered Options

### Opción 1: Solo búsqueda vectorial (cosine similarity)

Embedding de la query → cosine similarity contra embeddings de chunks.

### Opción 2: Solo búsqueda BM25 (keyword)

Full-text search con `tsvector` / `tsquery` en PostgreSQL.

### Opción 3: Búsqueda híbrida Vector + BM25 + RRF

Ambas búsquedas en paralelo, fusionadas con Reciprocal Rank Fusion.

## Decision

**Búsqueda híbrida Vector + BM25 + RRF (Opción 3)**, seguida de reranking con Vertex AI.

### Pipeline de retrieval

```
Query del usuario
    │
    ├─→ Gemini Embedding (task_type=RETRIEVAL_QUERY)
    │       └─→ Vector Search (cosine, top-30)
    │
    └─→ ts_query (PostgreSQL español)
            └─→ BM25 Search (tsvector, top-30)
    │
    ├─→ RRF Fusion (k=60, combina ambos rankings)
    │
    └─→ Vertex AI Reranking (semantic-ranker-512, top-10 final)
```

### Reciprocal Rank Fusion (RRF)

```python
def rrf_score(ranks: list[int], k: int = 60) -> float:
    """Calcula score RRF para un documento que aparece en múltiples rankings."""
    return sum(1.0 / (k + rank) for rank in ranks)

# Ejemplo: documento en posición 1 en vector y posición 5 en BM25
# score = 1/(60+1) + 1/(60+5) = 0.0164 + 0.0154 = 0.0318
```

### Configuración

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| Vector top-k | 30 | Pool amplio para RRF |
| BM25 top-k | 30 | Pool amplio para RRF |
| RRF k | 60 | Estándar de la literatura |
| Reranking input | Top-20 post-RRF | Balance calidad/latencia |
| Reranking output | Top-10 | Contexto suficiente para generación |
| Reranker | Vertex AI semantic-ranker-512@latest | Ecosistema Google, español |

### Justificación

| Tipo de query | Vector solo | BM25 solo | Híbrida |
|---------------|------------|-----------|---------|
| "¿Qué requisitos tiene la normativa de créditos?" | Bueno (semántica) | Medio (keywords parciales) | Excelente |
| "Comunicación A 7632" | Malo (embedding no captura códigos) | Excelente (match exacto) | Excelente |
| "regulación sobre lavado de activos" | Bueno | Bueno | Excelente (+combinación) |

Benchmarks de la literatura muestran **+15% de relevancia** en búsqueda híbrida vs solo vectorial.

## Consequences

### Positivas

- Cubre tanto consultas semánticas como búsquedas de términos exactos
- +15% relevancia vs solo vectorial en benchmarks
- RRF es simple, determinístico, y no requiere entrenamiento
- Todo ejecuta en PostgreSQL (sin servicio de búsqueda adicional)
- Vertex AI reranking como segunda pasada mejora precisión del top-10

### Negativas

- Dos queries a PostgreSQL por cada consulta (vector + BM25) — mitigado con ejecución paralela
- RRF requiere tuning del parámetro k (60 es buen default)
- BM25 requiere mantenimiento de `tsvector` (trigger en INSERT/UPDATE)
- Latencia ligeramente mayor que solo vectorial (~50-100ms extra)

## References

- [Reciprocal Rank Fusion — Original Paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [Vertex AI Ranking API](https://cloud.google.com/vertex-ai/docs/generative-ai/ranking)
- Skill: `.claude/skills/rag-retrieval/SKILL.md`

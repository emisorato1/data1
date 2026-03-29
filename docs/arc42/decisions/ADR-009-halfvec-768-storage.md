# ADR-009: halfvec(768) para Almacenamiento Vectorial

## Status

**Accepted**

## Date

2026-02-13

## Context

Los embeddings generados por Gemini text-embedding-004 tienen 768 dimensiones (Matryoshka). Debemos elegir el tipo de dato para almacenar estos embeddings en pgvector, considerando:
- Volumen potencial: hasta 1M+ documentos × ~10 chunks/doc = 10M+ embeddings
- Latencia de búsqueda: p95 < 300ms para vector search
- Costo de almacenamiento: RAM y disco

## Considered Options

### Opción 1: vector(768) — float32

768 dimensiones × 4 bytes = **3,072 bytes/embedding**

### Opción 2: halfvec(768) — float16

768 dimensiones × 2 bytes = **1,536 bytes/embedding**

### Opción 3: Quantización binaria (bit vectors)

768 dimensiones × 1 bit = **96 bytes/embedding**

## Decision

**halfvec(768) — float16 (Opción 2).**

### Comparación a escala

| Métrica | vector (float32) | halfvec (float16) | Ahorro |
|---------|-------------------|--------------------|----|
| Bytes/embedding | 3,072 | 1,536 | -50% |
| 1M embeddings | ~3 GB | ~1.5 GB | -50% |
| 10M embeddings | ~30 GB | ~15 GB | -50% |
| Índice HNSW (10M) | ~45 GB | ~22 GB | -50% |
| Recall@10 loss | baseline | < 1% | Negligible |

### Requisitos

- **pgvector 0.8.0+**: halfvec support fue introducido en esta versión
- **PostgreSQL 16+**: compatible con halfvec y HNSW iterative scans

### Definición de tabla

```sql
CREATE TABLE chunk_embeddings (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER REFERENCES document_chunks(id),
    embedding halfvec(768) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_embeddings_hnsw
ON chunk_embeddings USING hnsw (embedding halfvec_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Justificación

- A 768 dimensiones, float16 pierde < 1% de precisión en recall@10 vs float32
- Gemini embeddings son Matryoshka: diseñados para funcionar bien con dimensionalidad y precisión reducida
- El ahorro de 50% en RAM es crítico para índices HNSW que deben caber en memoria
- Quantización binaria (Opción 3) pierde demasiada información para documentos bancarios densos

## Consequences

### Positivas

- 50% menos RAM y almacenamiento
- Índice HNSW más rápido de construir y buscar (menos datos)
- Pérdida de precisión negligible (< 1% en recall@10)
- Escala a 10M+ embeddings en hardware razonable

### Negativas

- Requiere pgvector 0.8+ (restricción de versión mínima)
- Si se migra a otro vector store, verificar que soporte float16
- Debugging: los valores halfvec no son legibles directamente en SQL (necesitan cast)

## References

- [pgvector halfvec support](https://github.com/pgvector/pgvector#half-precision-vectors)
- [Matryoshka Representation Learning](https://arxiv.org/abs/2205.13147)
- [Gemini Embedding Dimensions](https://ai.google.dev/gemini-api/docs/embeddings)

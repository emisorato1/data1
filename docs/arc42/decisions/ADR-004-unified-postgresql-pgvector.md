# ADR-004: PostgreSQL + pgvector como Base de Datos Unificada

## Status

**Accepted**

## Date

2026-02-13

## Context

El sistema necesita almacenar:
- Datos relacionales (usuarios, conversaciones, mensajes, documentos, permisos, audit logs)
- Embeddings vectoriales (768 dimensiones por chunk, potencialmente millones)
- Texto completo para búsqueda BM25 (tsvector)
- Estado de LangGraph (checkpoints de conversación)
- Tablas espejo de OpenText (permisos de documentos)

Debemos decidir si usar una base de datos unificada o bases especializadas separadas.

## Considered Options

### Opción 1: PostgreSQL unificado con pgvector

Un solo PostgreSQL 16+ con la extensión pgvector 0.8+ para almacenamiento vectorial y búsqueda de similitud.

### Opción 2: PostgreSQL (relacional) + Pinecone/Weaviate (vectorial)

Base relacional separada de la base vectorial.

### Opción 3: PostgreSQL (relacional) + Elasticsearch (texto + vectorial)

Elasticsearch para búsqueda de texto completo y vectorial.

## Decision

**PostgreSQL 16+ con pgvector 0.8+ como base de datos unificada (Opción 1).**

### Justificación

| Criterio | PG + pgvector | PG + Pinecone | PG + Elasticsearch |
|----------|---------------|---------------|-------------------|
| Complejidad operacional | 1 servicio | 2 servicios + sync | 2 servicios + sync |
| Consistencia transaccional | ACID nativo | Eventual (cross-DB) | Eventual (cross-DB) |
| Búsqueda híbrida | SQL unificado (vector + BM25 en 1 query) | 2 queries + merge client-side | Posible pero complejo |
| Costo | Incluido | $70-700+/mes (Pinecone) | Cluster adicional |
| Latencia | Local (sin network hop) | Network hop por query | Network hop por query |
| Auditoría | Un solo audit log | Datos dispersos | Datos dispersos |
| Escala (1M docs) | Suficiente con HNSW | Mejor para >10M | Mejor para full-text pesado |
| halfvec support | pgvector 0.8+ nativo | No (float32 solo) | No |

### Capacidades unificadas en PostgreSQL

```sql
-- Búsqueda vectorial (cosine similarity)
SELECT * FROM chunk_embeddings
ORDER BY embedding <=> $query_embedding::halfvec(768)
LIMIT 30;

-- Búsqueda BM25 (text search)
SELECT * FROM document_chunks
WHERE tsv @@ plainto_tsquery('spanish', $query)
ORDER BY ts_rank(tsv, query) DESC
LIMIT 30;

-- Joins directos (sin sync cross-DB)
SELECT ce.*, dc.content, d.title
FROM chunk_embeddings ce
JOIN document_chunks dc ON ce.chunk_id = dc.id
JOIN documents d ON dc.document_id = d.id
WHERE d.area_funcional = 'riesgo';
```

### Índices

```sql
-- HNSW para búsqueda vectorial (pgvector 0.8+)
CREATE INDEX idx_embeddings_hnsw
ON chunk_embeddings USING hnsw (embedding halfvec_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- GIN para búsqueda BM25
CREATE INDEX idx_chunks_tsv ON document_chunks USING gin(tsv);
```

## Consequences

### Positivas

- Una sola base de datos: simplicidad operacional, backup unificado, un solo connection pool
- ACID: transacciones atómicas entre datos relacionales y vectoriales
- Búsqueda híbrida en un solo SQL (vector + BM25 + RRF sin cross-DB merge)
- halfvec(768) nativo: -50% almacenamiento vs float32
- LangGraph `PostgresSaver` usa la misma instancia
- Audit trail completo en un solo lugar

### Negativas

- Si el volumen supera 10M+ chunks, pgvector puede requerir tuning avanzado o particionamiento
- No tiene las features enterprise de Pinecone (namespaces, metadata filtering avanzado)
- El tuning de HNSW (m, ef_construction, ef_search) requiere experimentación

### Mitigación para escala futura

- Particionamiento de tablas por `area_funcional` si crece mucho
- Read replicas para separar carga de lectura/escritura
- Si escala excede pgvector: extraer a Pinecone/Qdrant con Strangler Pattern

## References

- [pgvector — GitHub](https://github.com/pgvector/pgvector)
- [pgvector 0.8 halfvec support](https://github.com/pgvector/pgvector/releases/tag/v0.8.0)
- [HNSW index tuning guide](https://github.com/pgvector/pgvector#hnsw)

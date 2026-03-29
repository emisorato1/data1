# T3-S1-02: Estrategia de chunking

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T3-S2-01 (embeddings necesitan chunks) |
| Depende de | T3-S1-01 |
| Skill | `rag-indexing/SKILL.md` + `rag-indexing/references/chunking-area.md` |
| Estimacion | M (2-4h) |

## Contexto

Segmentacion adaptativa de documentos bancarios. El chunking es critico para la calidad del RAG: chunks muy pequenos pierden contexto, chunks muy grandes diluyen la relevancia. Los documentos bancarios son densos y contienen tablas que no deben partirse.

## Spec

Implementar `AdaptiveChunker` que segmente documentos en chunks de ~4KB (1000 tokens) con 15% overlap, detectando y preservando tablas como unidades atomicas.

## Acceptance Criteria

- [x] `AdaptiveChunker` en `src/infrastructure/rag/chunking/adaptive_chunker.py`
- [x] Usa `RecursiveCharacterTextSplitter` de LangChain como base
- [x] Configuracion:
  - Chunk size: ~4KB (1000 tokens)
  - Overlap: 15% (~150 tokens)
  - Separadores configurables por tipo de documento
- [x] Deteccion de tablas: chunks de tabla no se parten (tabla completa = 1 chunk)
- [x] Cada chunk preserva metadata:
  - `doc_id`: ID del documento padre
  - `chunk_index`: posicion secuencial dentro del documento
  - `page_number`: pagina de origen
  - `source_file`: nombre del archivo original
  - `has_table`: boolean indicando si contiene tabla
- [x] Metodo `chunk(document: LoadedDocument) -> list[Chunk]`
- [x] `Chunk` dataclass con: `text`, `metadata`, `token_count`
- [x] Tests con documentos bancarios de ejemplo (texto denso + tablas)

## Archivos a crear/modificar

- `src/infrastructure/rag/chunking/adaptive_chunker.py` (crear)
- `src/infrastructure/rag/chunking/__init__.py` (modificar — exports)
- `tests/unit/test_adaptive_chunker.py` (crear)
- `tests/fixtures/doc_with_tables.txt` (crear — texto simulando doc bancario con tablas)

## Decisiones de diseno

- 4KB sobre 512 tokens: documentos bancarios son densos, 512 tokens fragmenta ideas complejas
- 15% overlap: balance entre coherencia en fronteras y redundancia de storage
- RecursiveCharacterTextSplitter: robusto, bien testeado, separadores jerarquicos

## Out of scope

- Embeddings de chunks (spec T3-S2-01)
- Deteccion automatica de area funcional por keywords (se agrega en Sprint 2)
- Almacenamiento en pgvector (spec T3-S2-01)
- Chunking de imagenes dentro de documentos (post-MVP)

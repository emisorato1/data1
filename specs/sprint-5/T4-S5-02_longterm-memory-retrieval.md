# T4-S5-02: Long-term memory retrieval integrado en busqueda

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Lautaro) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | T4-S5-01 |
| Skill | `chat-memory/SKILL.md` + `rag-retrieval/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Episodic memories are stored but not yet used during retrieval. The RAG pipeline needs to incorporate relevant long-term memories to provide personalized, context-aware responses.

## Spec

Integrate episodic memory retrieval into the hybrid search pipeline, adding relevant user memories as additional context before generation.

## Acceptance Criteria

- [x] Nuevo paso en el nodo `retrieve` que busca memorias relevantes del usuario
- [x] Busqueda por similarity en episodic_memories usando query embedding
- [x] Top-K configurable (default: 5 memorias mas relevantes)
- [x] Memorias inyectadas en el contexto del prompt de generacion (seccion separada)
- [x] Update de `last_accessed` en memorias utilizadas (para decay futuro)
- [x] Peso configurable de memorias vs documentos en el contexto
- [x] Si no hay memorias relevantes (similarity < threshold), no se inyectan
- [x] Tests de integracion: query con y sin memorias relevantes

## Archivos a crear/modificar

- `src/application/graphs/nodes/retrieve.py` (modificar — agregar memory retrieval)
- `src/application/services/memory_retrieval_service.py` (crear)
- `tests/integration/test_memory_retrieval.py` (crear)

## Decisiones de diseno

- **Retrieval separado de documentos**: Las memorias se buscan en paralelo con los documentos, no compiten en el mismo index.
- **Inyeccion en prompt (no en retrieval context)**: Las memorias son contexto personal, no chunks de documentos. Van en seccion separada del system prompt.
- **Last_accessed tracking**: Permite implementar memory decay en el futuro (memorias no accedidas se degradan).

## Out of scope

- Memory decay/expiry automatico
- UI para visualizar memorias
- Memoria compartida entre usuarios

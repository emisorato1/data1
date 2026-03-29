# T4-S6-01: Filtros permisos en hybrid search (late binding)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T6-S7-01, T6-S10-03 |
| Depende de | T3-S6-02 |
| Skill | `security-mirror/SKILL.md` + `rag-retrieval/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Zero Trust requires that search results only include documents the user is authorized to see. Late binding means permission checks happen at query time (not at indexing time), ensuring always-current permissions.

## Spec

Integrate PermissionResolver into the hybrid search pipeline so that retrieval results are filtered by user permissions before reranking and generation.

## Acceptance Criteria

- [x] Filtro de permisos inyectado en el nodo `retrieve` del grafo LangGraph
- [x] Late binding: permisos evaluados al momento de la query, no pre-filtrados en index
- [x] Vector search: WHERE clause con document_ids accesibles del PermissionResolver
- [x] BM25 search: mismo filtro aplicado
- [x] Performance: overhead < 200ms para filtrado de permisos
- [x] Si usuario no tiene acceso a ningun documento: respuesta "No tengo documentos disponibles para tu consulta"
- [x] Logging: documentos filtrados por permisos registrados en Langfuse
- [x] Tests: query con documentos accesibles, query sin documentos accesibles, mixed

## Archivos a crear/modificar

- `src/application/graphs/nodes/retrieve.py` (modificar)
- `tests/integration/test_permission_search.py` (crear)

## Decisiones de diseno

- **Late binding sobre pre-filtering**: Permisos pueden cambiar entre indexacion y query. Late binding siempre refleja permisos actuales.
- **WHERE clause en search**: Mas eficiente que filtrar post-retrieval.

## Out of scope

- Permission caching optimization
- Row-level security en PostgreSQL

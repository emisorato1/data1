# T3-S9-01: Document versioning y re-indexacion

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Media |
| Estado | pending |
| Bloqueante para | - |
| Depende de | T3-S7-01 |
| Skill | `document-management/SKILL.md` + `rag-indexing/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Documents may be updated (new policy version, updated procedure). System needs to track versions, maintain history, and auto re-index.

## Spec

Implement document versioning that tracks version history, stores multiple versions, and triggers re-indexation on new version upload.

## Acceptance Criteria

- [ ] Campo `version` en tabla `documents` (auto-incrementing per document)
- [ ] Version nueva: anterior marcado como `superseded`
- [ ] Historial versiones: `GET /documents/{id}/versions`
- [ ] Re-indexacion automatica: nuevos chunks reemplazan antiguos
- [ ] Chunks viejos eliminados solo tras nuevos disponibles (swap atomico)
- [ ] Search siempre usa version mas reciente
- [ ] Migracion Alembic para campo version y tabla `document_versions`
- [ ] Tests versionado con multiples versiones

## Archivos a crear/modificar

- `alembic/versions/xxx_add_document_versioning.py` (crear)
- `src/domain/models/document.py` (modificar)
- `src/application/services/document_version_service.py` (crear)
- `src/api/routes/documents.py` (modificar)
- `tests/unit/test_document_versioning.py` (crear)

## Decisiones de diseno

- **Soft replace over hard delete**: Version anterior en historial.
- **Atomic swap**: Estado consistente durante re-indexacion.
- **Auto-increment per doc**: Cada documento su conteo.

## Out of scope

- Diff entre versiones
- Version rollback
- Concurrent editing

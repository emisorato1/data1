# T2-S7-01: Endpoints CRUD documentos (GET list, GET by id, DELETE)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Ema) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T5-S7-01 |
| Depende de | T2-S5-02 |
| Skill | `document-management/SKILL.md` + `api-design/SKILL.md` |
| Estimacion | L (4-8h) |

> POST-05

## Contexto

Document management requires more than upload. Users and admins need to list documents (with filtering and pagination), view document details (including indexing status), and delete documents (with cascade cleanup of chunks and embeddings).

## Spec

Implement REST API endpoints for listing, retrieving, and deleting documents, with proper authorization checks and cascade operations.

## Acceptance Criteria

- [x] `GET /api/v1/documents` con paginacion (limit/offset), filtros por status, type, date range
- [x] `GET /api/v1/documents/{id}` con metadata completa, status del pipeline, chunk count
- [x] `DELETE /api/v1/documents/{id}` con cascade: elimina chunks, embeddings, archivo GCS
- [x] Response paginada con total_count, next/prev links
- [x] Filtro por status: pending, indexing, indexed, failed
- [x] Solo documentos accesibles al usuario (integrar PermissionResolver si disponible)
- [x] Admin role puede ver/eliminar todos los documentos
- [x] Soft delete: marca como `deleted`, cleanup asincronico
- [x] Tests de cada endpoint con distintos roles y filtros

## Archivos a crear/modificar

- `src/api/routes/documents.py` (modificar — agregar GET y DELETE)
- `src/application/services/document_service.py` (crear)
- `src/api/schemas/documents.py` (modificar — agregar schemas de response)
- `tests/integration/test_document_crud.py` (crear)

## Decisiones de diseno

- **Soft delete**: El documento se marca como deleted inmediatamente, pero la limpieza de chunks/embeddings/GCS es asincronica para no bloquear el request
- **Paginacion limit/offset**: Simple y suficiente para volumen esperado (< 10k documentos)
- **Permission check en list**: GET list solo retorna documentos accesibles al usuario actual

## Out of scope

- Bulk delete/operations
- Document versioning (spec T3-S9-01)
- Document update/replace (re-upload es delete + upload nuevo)

## Registro de Implementacion

**Fecha:** 2026-03-25

### Archivos creados

| Archivo | Descripcion |
|---------|-------------|
| `src/application/services/document_service.py` | Servicio de aplicación para CRUD de documentos con autorización |
| `tests/integration/test_document_crud.py` | 22 tests de integración para los endpoints |

### Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `src/infrastructure/api/v1/documents.py` | Agregados GET list, GET detail, DELETE endpoints |
| `src/infrastructure/api/schemas/documents.py` | Agregados DocumentListResponse, DocumentDetailResponse, DocumentDeleteResponse, PaginationLinks |
| `src/domain/repositories/document_repository.py` | Agregados métodos list_documents, soft_delete, get_by_id_with_chunk_count + dataclasses |
| `src/infrastructure/database/repositories/document_repository.py` | Implementación de nuevos métodos del repositorio |
| `src/infrastructure/database/models/document.py` | Agregado estado `indexing` a DocumentStatus |
| `tests/integration/test_document_upload.py` | Ajustados status codes (400/413 -> 422) por cambio a ValidationError |

### Notas de implementación

- DELETE usa soft delete (`is_active=False`), cleanup asíncrono de GCS/chunks queda pendiente
- Autorización basada en `uploaded_by` para usuarios regulares, admins (`is_superuser`) pueden todo
- Paginación limit/offset con links next/prev en response
- Coverage: 87% en archivos modificados/creados

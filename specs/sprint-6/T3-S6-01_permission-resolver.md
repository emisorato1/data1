# T3-S6-01: PermissionResolver con datos sinteticos OpenText

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T3-S6-02, T4-S6-01, T3-S7-01 |
| Depende de | T3-S3-01 (done) |
| Skill | `security-mirror/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

The Security Mirror pattern replicates OpenText ACLs in PostgreSQL. The PermissionResolver translates OpenText permission models into database queries that determine document access for each user. Uses synthetic data initially (real OpenText data comes later via CDC).

## Spec

Implement PermissionResolver service that queries the local permission mirror tables (opentext_permissions, opentext_group_members from T3-S3-01) to determine if a user has access to specific documents.

## Acceptance Criteria

- [x] Clase `PermissionResolver` en `src/infrastructure/security/permission_resolver.py`
- [x] Metodo `can_access(user_id, document_id) -> bool` que consulta tablas de permisos
- [x] Metodo `get_accessible_document_ids(user_id) -> list[str]` para filtrado batch
- [x] Soporte para permisos directos (usuario -> documento) e indirectos (via grupo)
- [x] Datos sinteticos de **prueba**: 50+ documentos, 10+ usuarios, 5+ grupos con permisos variados
- [x] Seeds de datos sinteticos ejecutables via script o fixture
- [x] Cache Redis de permisos con TTL configurable (default: 5 min)
- [x] Tests con escenarios: acceso directo, acceso por grupo, denegado, sin permisos

## Archivos a crear/modificar

- `src/infrastructure/security/permission_resolver.py` (crear)
- `src/infrastructure/security/permission_cache.py` (crear)
- `scripts/seed_synthetic_permissions.py` (crear)
- `tests/unit/test_permission_resolver.py` (crear)

## Decisiones de diseno

- **Cache Redis**: Permisos no cambian frecuentemente, cache reduce load en DB.
- **Datos sinteticos primero**: No dependemos de OpenText real para development/testing.

## Out of scope

- Recursive CTE (spec T3-S6-02)
- CDC sync (spec T3-S7-01)
- Permisos en real-time

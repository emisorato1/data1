# T2-S5-03: Audit logging forense SHA-256 hashing

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Branko) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | - |
| Depende de | T2-S2-01 (done), T2-S2-02 (done), T1-S1-04 (done) |
| Skill | `observability/SKILL.md` |
| Estimacion | M (2-4h) |

## Contexto

Enterprise banking environment requires comprehensive audit trails. Every significant action must be logged immutably with cryptographic integrity verification for forensic analysis and compliance.

## Spec

Implement structured audit logging with SHA-256 hash chaining, covering all document operations, authentication events, and RAG queries.

## Acceptance Criteria

- [x] Modelo `AuditLog` con campos: timestamp, actor_id, action, resource_type, resource_id, details_json, hash_chain
- [x] Hash chain: cada entry incluye SHA-256 de (entry_data + previous_hash)
- [x] Tabla `audit_logs` creada via Alembic migration
- [x] AuditService con metodo `log(actor, action, resource, details)`
- [x] Eventos auditados: document_upload, document_delete, login, logout, query, admin_action
- [x] Middleware FastAPI que automaticamente loguea requests a endpoints sensibles
- [x] Endpoint `GET /api/v1/admin/audit-logs` con paginacion y filtros (solo admin)
- [x] Verificacion de integridad: endpoint o script que valida la hash chain
- [x] Tests unitarios del hash chain y del servicio

## Archivos a crear/modificar

- `src/domain/models/audit_log.py` (crear)
- `src/application/services/audit_service.py` (crear)
- `src/api/middleware/audit_middleware.py` (crear)
- `src/api/routes/admin.py` (crear o modificar)
- `alembic/versions/xxx_add_audit_logs_table.py` (crear)
- `tests/unit/test_audit_service.py` (crear)

## Decisiones de diseno

- **Hash chain sobre simple logging**: Garantiza integridad forense. Si alguien modifica un log, la cadena se rompe.
- **JSON details flexible**: Permite distintos tipos de eventos sin schema rigido.
- **Middleware automatico**: Reduce riesgo de olvidar loguear un endpoint.

## Out of scope

- Exportacion de audit logs a SIEM externo
- Rotacion y archivado de logs antiguos
- Tamper-evident logging con blockchain

# T2-S5-02: Storage GCS + registro DB status pending

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Branko) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T1-S5-01, T2-S7-01 |
| Depende de | T2-S5-01, INFRA-S5-01 |
| Skill | `document-management/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Once a document is uploaded and validated, it needs to be stored durably in GCS and tracked in the database. This is the persistence layer of the document management pipeline.

## Spec

Implement GCS storage service that saves uploaded files to a structured bucket path, creates a `documents` DB record with status `pending`, and returns the storage URI.

## Acceptance Criteria

- [x] Servicio `DocumentStorageService` que sube archivos a GCS bucket
- [x] Path estructura en GCS: `{tenant_id}/{year}/{month}/{document_id}/{filename}`
- [x] Registro en tabla `documents` con status `pending`, storage_uri, metadata
- [x] Tabla `documents` creada via migracion Alembic (si no existe)
- [x] Transaccion atomica: si falla GCS upload, no se crea registro DB
- [x] Transaccion atomica: si falla DB insert, se elimina archivo de GCS (compensacion)
- [x] Configuracion de GCS bucket via environment variables
- [x] Tests con mock de GCS client

## Archivos a crear/modificar

- `src/infrastructure/storage/gcs_client.py` (crear)
- `src/infrastructure/storage/__init__.py` (crear)
- `src/application/services/document_storage_service.py` (crear)
- `alembic/versions/xxx_add_documents_table.py` (crear — si tabla no existe)
- `tests/unit/test_document_storage.py` (crear)

## Decisiones de diseno

- **GCS sobre filesystem**: Durabilidad, escalabilidad, CMEK encryption nativo. El bucket se provisiona en INFRA-S5-01.
- **Path con tenant_id**: Preparado para multi-tenancy futuro sin cambios de estructura.
- **Compensacion en vez de two-phase commit**: Mas simple y confiable en un contexto de cloud storage.

## Out of scope

- Provisioning del bucket GCS (spec INFRA-S5-01 en itmind-infrastructure)
- Lifecycle policies del bucket (spec INFRA-S5-01)
- Trigger de indexacion (spec T1-S5-01)

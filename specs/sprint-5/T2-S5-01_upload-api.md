# T2-S5-01: API upload documentos + validacion archivo

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Ema) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T2-S5-02 |
| Depende de | - |
| Skill | `document-management/SKILL.md` + `api-design/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

First step of the Document Management feature. Users (and future automated systems) need to upload documents to the RAG system. Currently, document loading is batch-only via Airflow. This endpoint enables on-demand document uploads.

## Spec

Implement `POST /api/v1/documents` endpoint with multipart/form-data upload, file type validation (PDF, DOCX, TXT, CSV), size limit (50MB), and metadata extraction.

## Acceptance Criteria

- [x] `POST /api/v1/documents` endpoint acepta multipart/form-data
- [x] Validacion de tipo de archivo: PDF, DOCX, TXT, CSV (usando FileValidator existente)
- [x] Validacion de tamano maximo: 50MB configurable via settings
- [x] Extraccion de metadata basica (nombre, tamano, tipo MIME, hash SHA-256)
- [x] Response 201 con document_id, metadata y status `pending`
- [x] Response 400 con mensaje claro para archivos invalidos
- [x] Response 413 para archivos que exceden tamano maximo
- [x] Autenticacion JWT requerida (usa middleware existente)
- [x] Tests unitarios y de integracion del endpoint

## Archivos a crear/modificar

- `src/api/routes/documents.py` (crear)
- `src/api/schemas/documents.py` (crear)
- `src/application/services/document_upload_service.py` (crear)
- `tests/integration/test_document_upload.py` (crear)

## Decisiones de diseno

- **Combinar upload + validacion en un endpoint**: POST-01 y POST-02 del backlog describen funcionalidades inseparables. La validacion ocurre antes de persistir.
- **FileValidator reutilizado**: El componente de Sprint 1 (T3-S1-01) ya valida tipos y tamanos. Se reutiliza en el endpoint.
- **SHA-256 hash en upload**: Se calcula al recibir el archivo para audit trail y deduplicacion futura.

## Out of scope

- Storage en GCS (spec T2-S5-02)
- Trigger de Airflow DAG (spec T1-S5-01)
- Endpoints CRUD de documentos (spec T2-S7-01)
- Frontend de gestion de documentos (spec T5-S7-01)

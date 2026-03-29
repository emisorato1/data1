# T1-S2-01: Schema SQL completo + migraciones de dominio

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco, Agus) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T3-S2-01, T4-S2-01 |
| Depende de | T1-S1-04 |
| Skill | `database-setup/SKILL.md` + `security-mirror/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Tablas para todo el dominio RAG: documentos, chunks con embeddings integrados y pipeline status. Incluye reproducción fiel del modelo de seguridad de OpenText (dtree, kuaf, dtreeacl) con datos sintéticos para validación de permisos "Late Binding".

## Spec

Crear migraciones Alembic con las tablas del dominio RAG y el espejo de seguridad de OpenText. Los IDs relacionados con OpenText deben usar `BigInteger`. Los embeddings se almacenan directamente en la tabla de chunks.

## Acceptance Criteria

- [x] Migracion con tablas: `documents`, `document_chunks`
- [x] Columna `embedding halfvec(768)` directamente en `document_chunks`
- [x] Indice HNSW creado: `CREATE INDEX ON document_chunks USING hnsw (embedding halfvec_cosine_ops)`
- [x] Tabla `audit_logs` y `security_events` para trazabilidad bancaria
- [x] Tabla `pipeline_runs` para tracking de ejecuciones (document_id, dag_run_id, status, started_at, finished_at)
- [x] Espejo OpenText (mismo schema): `dtree`, `kuaf`, `dtreeacl`, `kuafchildren`, `dtreeancestors`
- [x] Todos los IDs provenientes de OpenText (DataID, RightID, ID, etc.) definidos como `BIGINT`
- [x] Vista Materializada para rendimiento: `kuaf_membership_flat`
- [x] Script de seed data para desarrollo (usuarios mock, docs mock, ACLs mock)
- [x] `alembic upgrade head` aplica todo sin errores

## Archivos a crear/modificar

- `alembic/versions/002_rag_domain.py` (crear)
- `src/infrastructure/database/models/document.py` (actualizar DocumentChunkModel)
- `src/infrastructure/database/models/audit.py` (crear AuditLogModel, SecurityEventModel)
- `src/infrastructure/database/models/permission.py` (crear modelos para dtree, kuaf, dtreeacl)
- `scripts/seed_data.py` (crear)

## Decisiones de diseno

- **Single Table Storage**: Embeddings en `document_chunks` para evitar JOINs y cumplir con SLA < 3s.
- **BigInteger para IDs**: Garantiza compatibilidad con los sistemas legados de OpenText y evita overflow.
- **Fidelidad Semántica**: Se mantienen nombres originales (`dtree`, `kuaf`) para asegurar que la lógica de bitmasking (`permissions & 2`) sea portable al sistema real.
- **Unified Schema**: Por simplicidad en la fase inicial, se utiliza el schema `public` para las tablas de seguridad, facilitando el desarrollo.

## Out of scope

- Repositorios SQLAlchemy (se crean bajo demanda)
- Indices GIN para BM25 (spec T4-S2-01)
- CDC desde OpenText real (post-MVP)

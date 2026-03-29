# T3-S5-02: Sincronización metadata y permisos xECM

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Alta |
| Estado | blocked |
| Bloqueante para | IA-07 (testing interno), IA-19 (escenarios xECM) |
| Depende de | T3-S3-01 (done), INFRA E-02 (done), INFRA E-03 (done), Coordinacion #2 (acceso xECM) |
| Skill | `security-mirror/SKILL.md` |
| Estimacion | M (2-4h) |
| Backlog CSV | IA-06 |

## Contexto

La infraestructura de OpenText Content Server ya esta desplegada en GCP (specs E-01, E-02, E-03 del repositorio `itmind-infrastructure`):
- 4 VMs Windows provisionadas (Frontend, Backend, Archive Center, Database) en subnet 10.2.48.0/21
- IAM y outputs configurados (E-03)
- Datos sinteticos ya cargados en las tablas del Security Mirror (T3-S3-01)

Esta tarea implementa la sincronizacion real de metadata y permisos desde OpenText xECM hacia las tablas del Security Mirror en PostgreSQL, reemplazando los datos sinteticos con datos reales cuando el acceso al Content Server este disponible.

**BLOCKER ACTUAL:** No hay acceso real al Content Server de OpenText. La coordinacion #2 (acceso xECM) debe resolverse antes de poder implementar esta tarea. Mientras tanto, el sistema opera con datos sinteticos (T3-S3-01).

## Spec

Implementar un servicio de sincronizacion que conecte al API REST de OpenText Content Server, extraiga la estructura de documentos, usuarios, grupos y permisos (ACLs), y los sincronice en las tablas del Security Mirror PostgreSQL.

## Acceptance Criteria

- [ ] Cliente API para OpenText Content Server (`ContentServerClient`)
  - Autenticacion via API key o usuario/password
  - Endpoints: `/api/v2/nodes`, `/api/v2/members`, `/api/v2/nodes/{id}/permissions`
  - Manejo de paginacion y rate limiting
- [ ] Servicio `XECMSyncService` que sincroniza:
  - Tabla `dtree`: nodos (carpetas y documentos) con SubType, Name, ParentID
  - Tabla `kuaf`: usuarios y grupos con Type, Name, GroupID
  - Tabla `kuafchildren`: membresia de grupos (ParentID → ChildID)
  - Tabla `dtreeacl`: permisos ACL con bitmask de OpenText (See=1, SeeContents=2)
  - Tabla `dtreeancestors`: jerarquia de ancestros para herencia de permisos
- [ ] Refresco de vista materializada `kuaf_membership_flat` post-sincronizacion
- [ ] Sincronizacion incremental: solo actualizar nodos/permisos modificados desde ultima sync (usando campo `modify_date`)
- [ ] Configuracion de Content Server URL y credenciales via environment variables
- [ ] Tests unitarios con mock del API de Content Server
- [ ] Logging estructurado de la sincronizacion (nodos creados/actualizados/eliminados)

## Archivos a crear/modificar

- `src/infrastructure/opentext/client.py` (crear)
- `src/infrastructure/opentext/__init__.py` (crear)
- `src/application/services/xecm_sync_service.py` (crear)
- `tests/unit/test_xecm_sync.py` (crear)

## Decisiones de diseno

- **REST API sobre ODBC/SQL directo**: El Content Server expone REST API v2, mas seguro y mantenible que conectar directo a la DB de OpenText.
- **Sincronizacion incremental sobre full-sync**: Reduce carga en el Content Server y tiempo de sincronizacion. Full-sync disponible como fallback.
- **Reutilizar tablas existentes**: Las tablas del Security Mirror (T1-S2-01, T3-S3-01) ya existen con el schema correcto. Solo se reemplazan datos sinteticos por reales.
- **Sin Airflow DAG en esta spec**: La sincronizacion se ejecuta manualmente o via endpoint admin. El DAG programado de CDC es post-MVP (INFRA-S7-01 + T3-S7-01 via Pub/Sub).

## Dependencias de infraestructura (itmind-infrastructure)

| Spec Infra | Descripcion | Estado |
|------------|-------------|--------|
| E-01 | ECM Stage Scaffold | done |
| E-02 | ECM Compute Instances (4 VMs Windows) | done |
| E-03 | ECM IAM + Outputs | done |
| INFRA-S7-01 | Pub/Sub Topic CDC OpenText (para DAG event-driven futuro) | pending (Sprint 7) |

## Out of scope

- DAG de CDC automatizado via Pub/Sub (spec INFRA-S7-01 + T3-S7-01, Sprint 7)
- PermissionResolver con late binding en hybrid search (spec POST-08)
- Recursive CTE para membresia de grupos (spec POST-10)
- Configuracion de VPN o firewall rules para conectividad Content Server (responsabilidad infra)

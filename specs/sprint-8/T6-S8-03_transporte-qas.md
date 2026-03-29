# T6-S8-03: Transporte configuracion DEV a QAS

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, Agus) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-S9-01 |
| Depende de | T6-S8-01, T6-S8-02 |
| Skill | `docker-deployment/SKILL.md` |
| Estimacion | L (4-8h) — IA-21 |

## Contexto

QAS must be an exact replica of the validated DEV environment for formal testing. This involves migrating config, data, and deployments.

## Spec

Execute transport of all configuration, application deployment, and test data from DEV to QAS environment.

## Acceptance Criteria

- [ ] Ambiente QAS desplegado via Helm con values-staging.yaml
- [ ] Base de datos QAS inicializada con migraciones Alembic
- [ ] Datos de prueba migrados: documentos, embeddings, usuarios
- [ ] Configuracion Airflow transportada: DAGs, connections, variables
- [ ] Langfuse operativo en QAS
- [ ] Smoke test en QAS: login -> query -> response funciona
- [ ] Documentacion del proceso de transporte (reproducible)
- [ ] Checklist validacion QAS completado

## Archivos a crear/modificar

- `docs/deployment/transport-dev-to-qas.md` (crear)
- `docs/deployment/qas-validation-checklist.md` (crear)

## Decisiones de diseno

- **Helm-based transport**: Misma herramienta, diferentes values.
- **pg_dump para data**: Confiable para volumen pequeno.
- **Proceso documentado**: Reproducible para QAS -> PRD.

## Out of scope

- Automatizacion completa del transporte
- Datos produccion en QAS

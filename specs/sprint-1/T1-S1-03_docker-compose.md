# T1-S1-03: Docker Compose para desarrollo local

## Meta


| Campo           | Valor                                                                               |
| --------------- | ----------------------------------------------------------------------------------- |
| Track           | T1 (Franco, Agus)                                                                   |
| Prioridad       | Critica                                                                             |
| Estado          | done                                                                                |
| Bloqueante para | T2-S1-01 (necesita PG+Redis), T3-S1-01                                              |
| Depende de      | T1-S1-01                                                                            |
| Skill           | `docker-deployment/SKILL.md` + `docker-deployment/references/compose-full-stack.md` |
| Estimacion      | M (2-4h)                                                                            |


## Contexto

Los devs necesitan levantar PostgreSQL con pgvector y Redis localmente para desarrollar. Langfuse y Airflow se usan del cluster K8s compartido, NO se levantan localmente.

## Spec

Crear `docker-compose.yml` en la raiz del proyecto con los servicios de persistencia para desarrollo local. Solo PG+Redis. El compose debe ser minimalista y arrancar rapido.

## Acceptance Criteria

- [x] `docker-compose.yml` con: PostgreSQL 16 (con pgvector), Redis 7
- [x] pgvector extension habilitada via init script (`CREATE EXTENSION IF NOT EXISTS vector;`)
- [x] Volumen persistente para Postgres
- [x] Health checks para todos los servicios
- [x] `.env.example` con todas las variables documentadas (incluyendo URLs de Langfuse y Airflow del cluster)
- [x] `docker compose up` levanta PG+Redis sin errores
- [x] Postgres accesible en localhost:5432, Redis en localhost:6379
- [x] Documentacion en `.env.example`: como conectarse a Langfuse y Airflow del cluster compartido desde local

## Archivos a crear/modificar

- `docker-compose.yml` (crear)
- `scripts/init-db.sql` (crear — init script para pgvector extension)
- `.env.example` (crear)

## Decisiones de diseno

- Solo PG+Redis local: Langfuse y Airflow consumen muchos recursos, se usan del cluster compartido
- PostgreSQL 16: version LTS, soporte completo pgvector 0.8+
- Volumen nombrado (no bind mount): mas portable entre devs

## Out of scope

- Dockerfile de la aplicacion (spec T1-S3-01)
- Schema de tablas (spec T1-S1-04)
- Configuracion de Langfuse local (se usa del cluster)
- Configuracion de Airflow local (se usa del cluster)


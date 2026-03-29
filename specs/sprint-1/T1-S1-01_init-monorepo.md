# T1-S1-01: Inicializar monorepo con UV y pyproject.toml

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco, Agus) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T1-S1-02, T1-S1-03, T1-S1-05, todos los tracks |
| Depende de | - |
| Skill | `docker-deployment/SKILL.md` > Seccion "Dependencias" |
| Estimacion | M (2-4h) |

## Contexto

Es la primera tarea del proyecto. Sin el monorepo inicializado, ningun track puede arrancar. Define la estructura de dependencias y el package manager para todo el equipo.

## Spec

Inicializar el repositorio con `uv`, Python 3.12, y definir la estructura de dependencias del proyecto. El monorepo contiene backend Python + frontend Next.js + DAGs Airflow + Helm charts.

## Acceptance Criteria

- [x] `pyproject.toml` creado con UV como package manager
- [x] Python 3.12 como version minima
- [x] Grupos de dependencias separados: `[project.dependencies]`, `[project.optional-dependencies.dev]`, `[project.optional-dependencies.test]`
- [x] Dependencias core declaradas: fastapi, uvicorn, sqlalchemy, alembic, pydantic-settings, langchain, langgraph, langfuse, redis, psycopg[binary]
- [x] Dependencias Airflow DAGs: apache-airflow>=3.0 (solo para desarrollo/testing de DAGs local)
- [x] `uv sync` ejecuta sin errores
- [x] `.python-version` file creado
- [x] `.gitignore` actualizado para Python + Node.js + Airflow (monorepo)

## Archivos creados/modificados

- `pyproject.toml` (creado)
- `.python-version` (creado)
- `.gitignore` (creado)
- `uv.lock` (generado)

## Decisiones de diseno

- UV sobre Poetry/pip: mas rapido, mejor resolusion de deps, soporte nativo de workspaces
- Monorepo sobre multirepo: equipo pequeno, deploys coordinados, skills compartidas

## Out of scope

- Configuracion de frontend (Next.js se inicializa en Sprint 3)
- Docker files (spec T1-S1-03)
- CI pipeline (spec T1-S1-05)

## Notas de completado

Completada el 13/02/2026. Commit: `97350d0 T1-S1-01 completada`.

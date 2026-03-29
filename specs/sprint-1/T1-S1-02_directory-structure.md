# T1-S1-02: Crear estructura de directorios hexagonal

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco, Agus) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T2-S1-01, T3-S1-01, T4-S1-01, T4-S1-02 |
| Depende de | T1-S1-01 |
| Skill | `database-setup/SKILL.md` > Seccion "Arquitectura Hexagonal" |
| Estimacion | M (2-4h) |

## Contexto

Define el arbol de directorios que todos los tracks usaran. Sin esta estructura, los demas tracks no saben donde colocar su codigo. Sigue el arbol autorativo definido en `.claude/instructions.md`.

## Spec

Crear la estructura de directorios Clean/Hexagonal con las 4 capas: Domain, Application, Infrastructure, Presentation. Incluye tambien directorios para tests, DAGs de Airflow, frontend, Helm charts y Docker.

## Acceptance Criteria

- [x] Estructura creada alineada con arbol autorativo de `instructions.md`:
  ```
  src/
  ├── domain/
  │   ├── entities/
  │   ├── repositories/    # Interfaces (Protocol classes)
  │   └── services/
  ├── application/
  │   ├── use_cases/
  │   │   ├── auth/
  │   │   ├── documents/
  │   │   ├── rag/
  │   │   └── admin/
  │   ├── dtos/
  │   ├── graphs/          # LangGraph
  │   │   └── nodes/
  │   └── services/
  ├── infrastructure/
  │   ├── api/
  │   │   ├── middleware/
  │   │   ├── v1/
  │   │   ├── main.py
  │   │   └── dependencies.py
  │   ├── database/
  │   │   ├── models/
  │   │   └── repositories/
  │   ├── rag/
  │   │   ├── chunking/
  │   │   ├── embeddings/
  │   │   ├── vector_store/
  │   │   ├── retrieval/
  │   │   └── loaders/
  │   ├── llm/
  │   │   └── prompts/templates/
  │   ├── cache/
  │   ├── security/
  │   │   ├── guardrails/
  │   │   └── security_mirror/
  │   └── observability/
  ├── config/
  └── shared/
  ```
- [x] Directorios adicionales: `alembic/`, `dags/`, `tests/`, `frontend/`, `helm/`, `docker/`
- [x] Archivos `__init__.py` en todos los paquetes Python
- [x] `src/` registrado como package en `pyproject.toml`

## Archivos creados/modificados

- `src/**/__init__.py` (creados)
- `tests/`, `dags/`, `frontend/`, `helm/`, `docker/` (creados)

## Decisiones de diseno

- Clean/Hexagonal sobre MVC: mejor separacion de concerns para un sistema con multiples pipelines (API, Airflow, evaluacion)
- `src/` como paquete raiz: evita conflictos de imports, alinea con estandar UV

## Out of scope

- Contenido de los archivos (solo estructura vacia)
- Configuracion de Docker (spec T1-S1-03)
- Schema de base de datos (spec T1-S1-04)

## Notas de completado

Completada el 13/02/2026. Commit: `8386438 T1-S1-02 completado`.

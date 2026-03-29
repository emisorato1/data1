# ADR-011: Backend Python en la Raíz del Monorepo

## Status

**Accepted**

## Date

2026-02-18

## Context

El monorepo contiene dos ecosistemas de runtime: Python (backend, DAGs, scripts) y Node.js (frontend Next.js). Debemos definir cómo se organizan físicamente en el repositorio.

La pregunta concreta es: ¿el backend Python vive en la raíz del proyecto o en un subdirectorio `backend/`?

### Fuerzas en juego

- **Proporción de código**: Python es ~80% del proyecto (backend, DAGs, scripts, tests). Node.js es ~20% (frontend)
- **Dependencias compartidas**: Los DAGs de Airflow importan código de `src/` (`IndexingService`, modelos, etc.)
- **Tooling Python**: UV, ruff, mypy, pytest, alembic — todos asumen que la raíz es el proyecto Python
- **Simetría**: Tener el frontend en `frontend/` pero el backend "suelto" en la raíz es asimétrico
- **Onboarding**: Un nuevo dev debe entender rápidamente dónde está cada cosa
- **Timeline**: El proyecto ya está inicializado con esta estructura (T1-S1-01, T1-S1-02 completados)

## Considered Options

### Opción 1: Backend en la raíz (layout actual)

```
enterprise-ai-platform/     ← ES el proyecto Python
├── pyproject.toml
├── src/
├── tests/
├── alembic/
├── dags/                   ← Comparte ecosistema Python
├── frontend/               ← Subdirectorio aislado (Node.js)
├── helm/
├── docs/
└── specs/
```

**Pros:**
- Convención estándar de UV/Poetry: `pyproject.toml` en raíz, `src/` layout
- DAGs importan `src/` sin configuración extra de PYTHONPATH
- `uv sync`, `pytest`, `ruff check`, `mypy src/`, `alembic upgrade head` — todo funciona con paths por defecto
- Docker build context simple (`.` como context para backend)
- CI estándar sin paths custom
- Ya implementado y funcionando (T1-S1-01, T1-S1-02)

**Contras:**
- Asimétrico: el backend no tiene "su carpeta" como el frontend
- La raíz mezcla archivos del backend (`pyproject.toml`, `uv.lock`) con archivos del proyecto (`docs/`, `specs/`, `helm/`)
- Para un nuevo dev puede no ser obvio que "la raíz ES el backend"

### Opción 2: Todo en subdirectorios (layout simétrico)

```
enterprise-ai-platform/     ← Solo orquestación
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   ├── tests/
│   └── alembic/
├── frontend/
│   ├── package.json
│   └── app/
├── dags/
├── helm/
├── docs/
└── specs/
```

**Pros:**
- Simétrico: cada componente en su carpeta
- Más claro para nuevos devs: "el backend está en `backend/`"
- Separación visual limpia entre componentes

**Contras:**
- Requiere migrar estructura existente (pyproject.toml, alembic.ini, paths en CI, Dockerfiles, skills, specs)
- UV workspace configuration necesaria (`[tool.uv.workspace]` o `root` adjustment)
- DAGs necesitan `backend/src/` en PYTHONPATH para importar `IndexingService`
- Airflow GCS sync necesita configuración adicional para resolver imports
- pytest, ruff, mypy necesitan paths explícitos (`pytest backend/tests/`)
- Docker build context cambia a `backend/` — pero necesita acceso a `dags/` para shared code
- Alembic paths de migración cambian
- Todos los skills (17) y specs (44) que referencian `src/` deben actualizarse
- Overhead de migración sin beneficio funcional para MVP

## Decision

**Backend en la raíz (Opción 1).**

La raíz del monorepo es el proyecto Python. `frontend/`, `helm/`, `docs/`, y `specs/` son subdirectorios que viven dentro del proyecto Python. Esta es la convención estándar de UV y la más pragmática dado que:

1. Python es el 80% del codebase
2. Los DAGs comparten el ecosistema Python del backend
3. Todo el tooling funciona con paths por defecto
4. El proyecto ya está configurado así
5. La migración a Opción 2 tiene costo alto sin beneficio funcional

### Modelo mental correcto

```
enterprise-ai-platform/     ← "Este ES el backend Python"
├── pyproject.toml           │
├── src/                     │  Monolito modular Python
├── tests/                   │
├── alembic/                 │
├── dags/                    │  (comparte ecosistema Python)
│
├── frontend/                ← Subdirectorio Node.js (ciudadano independiente)
├── helm/                    ← Subdirectorio infra
├── docs/                    ← Subdirectorio documentación
└── specs/                   ← Subdirectorio specs
```

## Consequences

### Positivas

- Zero configuración extra para UV, pytest, ruff, mypy, alembic
- DAGs importan `src/` nativamente
- Docker build context simple
- CI con paths estándar
- No hay migración: la estructura ya existe y funciona

### Negativas

- Asimetría visual (backend en raíz, frontend en subdirectorio)
- Nuevos devs necesitan entender que "la raíz es el backend" (documentar en README/onboarding)
- Si en el futuro se agregan más servicios Python, la raíz se vuelve ambigua

### Trigger de reconsideración

Migrar a Opción 2 (subdirectorios) si:
- Se agregan 2+ servicios Python independientes (no el caso actual)
- El equipo crece a 20+ personas y necesitan ownership clara por directorio
- Se adopta un framework de monorepo (Nx, Turborepo) que requiere subdirectorios

## Related

- [ADR-001](ADR-001-modular-monolith.md) — Monolito Modular Hexagonal (justifica un solo proceso Python)
- [ADR-005](ADR-005-airflow-separated-indexing.md) — Airflow separado (los DAGs comparten deps con el backend)

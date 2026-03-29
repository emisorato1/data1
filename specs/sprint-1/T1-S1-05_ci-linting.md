# T1-S1-05: CI basico (linting + type checking)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | T1-S1-01 |
| Skill | `testing-strategy/SKILL.md` > Seccion "CI" |
| Estimacion | M (2-4h) |

## Contexto

Pipeline minimo para mantener calidad de codigo desde dia 1. Si no se establece temprano, la deuda tecnica se acumula rapido con 7-8 personas trabajando en paralelo.

## Spec

Configurar linting con Ruff, type checking con mypy, y un pipeline CI que ejecute en cada push/PR. Pre-commit hooks opcionales para validacion local.

## Acceptance Criteria

- [x] GitHub Actions workflow configurado (`.github/workflows/ci.yml`)
- [x] Ruff (linter + formatter) configurado en `pyproject.toml`
  - Rules: `["E", "F", "W", "I", "N", "UP", "B", "SIM"]`
  - Target: Python 3.12
  - Line length: 120
- [x] mypy configurado para type checking basico en `pyproject.toml`
  - `strict = false` (se endurece gradualmente)
  - `ignore_missing_imports = true` (por ahora)
- [x] Pipeline ejecuta en cada push/PR: `ruff check`, `ruff format --check`, `mypy src/`
- [x] Pre-commit hooks opcionales configurados (`.pre-commit-config.yaml`)
- [x] Pipeline pasa en el estado actual del repo

## Archivos a crear/modificar

- `.github/workflows/ci.yml` (crear)
- `pyproject.toml` (modificar — agregar seccion `[tool.ruff]` y `[tool.mypy]`)
- `.pre-commit-config.yaml` (crear)

## Decisiones de diseno

- Ruff sobre flake8+black+isort: una sola herramienta, 10-100x mas rapida
- mypy no estricto por ahora: el equipo puede ir habilitando checks gradualmente
- Pre-commit como opcional: no forzar en el equipo, pero disponible

## Out of scope

- Tests en CI (se agregan cuando haya tests en Sprint 2-3)
- CD / deploy automatico (post-MVP)
- Docker build en CI

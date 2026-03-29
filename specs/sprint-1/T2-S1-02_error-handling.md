# T2-S1-02: Excepciones personalizadas y error handling base

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Branko) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | Todos los tracks (usan estas excepciones) |
| Depende de | T2-S1-01 |
| Skill | `error-handling/SKILL.md` + `error-handling/references/exception-definitions.md` |
| Estimacion | M (2-4h) |

## Contexto

Jerarquia de excepciones del dominio y handlers que todos los tracks usaran. Sin excepciones estandarizadas, cada track inventa su propio manejo de errores y el frontend recibe formatos inconsistentes.

## Spec

Crear la jerarquia de excepciones custom del proyecto con una clase base `AppError` y excepciones especificas por dominio. Integrar con los exception handlers de FastAPI para convertir automaticamente excepciones en responses JSON estandarizados.

## Acceptance Criteria

- [x] Clase base `AppError(Exception)` con atributos: `code` (str), `message` (str), `status_code` (int)
- [x] Excepciones especificas:
  - `NotFoundError` (404)
  - `AuthenticationError` (401)
  - `AuthorizationError` (403)
  - `ValidationError` (422)
  - `RateLimitError` (429)
  - `ExternalServiceError` (502)
  - `PipelineError` (500)
- [x] Handler global en FastAPI que convierte `AppError` -> response JSON estandarizado:
  ```json
  {"data": null, "error": {"code": "NOT_FOUND", "message": "..."}, "meta": {}}
  ```
- [x] Logging automatico de errores 5xx con structlog (o logging estandar si structlog no esta aun)
- [x] Errores no exponen stack traces ni datos internos en produccion (controlado via `Settings.debug`)
- [x] Tests unitarios para cada excepcion y handler

## Archivos a crear/modificar

- `src/shared/exceptions.py` (modificar — expandir la base creada en T2-S1-01)
- `src/infrastructure/api/main.py` (modificar — registrar handlers)
- `tests/unit/test_exceptions.py` (crear)
- `tests/unit/test_error_handlers.py` (crear)

## Decisiones de diseno

- Jerarquia plana (no mas de 2 niveles): `AppError` -> `NotFoundError`, etc. Sin sub-jerarquias innecesarias
- `code` como string enum-like (ej: `"NOT_FOUND"`, `"AUTH_FAILED"`): mas legible que codigos numericos para el frontend
- Logging solo de 5xx: los 4xx son errores del cliente, no del sistema

## Out of scope

- Circuit breaker para servicios externos (post-MVP)
- Retry logic (cada servicio lo implementa segun su spec)
- Excepciones de Airflow DAGs (se manejan dentro del contexto de Airflow)

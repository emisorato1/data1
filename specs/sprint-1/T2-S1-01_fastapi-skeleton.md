# T2-S1-01: FastAPI skeleton con health checks y config

## Meta


| Campo           | Valor                                             |
| --------------- | ------------------------------------------------- |
| Track           | T2 (Ema, Branko)                                  |
| Prioridad       | Critica                                           |
| Estado          | done                                              |
| Bloqueante para | T2-S1-02, T2-S2-01, T2-S2-02, T2-S2-03            |
| Depende de      | T1-S1-02                                          |
| Skill           | `api-design/SKILL.md` + `error-handling/SKILL.md` |
| Estimacion      | L (4-8h)                                          |


## Contexto

El punto de entrada de la aplicacion. Todo el backend pasa por FastAPI. Sin este skeleton, ningun endpoint se puede implementar. Debe incluir el factory pattern, configuracion centralizada y health checks para verificar que la infra esta levantada.

## Spec

Crear la aplicacion FastAPI con factory pattern (`create_app()`), configuracion via Pydantic BaseSettings, health checks, exception handlers globales y response schema estandarizado.

## Acceptance Criteria

- [x] `src/infrastructure/api/main.py` con factory pattern (`create_app()`)
- [x] Lifespan handler para startup/shutdown (conexion DB, Redis)
- [x] Pydantic `BaseSettings` en `src/config/settings.py` con validacion estricta
- [x] Variables configuradas:
  - [x] `DATABASE_URL`
  - [x] `REDIS_URL`
  - [x] `JWT_SECRET`
  - [x] `GEMINI_API_KEY`
  - [x] `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`
  - [x] `AIRFLOW_API_URL`
- [x] Endpoint `GET /health` retorna `{"status": "ok", "version": "0.1.0"}`
- [x] Endpoint `GET /health/ready` verifica conectividad a Postgres y Redis
- [x] Exception handlers globales: 404, 422 (validation), 500 (generic)
- [x] Response schema estandarizado: `{"data": ..., "error": ..., "meta": ...}`
- [x] CORS middleware configurado (origenes parametrizables)
- [x] `uvicorn` arranca la app sin errores

## Archivos a crear/modificar

- `src/infrastructure/api/main.py` (crear)
- `src/infrastructure/api/dependencies.py` (crear)
- `src/infrastructure/api/v1/health.py` (crear)
- `src/config/settings.py` (crear)
- `src/shared/exceptions.py` (crear — base minima, se expande en T2-S1-02)

## Decisiones de diseno

- Factory pattern: permite multiples configuraciones (test, dev, prod) e inyeccion de dependencias
- Pydantic BaseSettings con `model_config = SettingsConfigDict(env_file=".env")`: validacion estricta de config
- Response schema unico: consistencia para el frontend, facilita error handling

## Out of scope

- Auth middleware (spec T2-S2-01)
- Rate limiting (spec T2-S4-01)
- Security headers avanzados (spec T2-S2-02)
- Endpoints de negocio (specs de Sprint 2+)
- Logging estructurado con structlog (spec T1-S2-03)


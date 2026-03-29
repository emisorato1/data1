# T2-S7-02: Rate limiting avanzado token bucket por usuario

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Branko) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | - |
| Depende de | T2-S4-01 (done) |
| Skill | `api-design/SKILL.md` |
| Estimacion | M (2-4h) |

> POST-28

## Contexto

The basic rate limiting from Sprint 4 uses a simple counter. For production, a token bucket algorithm provides fairer rate limiting that handles burst traffic while maintaining average rate limits per user.

## Spec

Replace the basic rate limiter with a Redis-backed token bucket implementation, with per-user and per-endpoint configuration.

## Acceptance Criteria

- [x] Token bucket implementado con Redis (atomico via Lua script)
- [x] Configuracion per-user: tokens_per_second, bucket_size
- [x] Configuracion per-endpoint: diferentes limites para chat, upload, admin
- [x] Headers HTTP: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- [x] Response 429 Too Many Requests con Retry-After header
- [x] Usuarios admin tienen limites mas altos (configurable)
- [x] Metricas de rate limiting en logs (requests throttled por usuario)
- [x] Tests: burst handling, refill rate, per-user isolation

## Archivos a crear/modificar

- `src/api/middleware/rate_limiter.py` (modificar — reemplazar implementacion)
- `src/infrastructure/cache/token_bucket.py` (crear)
- `tests/unit/test_token_bucket.py` (crear)

## Decisiones de diseno

- **Token bucket sobre sliding window**: Permite bursts controlados, mas natural para uso humano
- **Redis Lua script**: Operacion atomica, evita race conditions en ambiente multi-pod
- **Per-endpoint config**: Chat queries son mas costosas que list documents, merecen limites diferentes

## Out of scope

- Rate limiting por IP (solo por usuario autenticado)
- Rate limiting distribuido multi-region
- Quotas mensuales

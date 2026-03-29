# T2-S4-01: Rate limiting basico

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Branko) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | - |
| Depende de | T2-S2-01 |
| Skill | `authentication/SKILL.md` > Seccion "Rate Limiting" |
| Estimacion | M (2-4h) |

## Contexto

Proteccion contra abuso de la API. Especialmente importante para el endpoint de chat que consume recursos LLM costosos. Sin rate limiting, un usuario malicioso o un bug en el frontend puede generar costos excesivos.

## Spec

Implementar rate limiting con Redis sliding window: por IP para endpoints publicos y por usuario para endpoints autenticados.

## Acceptance Criteria

- [x] Rate limit por IP: 100 requests/minuto para endpoints publicos
- [x] Rate limit por usuario: 30 requests/minuto para endpoint de chat
- [x] Response `429 Too Many Requests` con header `Retry-After`
- [x] Implementacion con Redis (sliding window)
- [x] Configurable via settings
- [x] Tests que verifican limites

## Archivos a crear/modificar

- `src/infrastructure/api/middleware/rate_limit.py` (crear)
- `src/infrastructure/cache/redis_client.py` (crear o modificar)
- `tests/unit/test_rate_limiting.py` (crear)

## Decisiones de diseno

- Redis sliding window sobre fixed window: distribucion mas uniforme, sin burst al inicio de ventana
- Limites separados IP vs usuario: endpoints publicos (login) por IP, chat por usuario autenticado
- 30 req/min para chat: ~1 query cada 2 segundos, suficiente para uso normal

## Out of scope

- Token bucket avanzado (post-MVP)
- Rate limiting por tenant/organizacion (post-MVP)
- Rate limiting adaptativo basado en carga (post-MVP)

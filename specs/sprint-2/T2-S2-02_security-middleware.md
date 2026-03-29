# T2-S2-02: Middleware de seguridad global

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Branko) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | T2-S1-01 |
| Skill | `api-design/SKILL.md` + `api-design/references/middleware-implementations.md` |
| Estimacion | M (2-4h) |

## Contexto

Capa de proteccion que aplica a todos los requests. Los security headers y validaciones basicas deben estar desde dia 1 para que el sistema pase auditorias de seguridad bancaria.

## Spec

Implementar middlewares de seguridad que apliquen globalmente: CORS, security headers, trusted host validation, request size limit, y logging de requests.

## Acceptance Criteria

- [x] CORS configurado con origenes permitidos desde settings
- [x] Security headers en todas las responses:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- [x] Trusted Host middleware (previene host header injection)
- [x] Request size limit (default 10MB)
- [x] Middleware de logging que registra: method, path, status, duration, user_id
- [x] Tests que verifican headers en responses

## Archivos a crear/modificar

- `src/infrastructure/api/middleware/cors.py` (crear)
- `src/infrastructure/api/middleware/auth.py` (crear — placeholder, se completa con T2-S2-01)
- `src/infrastructure/api/main.py` (modificar — registrar middlewares)
- `tests/unit/test_security_middleware.py` (crear)

## Decisiones de diseno

- Middleware sobre decoradores: aplica globalmente, no se puede olvidar en un endpoint
- Security headers hardcoded (no configurables): estos valores son best practice, no hay razon para cambiarlos

## Out of scope

- Rate limiting (spec T2-S4-01)
- WAF / DDoS protection (infraestructura GCP)
- CSP headers (se agregan cuando haya frontend)

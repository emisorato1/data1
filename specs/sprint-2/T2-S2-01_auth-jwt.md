# T2-S2-01: Auth completa (JWT + refresh tokens)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T2 (Ema, Branko) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T2-S2-03, T2-S3-01, T5-S3-01 |
| Depende de | T1-S1-04 |
| Skill | `authentication/SKILL.md` + `authentication/references/owasp-mapping.md` |
| Estimacion | XL (8h+) |

## Contexto

Sistema de autenticacion completo para el MVP. Todos los endpoints de negocio requieren JWT valido. Sin auth, el sistema no puede ir a produccion ni pasar auditorias bancarias.

## Spec

Implementar flujo completo de autenticacion con JWT en HTTPOnly cookies, refresh tokens rotativos, y dependencia FastAPI `get_current_user` para proteger endpoints.

## Acceptance Criteria

- [x] `POST /api/v1/auth/login` - Retorna access_token (15min) + refresh_token (7d) en HTTPOnly cookies
- [x] `POST /api/v1/auth/logout` - Invalida refresh token en DB
- [x] `POST /api/v1/auth/refresh` - Rota refresh token y emite nuevo access_token
- [x] Hashing con bcrypt (cost factor 12)
- [x] JWT con HS256, claims: `sub` (user_id), `exp`, `iat`, `role`
- [x] Dependencia FastAPI `get_current_user` que valida JWT y retorna User
- [x] Tabla `users` con seed de usuario admin para desarrollo
- [x] Tests unitarios + test de integracion (login -> refresh -> logout flow)

## Archivos a crear/modificar

- `src/infrastructure/security/jwt.py` (crear)
- `src/infrastructure/security/password.py` (crear)
- `src/infrastructure/security/refresh_token.py` (crear)
- `src/infrastructure/api/v1/auth.py` (crear)
- `src/infrastructure/api/dependencies.py` (modificar — agregar get_current_user)
- `src/application/use_cases/auth/login.py` (crear)
- `src/application/use_cases/auth/logout.py` (crear)
- `src/application/use_cases/auth/refresh.py` (crear)
- `src/application/dtos/auth_dtos.py` (crear)
- `tests/unit/test_jwt.py` (crear)
- `tests/unit/test_password.py` (crear)
- `tests/integration/test_auth_flow.py` (crear)

## Decisiones de diseno

- HTTPOnly cookies sobre Authorization header: previene XSS token theft
- Refresh token rotativo: cada uso invalida el anterior, detecta reuso (posible robo)
- bcrypt cost 12: balance seguridad/performance para login
- HS256 sobre RS256: simplicidad para MVP, se puede migrar despues

## Out of scope

- RBAC granular (post-MVP, solo roles basicos admin/user)
- OAuth2/SSO (post-MVP)
- MFA (post-MVP)
- Rate limiting en auth (spec T2-S4-01)

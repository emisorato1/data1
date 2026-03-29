# ADR-006: JWT con HTTPOnly Cookies y Refresh Tokens

## Status

**Accepted**

## Date

2026-02-13

## Context

El sistema requiere autenticación para proteger:
- Endpoints de chat RAG (información bancaria sensible)
- Conversaciones privadas de cada usuario
- Panel de administración (post-MVP)
- Cumplimiento con auditoría bancaria (trazabilidad por usuario)

El frontend es una SPA Next.js que se comunica con FastAPI vía REST + SSE.

## Considered Options

### Opción 1: JWT en HTTPOnly cookies + Refresh tokens en DB

- Access token (JWT, 15min) almacenado en cookie HTTPOnly
- Refresh token (opaco, 7 días) almacenado en DB y cookie HTTPOnly
- Rotación de refresh tokens en cada uso

### Opción 2: JWT en localStorage + Bearer header

- Access token almacenado en localStorage del browser
- Enviado como `Authorization: Bearer <token>`

### Opción 3: Session-based (server-side sessions)

- Session ID en cookie
- Estado de sesión almacenado en Redis

### Opción 4: OAuth 2.0 / OpenID Connect (delegado)

- Autenticación delegada a un Identity Provider externo

## Decision

**JWT en HTTPOnly cookies + Refresh tokens en DB (Opción 1).**

### Flujo de autenticación

```
1. Login: POST /api/v1/auth/login {email, password}
   ← Set-Cookie: access_token=<JWT>; HttpOnly; Secure; SameSite=Strict; Max-Age=900
   ← Set-Cookie: refresh_token=<opaque>; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh

2. Request autenticado: GET /api/v1/conversations
   → Cookie: access_token=<JWT>
   ← 200 OK

3. Token expirado: GET /api/v1/conversations
   → Cookie: access_token=<expired JWT>
   ← 401 Unauthorized

4. Refresh: POST /api/v1/auth/refresh
   → Cookie: refresh_token=<opaque>
   ← Set-Cookie: access_token=<new JWT>; ...
   ← Set-Cookie: refresh_token=<new opaque>; ...  (rotación)

5. Logout: POST /api/v1/auth/logout
   → Cookie: refresh_token=<opaque>
   ← Refresh token invalidado en DB
   ← Set-Cookie: access_token=; Max-Age=0
   ← Set-Cookie: refresh_token=; Max-Age=0
```

### Configuración JWT

| Parámetro | Valor |
|-----------|-------|
| Algoritmo | HS256 |
| TTL access token | 15 minutos |
| TTL refresh token | 7 días |
| Claims | `sub` (user_id), `exp`, `iat`, `role` |
| Password hashing | bcrypt (cost factor 12) |
| Cookie flags | `HttpOnly`, `Secure`, `SameSite=Strict` |

### Justificación sobre alternativas

| Criterio | HTTPOnly Cookie | localStorage | Sessions | OAuth |
|----------|----------------|-------------|----------|-------|
| XSS protection | Sí (JS no puede leer la cookie) | No (vulnerable) | Sí | Sí |
| CSRF protection | SameSite=Strict | N/A | Requiere token | Delegado |
| SSE compatible | Sí (cookies enviadas automáticamente) | No (no se puede enviar Bearer en EventSource) | Sí | Complejo |
| Stateless server | Sí (JWT self-contained) | Sí | No (Redis) | Delegado |
| Complejidad | Media | Baja (pero inseguro) | Media | Alta (IdP externo) |
| Auditoría bancaria | `sub` claim = trazabilidad | Igual | Session ID | Delegado |

**Razón crítica**: `EventSource` (API nativa de SSE) **no soporta headers custom**. Si usáramos Bearer tokens en localStorage, el streaming SSE no funcionaría sin workarounds. HTTPOnly cookies se envían automáticamente con cada request, incluyendo SSE.

## Consequences

### Positivas

- Protección contra XSS: JavaScript no puede acceder a los tokens
- SSE nativo: cookies se envían automáticamente con EventSource
- Stateless: FastAPI no necesita almacenar sesiones (solo refresh tokens en DB)
- Rotación de refresh tokens: cada uso emite uno nuevo, el anterior se invalida
- CSRF protection con `SameSite=Strict`
- Trazabilidad: `user_id` en JWT claims para audit logs

### Negativas

- Complejidad de implementación mayor que Bearer token simple
- Refresh token en DB requiere tabla y lógica de rotación/invalidación
- Cookies tienen límite de ~4KB (suficiente para JWT)
- Cross-domain requiere configuración de `SameSite` y CORS cuidadosa

## References

- OWASP: [JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- OWASP: [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- Skill: `.claude/skills/authentication/SKILL.md`

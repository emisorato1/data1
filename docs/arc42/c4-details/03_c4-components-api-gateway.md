# Enterprise AI Platform – API Gateway

## 1. Visión General

**Diagrama de referencia:** `docs/arc42/diagrams/03-c4-contenedor-api-gateway.drawio.svg`

---

La **API Gateway** es el punto de entrada principal de la Enterprise AI Platform.  
Expone interfaces REST y de comunicación en tiempo real para usuarios humanos y sistemas técnicos, garantizando seguridad, aislamiento por tenant (internos), autorización y observabilidad.

La arquitectura sigue principios de **Clean Architecture** y el **modelo C4**, asegurando una clara separación de responsabilidades y una evolución controlada del sistema.

### Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework Web | FastAPI | 0.109+ |
| Runtime | Python | 3.11+ |
| Base de Datos | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ |
| Validación | Pydantic | 2.0+ |
| Autenticación | python-jose (JWT) | 3.3+ |
| WebSocket | Starlette WebSockets | - |

---

## 2. Principios y Decisiones de Diseño

| Principio | Descripción | Justificación |
|-----------|-------------|---------------|
| **Clean Architecture** | Separación en capas (Presentación, Aplicación, Dominio, Infraestructura) | Facilita testing, mantenibilidad y evolución independiente |
| **Stateless API** | Sin estado en el servidor entre requests | Escalabilidad horizontal y resiliencia |
| **Multi-tenant por diseño** | Aislamiento de datos por tenant en cada operación | Requisito de negocio para entorno bancario |
| **Fail-safe** | Errores controlados con respuestas predecibles | Seguridad y experiencia de usuario consistente |
| **Defense in depth** | Múltiples capas de validación y seguridad | Requisito regulatorio para entorno financiero |

---

## 3. Actores y Sistemas Externos

### 3.1 Personas

- **Chat User**  
  Empleado de la organización que interactúa con la interfaz conversacional.

- **Technical User**  
  Usuario técnico o integrador que consume la API directamente para integraciones sistema-a-sistema.

### 3.2 Sistemas Externos

- **RAG Chat Frontend (React)**  
  Interfaz de usuario conversacional que se comunica con la API Gateway vía HTTPS y WebSocket/SSE.

- **OpenText ECM**  
  Sistema de gestión documental corporativo. Actúa como intermediario o fuente de documentos para el usuario antes de interactuar con la plataforma de IA, según el flujo de negocio del banco.

- **RAG Generation Service**  
  Servicio externo encargado de la generación de respuestas mediante técnicas de Retrieval-Augmented Generation (RAG), accedido mediante WebSocket.

- **Observability Stack**  
  Plataforma compuesta por Langfuse, Prometheus y Grafana. Recibe métricas, trazas, latencia y costos exportados principalmente por el middleware y los orquestadores de la API.

- **Base de Datos de Plataforma (PostgreSQL)**  
  Base de datos relacional central para la persistencia de información (User, Conversation, Message, Roles, Auth, Tenant).

- **[TBD] External System / Agente de IA**  
  Sistemas de integración externos o agentes de IA independientes que colaboran con la plataforma invocando sus interfaces programáticas.

- **[TBD] A2A Server (Agent-to-Agent)**  
  Servidor externo para la comunicación entre agentes. Permite que otros agentes automatizados invoquen la API Gateway mediante protocolos estándar (HTTP/WebSocket) para colaboración multi-agente.

- **[TBD] MCP Server**  
  Sistema externo que expone herramientas y acciones. Se conecta mediante el protocolo MCP utilizando transportes como **STDIO** o **SSE** (Server-Sent Events).

---

## 4. API Gateway (Contenedor)

**Tecnología:** FastAPI (Python)

**Responsabilidad:**  
Actúa como frontera del sistema, exponiendo las APIs, aplicando controles de seguridad y orquestando los flujos de la aplicación.

---

## 5. Capa de Presentación

La capa de presentación gestiona todas las solicitudes entrantes y define el límite de transporte del sistema.

### 5.1 Middleware Pipeline

**Responsabilidades:**
- Validación de JWT (access tokens)
- Resolución de tenant
- Rate limiting
- Propagación de trace_id
- **Emisión de métricas HTTP**: Envío automático de latencia y códigos de estado al Observability Stack
- Bloqueo de solicitudes no autorizadas (401 / 403 / 429)

La validación de JWT se realiza aquí antes de que la solicitud alcance a los controladores.

**Orden de ejecución (de afuera hacia adentro):**

| # | Middleware | Responsabilidad |
|---|------------|-----------------|
| 1 | CORS Middleware | Validar origen de solicitudes cross-origin |
| 2 | Trusted Host Middleware | Validar header Host contra lista permitida |
| 3 | HTTPS Redirect Middleware | Redirigir HTTP a HTTPS (producción) |
| 4 | GZip Middleware | Comprimir respuestas > 500 bytes |
| 5 | Request ID Middleware | Generar/propagar X-Request-ID |
| 6 | Rate Limiting Middleware | Aplicar límites por IP/usuario/tenant |
| 7 | Authentication Middleware | Validar JWT y extraer claims |
| 8 | Tenant Resolution Middleware | Resolver y validar tenant del usuario |
| 9 | Metrics Middleware | Registrar latencia y códigos de respuesta |

**Tecnología FastAPI:**
- Uso del decorador `@app.middleware("http")` para middleware custom
- `CORSMiddleware` de `fastapi.middleware.cors`
- Starlette middlewares compatibles

---

### 5.2 Router

**Responsabilidades:**
- Enrutamiento de solicitudes HTTP hacia el controlador correspondiente según la URL, método y versión de la API
- No contiene lógica de negocio

**Estrategia de Versionado:**

| Aspecto | Configuración |
|---------|---------------|
| Método | URL path prefix (`/api/v1/`, `/api/v2/`) |
| Deprecación | Header `Deprecation` con fecha de sunset |
| Compatibilidad | Mínimo 6 meses de soporte para versiones deprecadas |

---

### 5.3 Controllers

Los controladores representan el límite entre el transporte y la lógica de aplicación.

| Controller | Endpoints | Responsabilidad |
|------------|-----------|-----------------|
| Auth Controller | `/auth/*` | Login, logout, refresh token, API keys |
| Chat Controller | `/chat/*` | Envío de mensajes, streaming |
| Conversation Controller | `/conversations/*` | CRUD de conversaciones |
| User Controller | `/users/*` | Gestión de usuarios y perfiles |
| Health Controller | `/health/*` | Health checks |

**Responsabilidades:**
- Recepción de solicitudes
- Validación de entrada mediante esquemas Pydantic
- Delegación de la ejecución a la capa de aplicación
- Formateo de respuestas

---

### 5.4 Endpoints WebSocket / SSE

**Responsabilidades:**
- Gestión de comunicación en tiempo real
- Manejo de conexiones persistentes
- Delegación del flujo conversacional a la capa de aplicación (Chat Orchestrator)
- Heartbeat para detección de conexiones muertas

**Configuración WebSocket:**

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| Ping interval | 30s | Intervalo de ping para mantener conexión |
| Ping timeout | 10s | Timeout para respuesta de pong |
| Max message size | 64KB | Tamaño máximo de mensaje |
| Close timeout | 5s | Timeout para cierre graceful |

---

### 5.5 Request/Response Schemas (DTO)

**Responsabilidades:**
- Definir la estructura de las solicitudes y respuestas
- Validar los datos de entrada con Pydantic
- Actuar como artefactos pasivos utilizados por los controladores
- Documentar automáticamente la API via OpenAPI

---

## 6. Capa de Aplicación

La capa de aplicación implementa los casos de uso del sistema y orquesta los flujos entre dominio e infraestructura.

### 6.1 Auth Use Cases

**Responsabilidades:**
- Autenticación de usuarios (email/password)
- Emisión de tokens (access y refresh)
- Gestión de sesiones y credenciales
- Revocación de tokens
- Gestión de API keys para usuarios técnicos

**Casos de uso:**

| Use Case | Descripción |
|----------|-------------|
| `LoginUseCase` | Autentica usuario y emite tokens |
| `LogoutUseCase` | Revoca refresh token activo |
| `RefreshTokenUseCase` | Renueva access token con refresh token válido |
| `CreateApiKeyUseCase` | Genera API key para usuario técnico |
| `RevokeApiKeyUseCase` | Revoca API key existente |

---

### 6.2 Conversation Use Cases

**Responsabilidades:**
- Creación y gestión de conversaciones
- Validación de pertenencia al tenant
- Control del ciclo de vida de las conversaciones

**Casos de uso:**

| Use Case | Descripción |
|----------|-------------|
| `CreateConversationUseCase` | Crea nueva conversación para el usuario |
| `GetConversationUseCase` | Obtiene conversación por ID (validando tenant) |
| `ListConversationsUseCase` | Lista conversaciones del usuario |
| `DeleteConversationUseCase` | Elimina conversación (soft delete) |

---

### 6.3 Authorization Policy

**Responsabilidades:**
- Evaluar permisos y scopes
- Aplicar control de acceso basado en roles y scopes (RBAC)
- Autorizar o rechazar la ejecución de casos de uso

Este componente es consultado por los controladores y endpoints en tiempo real.

**Roles definidos:**

| Rol | Descripción | Scopes |
|-----|-------------|--------|
| `user` | Usuario estándar | `read:conversations`, `write:messages` |
| `admin` | Administrador de tenant | `admin:users`, `admin:conversations` |
| `technical_user` | Usuario de integración | `api:full_access` |

---

### 6.4 Chat Orchestrator

**Responsabilidades:**
- Coordinar el flujo completo del chat
- Decidir cuándo invocar al RAG-generation-service
- Manejar respuestas en streaming
- Persistir mensajes y estados
- Emitir información de observabilidad
- [TBD] Decidir cuándo invocar herramientas (MCP y A2A)

Es el componente central de orquestación de la plataforma.

---

## 7. Capa de Dominio

La capa de dominio define los conceptos centrales del negocio, independientes de preocupaciones técnicas.

### Modelo de Dominio

| Entidad | Atributos Principales | Descripción |
|---------|----------------------|-------------|
| **Tenant** | `id`, `name`, `config`, `created_at` | Unidad de negocio aislada |
| **User** | `id`, `email`, `tenant_id`, `role_id`, `status` | Usuario del sistema |
| **Role** | `id`, `name`, `scopes`, `tenant_id` | Rol con permisos asociados |
| **Conversation** | `id`, `user_id`, `tenant_id`, `title`, `status` | Sesión de chat |
| **Message** | `id`, `conversation_id`, `role`, `content`, `metadata` | Mensaje individual |

**Características:**
- Encapsula reglas e invariantes del negocio
- No depende de frameworks, protocolos ni infraestructura
- Validaciones de dominio (ej: usuario solo puede acceder a conversaciones de su tenant)

---

## 8. Capa de Infraestructura

La capa de infraestructura provee las implementaciones técnicas requeridas por la aplicación.

### 8.1 Persistencia (Repositorios)

**Tecnología:** PostgreSQL + SQLAlchemy

**Responsabilidades:**
- Persistir entidades del dominio
- Ejecutar operaciones CRUD
- Proveer acceso a datos con aislamiento por tenant

**Patrón de acceso:**
- Repository pattern para abstracción de persistencia
- Unit of Work para transacciones
- Queries con filtro automático de tenant

---

### 8.2 Auth / Token Store

**Tecnología:** PostgreSQL

**Responsabilidades:**
- Almacenar refresh tokens (hashed)
- Almacenar API keys (hashed con bcrypt)
- Permitir revocación y rotación de credenciales
- Mantener registro de tokens activos por usuario

---

### 8.3 RAG Client

**Tecnología:** WebSocket Client (aiohttp/websockets)

**Responsabilidades:**
- Invocar el servicio de generación RAG
- Manejar streaming de respuestas
- Encapsular detalles de comunicación
- Implementar circuit breaker

**Circuit Breaker:**

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| Failure threshold | 5 | Errores consecutivos para abrir circuito |
| Recovery timeout | 30s | Tiempo antes de intentar half-open |
| Half-open requests | 1 | Requests permitidos en half-open |

---

### 8.4 [TBD] MCP Client

**Tecnología:** Cliente de protocolo MCP

**Responsabilidades:**
- Invocar herramientas externas vía MCP Server
- Manejar la comunicación técnica con herramientas soportando transportes **STDIO** y **SSE**

---

### 8.5 Observability Client

**Responsabilidades:**
- Enviar métricas a Prometheus
- Enviar trazas a Langfuse
- Registrar costos de tokens LLM
- Integrarse con Grafana para dashboards

---

## 9. Contratos de Datos

### 9.1 Autenticación

#### POST /api/v1/auth/login

**Request:**

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `email` | string | Sí | Email válido, max 255 caracteres |
| `password` | string | Sí | Min 8 caracteres |

**Response (200 OK):**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `access_token` | string | JWT con expiración de 15 minutos |
| `refresh_token` | string | Token opaco para renovación |
| `expires_in` | integer | Segundos hasta expiración del access_token |
| `token_type` | string | Siempre "Bearer" |

**Ejemplo:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "expires_in": 900,
  "token_type": "Bearer"
}
```

---

#### POST /api/v1/auth/refresh

**Request:**

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `refresh_token` | string | Sí | Token válido no expirado |

**Response (200 OK):**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `access_token` | string | Nuevo JWT |
| `refresh_token` | string | Nuevo refresh token (rotación) |
| `expires_in` | integer | Segundos hasta expiración |
| `token_type` | string | "Bearer" |

---

### 9.2 Conversaciones

#### POST /api/v1/conversations

**Request:**

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `title` | string | No | Max 255 caracteres |
| `metadata` | object | No | Campos adicionales |

**Response (201 Created):**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | UUID de la conversación |
| `title` | string | Título (auto-generado si no se provee) |
| `created_at` | string | Timestamp ISO 8601 |
| `status` | string | "active" |

---

#### GET /api/v1/conversations

**Query Parameters:**

| Campo | Tipo | Obligatorio | Default | Validación |
|-------|------|-------------|---------|------------|
| `page` | integer | No | 1 | Min 1 |
| `page_size` | integer | No | 20 | Min 1, Max 100 |
| `status` | string | No | "active" | "active", "archived", "all" |

**Response (200 OK):**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `items` | array | Lista de conversaciones |
| `total` | integer | Total de items |
| `page` | integer | Página actual |
| `page_size` | integer | Tamaño de página |
| `pages` | integer | Total de páginas |

---

### 9.3 Chat / Mensajes

#### POST /api/v1/chat/messages

**Request:**

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `conversation_id` | string | No | UUID v4 (crea nueva si no existe) |
| `message` | string | Sí | 1-4000 caracteres |
| `stream` | boolean | No | Default: true |

**Response (200 OK - Streaming SSE):**

Eventos Server-Sent Events:

| Evento | Data | Descripción |
|--------|------|-------------|
| `message` | `{"chunk": "texto..."}` | Fragmento de respuesta |
| `source` | `{"document_id": "...", "title": "...", "snippet": "..."}` | Documento fuente |
| `done` | `{"message_id": "...", "tokens_used": {...}}` | Fin del stream |
| `error` | `{"code": "...", "message": "..."}` | Error durante procesamiento |

**Ejemplo de stream:**

```
event: message
data: {"chunk": "El horario de atención es "}

event: message
data: {"chunk": "de lunes a viernes de 9:00 a 18:00."}

event: source
data: {"document_id": "doc-123", "title": "Manual de Atención", "relevance": 0.92}

event: done
data: {"message_id": "msg-456", "tokens_used": {"input": 150, "output": 45}}
```

---

### 9.4 Health Checks

#### GET /health/live

**Response (200 OK):**

```json
{
  "status": "ok",
  "timestamp": "2026-01-11T10:30:00Z"
}
```

#### GET /health/ready

**Response (200 OK):**

```json
{
  "status": "ok",
  "checks": {
    "database": "ok",
    "rag_service": "ok"
  },
  "timestamp": "2026-01-11T10:30:00Z"
}
```

**Response (503 Service Unavailable):**

```json
{
  "status": "degraded",
  "checks": {
    "database": "ok",
    "rag_service": "error"
  },
  "timestamp": "2026-01-11T10:30:00Z"
}
```

---

## 10. Manejo de Errores y Recuperación

### 10.1 Estructura de Error Response

Todas las respuestas de error siguen el formato RFC 7807 (Problem Details):

```json
{
  "type": "https://api.enterprise-ai.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "El campo 'email' es requerido",
  "instance": "/api/v1/auth/login",
  "errors": [
    {"field": "email", "message": "Este campo es requerido"}
  ],
  "trace_id": "abc123-def456-ghi789",
  "timestamp": "2026-01-11T10:30:00Z"
}
```

### 10.2 Códigos de Error HTTP

| Código | Tipo | Descripción | Acción del Cliente |
|--------|------|-------------|-------------------|
| 400 | Bad Request | Payload malformado o inválido | Corregir formato del request |
| 401 | Unauthorized | Token ausente, expirado o inválido | Re-autenticar |
| 403 | Forbidden | Sin permisos para el recurso | Contactar administrador |
| 404 | Not Found | Recurso no existe | Verificar ID |
| 409 | Conflict | Conflicto de estado (ej: duplicado) | Verificar estado actual |
| 422 | Unprocessable Entity | Validación de negocio falló | Revisar reglas de negocio |
| 429 | Too Many Requests | Rate limit excedido | Esperar según header `Retry-After` |
| 500 | Internal Server Error | Error no manejado | Reportar con `trace_id` |
| 502 | Bad Gateway | RAG Service no disponible | Reintentar con backoff |
| 503 | Service Unavailable | Servicio en mantenimiento | Reintentar según `Retry-After` |
| 504 | Gateway Timeout | Timeout de RAG Service | Reintentar con backoff |

### 10.3 Códigos de Error de Negocio

| Código | HTTP Status | Descripción |
|--------|-------------|-------------|
| `AUTH_INVALID_CREDENTIALS` | 401 | Email o contraseña incorrectos |
| `AUTH_TOKEN_EXPIRED` | 401 | Token JWT expirado |
| `AUTH_TOKEN_REVOKED` | 401 | Refresh token revocado |
| `AUTH_RATE_LIMITED` | 429 | Demasiados intentos de login |
| `CONVERSATION_NOT_FOUND` | 404 | Conversación no existe |
| `CONVERSATION_ACCESS_DENIED` | 403 | Conversación pertenece a otro usuario/tenant |
| `MESSAGE_TOO_LONG` | 422 | Mensaje excede 4000 caracteres |
| `RAG_SERVICE_UNAVAILABLE` | 502 | Servicio RAG no disponible |
| `RAG_TIMEOUT` | 504 | Timeout esperando respuesta de RAG |

### 10.4 Política de Reintentos

| Tipo de Error | Reintentos | Backoff | Timeout Total |
|---------------|------------|---------|---------------|
| RAG timeout (504) | 2 | Exponencial (1s, 2s) | 35s |
| RAG unavailable (502) | 2 | Exponencial (1s, 2s) | 35s |
| Database timeout | 2 | Lineal (500ms) | 5s |
| Errores 4xx | 0 | - | - |

### 10.5 Respuestas de Fallback

| Escenario | Respuesta al Usuario |
|-----------|---------------------|
| RAG Service no disponible | "El servicio de consultas no está disponible en este momento. Por favor, intenta nuevamente en unos minutos." |
| Timeout de RAG | "La consulta está tomando más tiempo del esperado. Por favor, intenta con una pregunta más específica." |
| Error interno | "Ha ocurrido un error inesperado. Por favor, intenta nuevamente. Si el problema persiste, contacta a soporte con el código: {trace_id}" |

---

## 11. Modelo de Seguridad

### 11.1 Autenticación

| Aspecto | Configuración | Justificación |
|---------|---------------|---------------|
| **Algoritmo JWT** | RS256 (RSA con SHA-256) | Asimétrico, permite verificación sin secreto compartido |
| **Expiración Access Token** | 15 minutos | Minimiza ventana de exposición |
| **Expiración Refresh Token** | 7 días | Balance entre seguridad y UX |
| **Rotación de Refresh Token** | En cada uso | Detecta robo de tokens |
| **Almacenamiento de Refresh Token** | PostgreSQL (hashed) | Permite revocación |
| **API Keys** | Prefijo + hash bcrypt | Identificación rápida + seguridad |

**Claims del JWT:**

| Claim | Tipo | Descripción |
|-------|------|-------------|
| `sub` | string | User ID |
| `tenant_id` | string | Tenant ID |
| `role` | string | Rol del usuario |
| `scopes` | array | Permisos del usuario |
| `exp` | integer | Timestamp de expiración |
| `iat` | integer | Timestamp de emisión |
| `jti` | string | ID único del token |

### 11.2 Autorización

| Nivel | Mecanismo | Descripción |
|-------|-----------|-------------|
| **Endpoint** | RBAC | Roles: `user`, `admin`, `technical_user` |
| **Recurso** | Scopes | Permisos granulares (ej: `read:conversations`) |
| **Tenant** | Aislamiento automático | Validación en cada query |
| **Ownership** | Validación de propietario | Usuario solo accede a sus recursos |

### 11.3 Headers de Seguridad

| Header | Valor | Propósito |
|--------|-------|-----------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Forzar HTTPS |
| `X-Content-Type-Options` | `nosniff` | Prevenir MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevenir clickjacking |
| `Content-Security-Policy` | `default-src 'self'` | Prevenir XSS |
| `X-Request-ID` | UUID | Trazabilidad |
| `Cache-Control` | `no-store` | Prevenir cacheo de datos sensibles |

### 11.4 Rate Limiting

| Endpoint | Límite | Ventana | Acción |
|----------|--------|---------|--------|
| `POST /auth/login` | 5 requests | 1 minuto | 429 + bloqueo temporal |
| `POST /auth/refresh` | 10 requests | 1 minuto | 429 |
| `POST /chat/messages` | 30 requests | 1 minuto | 429 |
| `GET /*` | 100 requests | 1 minuto | 429 |
| Global por IP | 1000 requests | 1 minuto | 429 + alerta |

**Headers de Rate Limit:**

| Header | Descripción |
|--------|-------------|
| `X-RateLimit-Limit` | Límite total de la ventana |
| `X-RateLimit-Remaining` | Requests restantes |
| `X-RateLimit-Reset` | Timestamp de reset (Unix) |
| `Retry-After` | Segundos hasta poder reintentar (en 429) |

### 11.5 Protecciones Implementadas

| Amenaza | Mitigación |
|---------|------------|
| **Brute Force** | Rate limiting estricto en `/auth/*`, bloqueo temporal tras 5 intentos |
| **Token Theft** | Refresh token rotation, binding a user-agent |
| **SQL Injection** | Queries parametrizadas via SQLAlchemy ORM |
| **XSS** | Escape automático, CSP headers |
| **CSRF** | No aplica (API stateless con Bearer tokens) |
| **Timing Attacks** | Comparación de hashes en tiempo constante (`secrets.compare_digest`) |
| **Prompt Injection** | Validación en API Gateway + guardrails en RAG Service |

### 11.6 Gestión de Secretos

| Secreto | Almacenamiento | Rotación |
|---------|----------------|----------|
| JWT Private Key | GCP Secret Manager | Anual (con soporte de múltiples keys) |
| Database Password | GCP Secret Manager | Trimestral |
| API Keys (usuarios) | PostgreSQL (bcrypt hash) | Bajo demanda del usuario |
| Encryption Keys | GCP KMS | Anual |

---

## 12. Observabilidad y Métricas

### 12.1 Métricas RED (Rate, Errors, Duration)

| Métrica | Tipo | Labels | Umbral de Alerta |
|---------|------|--------|------------------|
| `http_requests_total` | Counter | `method`, `path`, `status` | - |
| `http_request_duration_seconds` | Histogram | `method`, `path` | P95 > 500ms |
| `http_errors_total` | Counter | `method`, `path`, `error_code` | > 1% en 5min |

### 12.2 Métricas de Negocio

| Métrica | Tipo | Descripción | Umbral |
|---------|------|-------------|--------|
| `auth_login_total` | Counter | Intentos de login | - |
| `auth_login_failures_total` | Counter | Logins fallidos | > 10/min (posible ataque) |
| `conversations_created_total` | Counter | Conversaciones nuevas | - |
| `messages_sent_total` | Counter | Mensajes enviados | - |
| `websocket_connections_active` | Gauge | Conexiones WS activas | > 500 (capacity) |
| `rag_client_requests_total` | Counter | Requests al RAG Service | - |
| `rag_client_errors_total` | Counter | Errores del RAG Client | > 5% en 5min |
| `rag_client_circuit_state` | Gauge | Estado del circuit breaker | 1 = open (alerta) |

### 12.3 Estructura de Logs

Formato JSON estructurado para todos los logs:

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `timestamp` | string | Sí | ISO 8601 con timezone |
| `level` | string | Sí | DEBUG, INFO, WARN, ERROR |
| `message` | string | Sí | Descripción del evento |
| `trace_id` | string | Sí | ID de trazabilidad (X-Request-ID) |
| `span_id` | string | No | ID del span actual |
| `tenant_id` | string | Sí* | ID del tenant (*si autenticado) |
| `user_id` | string | Sí* | ID del usuario (*si autenticado) |
| `action` | string | No | Acción realizada |
| `resource` | string | No | Recurso afectado |
| `duration_ms` | integer | No | Duración de la operación |
| `status` | string | No | success, failure |
| `error_code` | string | No | Código de error (si aplica) |
| `extra` | object | No | Campos adicionales |

**Ejemplo:**

```json
{
  "timestamp": "2026-01-11T10:30:00.123Z",
  "level": "INFO",
  "message": "User authenticated successfully",
  "trace_id": "abc123-def456",
  "tenant_id": "tenant-001",
  "user_id": "user-123",
  "action": "auth.login",
  "duration_ms": 145,
  "status": "success"
}
```

### 12.4 Logs de Auditoría

Para cumplimiento regulatorio, los siguientes eventos generan logs de auditoría inmutables:

| Evento | Datos Registrados |
|--------|-------------------|
| Login exitoso | user_id, tenant_id, IP, user_agent, timestamp |
| Login fallido | email (hash), IP, user_agent, reason, timestamp |
| Logout | user_id, tenant_id, timestamp |
| Token refresh | user_id, tenant_id, old_jti, new_jti, timestamp |
| Acceso a conversación | user_id, conversation_id, action, timestamp |
| Creación de API key | user_id, key_prefix, scopes, timestamp |
| Revocación de API key | user_id, key_prefix, revoked_by, timestamp |

### 12.5 Alertas Configuradas

| Alerta | Condición | Severidad | Acción |
|--------|-----------|-----------|--------|
| High Error Rate | error_rate > 5% por 5min | Critical | PagerDuty |
| High Latency | P95 > 2s por 5min | Warning | Slack |
| Circuit Open | rag_circuit_state = 1 | Critical | PagerDuty |
| Auth Brute Force | login_failures > 20/min | Warning | Slack + bloqueo |
| DB Connection Pool | pool_used > 80% | Warning | Slack |
| WebSocket Saturation | ws_connections > 400 | Warning | Slack |

---

## 13. Configuración

### 13.1 Variables de Entorno

| Variable | Tipo | Requerida | Default | Descripción |
|----------|------|-----------|---------|-------------|
| `DATABASE_URL` | string | Sí | - | Connection string de PostgreSQL |
| `JWT_PRIVATE_KEY` | string | Sí | - | Clave privada RSA para firmar JWT |
| `JWT_PUBLIC_KEY` | string | Sí | - | Clave pública RSA para verificar JWT |
| `JWT_ALGORITHM` | string | No | RS256 | Algoritmo de firma |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | No | 15 | Expiración de access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | No | 7 | Expiración de refresh token |
| `RAG_SERVICE_URL` | string | Sí | - | URL del RAG Generation Service |
| `RAG_SERVICE_TIMEOUT` | int | No | 30 | Timeout en segundos |
| `CORS_ORIGINS` | string | Sí | - | Orígenes permitidos (comma-separated) |
| `ENVIRONMENT` | string | No | development | development, staging, production |
| `LOG_LEVEL` | string | No | INFO | DEBUG, INFO, WARNING, ERROR |
| `PROMETHEUS_ENABLED` | bool | No | true | Habilitar métricas Prometheus |
| `LANGFUSE_PUBLIC_KEY` | string | No | - | API key de Langfuse |
| `LANGFUSE_SECRET_KEY` | string | No | - | Secret key de Langfuse |

### 13.2 Configuración por Entorno

| Aspecto | Development | Staging | Production |
|---------|-------------|---------|------------|
| HTTPS Redirect | No | Sí | Sí |
| CORS Origins | `*` | Específicos | Específicos |
| Rate Limiting | Relajado | Normal | Estricto |
| Log Level | DEBUG | INFO | INFO |
| Circuit Breaker | Deshabilitado | Habilitado | Habilitado |

---

## 14. Documentación de API

La documentación de la API se genera automáticamente mediante OpenAPI/Swagger y está disponible en:

| Endpoint | Descripción |
|----------|-------------|
| `/docs` | Swagger UI interactivo |
| `/redoc` | ReDoc (documentación alternativa) |
| `/openapi.json` | Especificación OpenAPI 3.0 |

> "La documentación interactiva estará disponible en ambientes de desarrollo y staging. En producción, la especificación OpenAPI se publica en el portal de desarrolladores interno para consumo de integradores autorizados."
---

## 15. Referencias

- Para definiciones de términos técnicos, consultar el glosario en `docs/arc42/12_glossary.md`.
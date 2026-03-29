# ADR-003: REST + SSE como Protocolo de Comunicación Frontend-Backend

## Status

**Accepted**

## Date

2026-02-13

## Context

El frontend (Next.js) necesita comunicarse con el backend (FastAPI) para:
- Autenticación (login, logout, refresh)
- CRUD de conversaciones
- Envío de preguntas y recepción de respuestas RAG en streaming
- Gestión de documentos (post-MVP)
- Panel de administración (post-MVP)

La respuesta del LLM se genera token a token y debe mostrarse incrementalmente en la UI del chat (UX tipo ChatGPT).

## Considered Options

### Opción 1: REST + SSE (Server-Sent Events)

- REST para operaciones CRUD estándar
- SSE para streaming de respuestas del LLM

### Opción 2: REST + WebSockets

- REST para CRUD
- WebSocket bidireccional para chat

### Opción 3: gRPC + gRPC Streaming

- gRPC para todas las comunicaciones
- gRPC server streaming para respuestas

### Opción 4: GraphQL + Subscriptions

- GraphQL para queries y mutations
- Subscriptions (WebSocket) para streaming

## Decision

**REST + SSE (Opción 1).**

### Protocolos por caso de uso

| Operación | Protocolo | Endpoint pattern |
|-----------|-----------|-----------------|
| Auth (login, logout, refresh) | REST POST | `/api/v1/auth/*` |
| Listar conversaciones | REST GET | `/api/v1/conversations` |
| Detalle conversación | REST GET | `/api/v1/conversations/{id}` |
| Crear conversación | REST POST | `/api/v1/conversations` |
| **Enviar mensaje (chat)** | **REST POST → SSE stream** | `/api/v1/conversations/{id}/messages` |
| Health checks | REST GET | `/health`, `/health/ready` |
| Documentos (post-MVP) | REST CRUD | `/api/v1/documents/*` |
| Admin (post-MVP) | REST CRUD | `/api/v1/admin/*` |

### Formato SSE para chat

```
POST /api/v1/conversations/{id}/messages
Content-Type: application/json
Cookie: access_token=<JWT>

{"content": "¿Cuál es la normativa BCRA para...?"}

--- Response: text/event-stream ---

event: token
data: {"content": "Según"}

event: token
data: {"content": " la normativa"}

event: token
data: {"content": " BCRA 123/456,"}

...

event: done
data: {"message_id": "msg_abc", "sources": [{"doc_id": 1, "title": "...", "page": 3}]}

event: error  (solo si hay error)
data: {"code": "GENERATION_FAILED", "message": "..."}
```

### Justificación sobre las alternativas

| Criterio | REST+SSE | WebSockets | gRPC | GraphQL |
|----------|----------|------------|------|---------|
| Complejidad server | Baja | Media (connection mgmt) | Alta (protobuf) | Alta (schema) |
| Complejidad client | Baja (EventSource API) | Media | Alta (code gen) | Media |
| Streaming LLM | Nativo (SSE diseñado para esto) | Funciona pero overkill | Funciona | Funciona pero complejo |
| Reconexión automática | Built-in (EventSource) | Manual | Manual | Manual |
| Bidireccional | No (unidireccional server→client) | Sí | Sí | Sí |
| HTTP/2 compatible | Sí | No (upgrade) | Nativo | Depende |
| Load balancer friendly | Sí (HTTP estándar) | Requiere sticky sessions | Requiere HTTP/2 | Sí |
| Caching | HTTP cache estándar | No | No | Con persisted queries |

**SSE es la elección correcta** porque:
1. El streaming es **unidireccional** (server → client): el usuario envía una pregunta (POST), el server responde con stream de tokens
2. No necesitamos bidireccionalidad (el usuario no envía datos durante el streaming)
3. Reconexión automática con `Last-Event-ID`
4. Compatible con CDNs y load balancers estándar
5. API nativa del browser (`EventSource`) — sin librerías adicionales
6. FastAPI tiene soporte nativo con `StreamingResponse`

## Consequences

### Positivas

- Simplicidad: REST para CRUD + SSE para streaming, sin overhead de WebSockets
- Estándar HTTP: compatible con cualquier proxy, CDN, load balancer
- Browser nativo: `EventSource` API sin dependencias en el frontend
- Reconexión automática: el browser reconecta SSE si se pierde la conexión
- Debugging simple: las request REST se inspeccionan con herramientas estándar

### Negativas

- Si en el futuro necesitamos comunicación bidireccional en tiempo real (ej. collaborative editing), WebSockets sería más apropiado
- SSE tiene un límite de ~6 conexiones simultáneas por dominio en HTTP/1.1 (no es problema con HTTP/2)
- No hay feedback del cliente durante el streaming (ej. "cancelar generación") — se puede implementar con un endpoint REST separado `DELETE /conversations/{id}/messages/current`

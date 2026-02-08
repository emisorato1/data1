
# TODO – Enterprise AI Platform

## Alta prioridad

- [ ] Integrar parsing completo de respuesta RAG
- [ ] Mapear output final → MessageORM
- [ ] Persistir fuentes en MessageSourceORM
- [ ] Manejar estados del run (pending / completed / failed)
- [ ] Manejo de errores tipados en MessageService

---

## Media prioridad

- [ ] Unificar `session_id` → `conversation_id`
- [ ] Rehabilitar relación Conversation ↔ Messages
- [ ] Agregar índices en messages (session_id, created_at)
- [ ] Validaciones Pydantic más estrictas
- [ ] Logs estructurados (JSON)

---

## Baja prioridad

- [ ] Soft delete en messages
- [ ] Paginación de historial
- [ ] Endpoint de healthcheck dedicado
- [ ] Métricas básicas (latencia, errores)

---

## Arquitectura futura

- [ ] Reintroducir tenant_id de forma transparente
- [ ] Separar write/read models (CQRS light)
- [ ] Cache de respuestas frecuentes
- [ ] Versionado de conversaciones

---

## Testing

- [ ] Tests unitarios MessageService
- [ ] Tests de integración API + DB
- [ ] Fixtures de conversaciones
- [ ] Mock de servicios externos

---

## Documentación

- [ ] Diagrama de arquitectura (C4)
- [ ] Diagrama ER de la DB
- [ ] Ejemplos de payloads válidos
- [ ] Guía de contribución

---
# Services

Servicios backend independientes y desplegables en contenedores.

## Servicios

- **api**: API Gateway (FastAPI) para autenticación, routing y rate limiting. Expone HTTP REST para operaciones CRUD y WebSocket para streaming de respuestas al frontend.
- **rag-generation**: Agente RAG con LangGraph para retrieval, augmentation y generation. Comunica vía gRPC con el API Gateway para alto rendimiento y streaming de tokens.
- **rag-indexation**: Pipelines de ingesta desde OpenText ECM a PostgreSQL/pgvector, compatible con Airflow.
- **mcp**: (Futuro) Servicio MCP para integraciones externas.

## Protocolos de comunicación

| Comunicación | Protocolo | Razón |
|--------------|-----------|-------|
| Frontend → API | HTTP REST + WebSocket | Compatibilidad browser, streaming UI |
| API → RAG Generation | gRPC | Alto rendimiento, tipado fuerte |
| API → RAG Indexation | HTTP/gRPC | Operaciones batch |

Cada servicio tiene su propio Dockerfile, tests y pyproject.toml.
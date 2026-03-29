# ADR-002: LangGraph como Librería Embebida en FastAPI

## Status

**Accepted**

## Date

2026-02-13

## Context

LangGraph es el motor de orquestación del pipeline RAG. Existen dos formas de usarlo:

1. **Como librería Python** (`pip install langgraph`): corre in-process dentro de FastAPI
2. **Como LangGraph Platform** (producto comercial): servicio independiente con su propia API REST (~30 endpoints), requiere Postgres + Redis adicionales

El pipeline RAG tiene 11+ nodos (validate_input, process_query, route_query, retrieve, rerank, assemble_context, generate, validate_output, load_memory, save_memory, respond_blocked) y necesita:
- Estado persistente entre turnos (checkpointer)
- Streaming de tokens vía SSE
- Integración con autenticación JWT existente
- Trazabilidad con Langfuse

## Considered Options

### Opción 1: LangGraph como librería embebida

```python
# Compilar grafo al inicio, almacenar en app.state
@asynccontextmanager
async def lifespan(app: FastAPI):
    checkpointer = AsyncPostgresSaver(pool)
    graph = build_rag_graph().compile(checkpointer=checkpointer)
    app.state.graph = graph
    yield

# Usar directamente en endpoints
@app.post("/api/v1/chat/{conversation_id}/messages")
async def chat(conversation_id: str, request: ChatRequest):
    async for event in app.state.graph.astream(state, config):
        yield format_sse(event)
```

**Pros:**
- Control total sobre endpoints, auth, rate limiting, business logic
- Sin infraestructura adicional (usa el mismo Postgres para checkpoints)
- Sin vendor lock-in (LangGraph OSS es MIT)
- Sin overlap entre API del Platform y nuestra API
- Cero costo adicional
- Latencia mínima (in-process, sin network hop)

**Contras:**
- Implementar streaming SSE manualmente (trivial con FastAPI)
- No tiene LangGraph Studio para debugging visual (usa Langfuse como alternativa)
- Implementar double-texting handling manualmente si se necesita

### Opción 2: LangGraph Platform como servicio separado

```python
# FastAPI actúa como proxy/gateway
from langgraph_sdk import get_client
client = get_client(url="http://langgraph-platform:8123")

@app.post("/api/v1/chat/{conversation_id}/messages")
async def chat(conversation_id: str, request: ChatRequest):
    thread = await client.threads.create()
    run = await client.runs.stream(thread["thread_id"], ...)
```

**Pros:**
- Background processing, cron jobs, webhooks built-in
- Double-texting handling built-in
- LangGraph Studio para debugging visual

**Contras:**
- Requiere Postgres + Redis adicionales (dedicados para Platform)
- Vendor lock-in al producto comercial (free tier: 1M nodes, luego paid)
- Overlap significativo: threads/runs/assistants del Platform duplican nuestro modelo de conversaciones
- Network hop adicional FastAPI → Platform (latencia extra)
- Un 4to namespace en K8s para operar
- La API del Platform tiene diseño opinionated que no se alinea con nuestro dominio bancario
- FastAPI se reduce a un proxy, perdiendo control sobre la lógica de negocio

## Decision

**LangGraph como librería embebida en FastAPI (Opción 1).**

El grafo RAG se compila al startup de FastAPI y se almacena en `app.state`. El checkpointer usa `AsyncPostgresSaver` sobre el mismo PostgreSQL del sistema. Los endpoints de chat invocan `graph.astream()` directamente, con streaming SSE nativo de FastAPI.

### Estructura de código

```
src/application/graphs/
├── state.py              # RAGState (TypedDict con reducers)
├── rag_graph.py          # build_rag_graph() → StateGraph
└── nodes/                # Un archivo por nodo
    ├── validate_input.py
    ├── process_query.py
    ├── route_query.py
    ├── retrieve.py
    ├── rerank.py
    ├── assemble_context.py
    ├── generate.py
    ├── validate_output.py
    ├── load_memory.py
    ├── save_memory.py
    └── respond_blocked.py
```

## Consequences

### Positivas

- Control total sobre API design, auth, y business logic
- Cero costo de licencia y cero infraestructura adicional
- Latencia mínima (in-process)
- Debugging con Langfuse (ya desplegado) en vez de LangGraph Studio
- Sin duplicación de modelos (nuestras conversations/messages son la fuente de verdad)

### Negativas

- Si en el futuro necesitamos features avanzadas del Platform (cron jobs sobre grafos, human-in-the-loop nativo), habría que implementarlas o migrar
- No tenemos LangGraph Studio para debugging visual (mitigado con Langfuse tracing)

## References

- [LangGraph as library in FastAPI — Production Template](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template)
- [LangServe Migration Guide — Recommends LangGraph](https://github.com/langchain-ai/langserve/blob/main/MIGRATION.md)
- [LangGraph Platform API Reference](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html)

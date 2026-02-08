# Implementación de Memoria — RAG Generation Service

> **Estado**: ✅ Implementado y probado (2026-02-07)
> **Referencia oficial**: [LangGraph Memory Documentation](https://langchain-ai.github.io/langgraph/concepts/memory/)

---

## 1. Resumen Ejecutivo

Se implementó un sistema de **memoria dual** que permite al chatbot RAG empresarial mantener conversaciones coherentes —similar a ChatGPT— combinando dos mecanismos nativos de LangGraph:

| Tipo de memoria | Mecanismo LangGraph | Backend | Alcance |
|---|---|---|---|
| **Short-term** (hilo de conversación) | Checkpointer (`AsyncPostgresSaver`) | PostgreSQL | Por thread/sesión |
| **Long-term** (memoria del usuario) | Store (`AsyncPostgresStore`) | PostgreSQL + embeddings | Cross-session, por usuario |

Ambos persisten en PostgreSQL, sobreviven reinicios del servicio y están preparados para Kubernetes.

---

## 2. ¿Por qué un servidor custom FastAPI y no `langgraph dev`?

### El problema con `langgraph dev`

La documentación oficial de LangGraph explica que existen dos formas de ejecutar un grafo: `langgraph dev` (desarrollo) y `langgraph up` (producción). Sin embargo, durante la implementación descubrimos una **limitación crítica**:

> *"Your graph includes a custom checkpointer. With LangGraph API, persistence is handled automatically by the platform, so providing a custom checkpointer here isn't necessary and **will be ignored when deployed**."*

`langgraph dev` usa internamente el runtime `langgraph_runtime_inmem`, que:

1. **Rechaza** cualquier checkpointer custom pasado en `builder.compile(checkpointer=...)`.
2. Inyecta un `InMemorySaver` automáticamente → **las conversaciones se pierden al reiniciar**.
3. El Store sí funciona con PostgreSQL si se configura en `langgraph.json`.

Esto significa que con `langgraph dev` es **imposible** lograr persistencia de conversaciones.

### La solución: Servidor custom con FastAPI

Se optó por reemplazar `langgraph dev` con un servidor FastAPI custom (`src/server.py`) que:

- Compila el grafo con `AsyncPostgresSaver` + `AsyncPostgresStore` de forma explícita.
- Ejecuta `.setup()` automáticamente al inicio para crear las tablas de persistencia.
- Expone los mismos endpoints que la API de LangGraph, manteniendo compatibilidad con el API Gateway.
- Usa `asynccontextmanager` para lifecycle hooks (startup/shutdown), preparado para Kubernetes.

### ¿Por qué no `langgraph up`?

`langgraph up` sí soporta PostgreSQL para el checkpointer, pero:

- Requiere construir una imagen Docker con `langgraph build`.
- No permite hot-reload durante desarrollo.
- Agrega una capa de abstracción adicional que dificulta el debugging.
- Limita el control sobre endpoints, middleware y lifecycle hooks.

El servidor custom FastAPI combina lo mejor de ambos mundos: persistencia completa + hot-reload + control total.

---

## 3. Conceptos Fundamentales (según la documentación oficial)

> **Referencia**: [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) y [LangGraph Memory](https://langchain-ai.github.io/langgraph/concepts/memory/)

### 3.1 Checkpointer — Short-term Memory

El **Checkpointer** es el mecanismo que LangGraph usa para guardar el estado del grafo después de cada "super-step". Según la documentación:

> *"A checkpoint is a snapshot of the graph state saved at each super-step and is represented by `StateSnapshot` [...] This enables several powerful capabilities like human-in-the-loop, memory, time travel, and fault-tolerance."*

En nuestro proyecto, el checkpointer habilita:

- **Persistencia de mensajes**: Los `messages` (con reducer `add_messages`) se acumulan automáticamente entre invocaciones del mismo `thread_id`.
- **Continuidad de conversación**: El usuario puede preguntar "¿cómo me llamo?" y el agente responde basándose en mensajes anteriores del mismo thread.
- **Sobrevive reinicios**: Al usar `AsyncPostgresSaver` con PostgreSQL, los checkpoints se almacenan de forma durable.

#### Implementaciones disponibles

| Checkpointer | Uso | Paquete |
|---|---|---|
| `MemorySaver` | Testing | `langgraph` |
| `SqliteSaver` / `AsyncSqliteSaver` | Prototipo local | `langgraph-checkpoint-sqlite` |
| `PostgresSaver` / `AsyncPostgresSaver` | **Producción** ✅ | `langgraph-checkpoint-postgres` |

#### ¿Por qué `AsyncPostgresSaver` y no `PostgresSaver`?

Se eligió la versión asíncrona porque:

1. **FastAPI es async-first**: Todos los endpoints son `async def`, y el grafo se ejecuta con `ainvoke` / `astream_events`.
2. **Connection pool async**: Usa `AsyncConnectionPool` de `psycopg`, que no bloquea el event loop.
3. **Preparado para alta concurrencia**: En Kubernetes con múltiples pods, cada pod mantiene su propio pool de conexiones async.

#### Tablas creadas por `.setup()`

Cuando se ejecuta `await checkpointer.setup()`, se crean automáticamente:

| Tabla | Contenido |
|---|---|
| `checkpoints` | Estado serializado del grafo por thread_id |
| `checkpoint_blobs` | Datos binarios (mensajes, estado) |
| `checkpoint_writes` | Escrituras pendientes (task-level) |
| `checkpoint_migrations` | Control de versión del schema |

### 3.2 Store — Long-term Memory

El **Store** es el mecanismo de LangGraph para memoria cross-session. Según la documentación:

> *"Stores in LangGraph provide a built-in persistence layer for data that needs to live beyond a single thread. Unlike checkpoints, which save state within a conversation thread, stores allow you to save and retrieve information across threads—making them ideal for learning user preferences or building shared knowledge bases."*

En nuestro proyecto, el Store permite:

- **Recordar hechos del usuario**: Nombre, rol, empresa, preferencias.
- **Búsqueda semántica**: Encontrar memorias relevantes al mensaje actual usando embeddings de OpenAI.
- **Separación por usuario**: Cada `user_id` tiene su propio namespace de memorias.

#### Namespaces

Los datos se organizan en namespaces (tuplas de strings):

```python
# Memorias de hechos de un usuario específico
namespace = (user_id, "facts")

# Posibles extensiones futuras
namespace = (user_id, "preferences")
namespace = (user_id, "summaries")
namespace = (tenant_id, "shared", "config")
```

#### Tablas creadas por `.setup()`

| Tabla | Contenido |
|---|---|
| `store` | Datos key-value (memorias) |
| `store_vectors` | Embeddings para búsqueda semántica |
| `store_migrations` | Control de versión del schema |

### 3.3 Diferencias entre Checkpointer y Store

| Aspecto | Checkpointer | Store |
|---|---|---|
| **Alcance** | Por thread (una conversación) | Cross-thread (entre conversaciones) |
| **Datos** | Estado completo del grafo (mensajes, contexto) | Datos arbitrarios key-value |
| **Guardado** | Automático (después de cada step) | Manual (desde los nodos) |
| **Búsqueda** | Por `thread_id` / `checkpoint_id` | Semántica con embeddings |
| **Uso típico** | "¿Cómo me llamo?" dentro del chat | Recordar nombre entre chats distintos |
| **Inyección** | En `builder.compile(checkpointer=...)` | En `builder.compile(store=...)` o como parámetro de nodo |

---

## 4. Arquitectura Implementada

### 4.1 Diagrama general

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Frontend (Next.js)                          │
│                      session_id = thread_id (UUID)                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       API Gateway (FastAPI)                           │
│                                                                      │
│  • Extrae user_id / tenant_id del token JWT                          │
│  • Pasa session_id como thread_id al RAG                             │
│  • Proxy streaming SSE hacia el frontend                             │
│  • Guarda mensajes en la DB del API Gateway                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  RAG Generation (FastAPI custom)                      │
│                       src/server.py                                   │
│                                                                      │
│  Lifespan (startup):                                                 │
│    1. AsyncPostgresSaver.from_conn_string(POSTGRES_URI)              │
│       → await checkpointer.setup()  (crea tablas)                    │
│    2. AsyncPostgresStore.from_conn_string(POSTGRES_URI, index=...)   │
│       → await store.setup()  (crea tablas + índices)                 │
│    3. builder.compile(checkpointer=checkpointer, store=store)        │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                     StateGraph (LangGraph)                     │  │
│  │                                                                │  │
│  │  START → orchestrator ──┬── public_agent ──→ END               │  │
│  │                         └── private_agent ─→ END               │  │
│  │                                                                │  │
│  │  Checkpointer: mensajes acumulados por thread_id               │  │
│  │  Store: memorias por (user_id, memory_type)                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Endpoints:                                                          │
│    GET  /info                          → Health check                │
│    POST /threads                       → Crear thread (no-op)        │
│    POST /threads/{id}/runs             → Ejecutar grafo (async)      │
│    GET  /threads/{id}/runs/{rid}/join  → Esperar resultado           │
│    POST /threads/{id}/runs/stream      → Streaming SSE               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL (pgvector)                             │
│                                                                      │
│  Tablas de checkpointer:        Tablas de store:                     │
│  ├── checkpoints                ├── store                            │
│  ├── checkpoint_blobs           ├── store_vectors                    │
│  ├── checkpoint_writes          └── store_migrations                 │
│  └── checkpoint_migrations                                           │
│                                                                      │
│  Tablas de documentos (RAG):    Tablas del API Gateway:              │
│  ├── documents                  ├── messages                         │
│  └── document_chunks            └── message_sources                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Flujo de una conversación

```
Usuario envía: "Hola, me llamo Emiliano"
         │
         ▼
    API Gateway
    ├── Extrae user_id del JWT (o usa anonymous)
    ├── Genera session_id si es nueva conversación
    └── POST /threads/{session_id}/runs/stream
              │
              ▼
         src/server.py
         ├── Inyecta thread_id = session_id en config.configurable
         └── graph.astream_events(input, config)
                   │
                   ▼
            orchestrator_node
            ├── Extrae user_id del config
            ├── Busca memorias en Store: store.asearch((user_id, "facts"), query=message)
            ├── Formatea memory_context para el prompt
            ├── Clasifica consulta → "public"
            └── return {current_agent: "public_agent", user_memories, memory_context}
                   │
                   ▼
            public_agent_node
            ├── Incluye memory_context en el system prompt
            ├── Busca documentos en vector store (RAG)
            ├── Genera respuesta con LLM (streaming)
            ├── Detecta info memorable: should_remember("me llamo Emiliano") → True
            ├── Guarda en Store: store.aput((user_id, "facts"), uuid, {data: "me llamo Emiliano"})
            └── return {response, sources, messages: [HumanMessage, AIMessage]}
                   │
                   ▼
         Checkpointer (automático)
         └── Guarda el estado completo (incluidos messages) en PostgreSQL
              con key = (thread_id, checkpoint_ns)

--- Siguiente mensaje en el mismo thread ---

Usuario envía: "¿Cómo me llamo?"
         │
         ▼
         Checkpointer restaura el estado anterior
         → state.messages contiene [HumanMessage("Hola..."), AIMessage("¡Hola Emiliano!...")]
         → El agente puede responder: "Te llamas Emiliano"
```

---

## 5. Implementación — Archivos Clave

### 5.1 `src/server.py` — Servidor FastAPI con lifespan

Este es el corazón de la persistencia. Usa `asynccontextmanager` para inicializar los recursos al arrancar y cerrarlos al apagar:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Checkpointer — persistencia de conversaciones
    async with AsyncPostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer:
        await checkpointer.setup()  # Crea tablas si no existen

        # 2. Store — long-term memory con búsqueda semántica
        async with AsyncPostgresStore.from_conn_string(
            POSTGRES_URI,
            index={
                "embed": f"openai:{EMBEDDING_MODEL}",
                "dims": 1536,
                "fields": ["$"],
            },
        ) as store:
            await store.setup()  # Crea tablas + índices si no existen

            # 3. Compilar grafo con persistencia
            graph_builder = create_graph_builder()
            graph = graph_builder.compile(
                checkpointer=checkpointer,
                store=store,
            )

            app.state.graph = graph
            yield

    # Los context managers cierran los pools automáticamente
```

**¿Por qué `from_conn_string` como async context manager?**

Según el código fuente de `langgraph-checkpoint-postgres`, `from_conn_string` es un `@asynccontextmanager` que:
1. Crea un `AsyncConnectionPool` con la URI de PostgreSQL.
2. Lo abre (`await pool.open()`).
3. Al salir del `async with`, lo cierra limpiamente (`await pool.close()`).

Esto garantiza que las conexiones se liberen correctamente al detener el servicio — requisito para Kubernetes donde los pods se destruyen y recrean frecuentemente.

### 5.2 `src/agents/graph.py` — Builder del grafo

El grafo se define con dos funciones:

```python
def create_graph_builder() -> StateGraph:
    """Crea el StateGraph SIN compilar — usado por src/server.py."""
    graph = StateGraph(RAGState)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("public_agent", public_agent_node)
    graph.add_node("private_agent", private_agent_node)
    graph.add_edge(START, "orchestrator")
    graph.add_conditional_edges("orchestrator", route_to_agent, {...})
    graph.add_edge("public_agent", END)
    graph.add_edge("private_agent", END)
    return graph

# Para backward-compatibility con langgraph dev
agent = create_graph_builder().compile()
```

**¿Por qué separar builder y compilación?**

- `create_graph_builder()` retorna el `StateGraph` **sin compilar**, para que `src/server.py` pueda inyectar el checkpointer y store.
- `agent` es un grafo compilado **sin checkpointer**, compatible con `langgraph dev` que inyecta su propio `InMemorySaver`.

### 5.3 `src/agents/state.py` — Estado del grafo con soporte de memoria

```python
class RAGState(TypedDict):
    # Short-term memory (automático via checkpointer)
    messages: Annotated[list, add_messages]  # Se acumulan entre invocaciones
    message: str                              # Mensaje actual del usuario

    # Long-term memory (manual via store)
    user_memories: NotRequired[list[UserMemory]]  # Memorias cargadas del usuario
    memory_context: NotRequired[str]               # Contexto formateado para el prompt

    # Resto del estado RAG
    session_id: str
    user_role: Literal["public", "private"]
    retrieved_context: list[RetrievedDocument]
    current_agent: str
    response: str
    sources: list[Source]
    metadata: dict
```

**Punto clave — `Annotated[list, add_messages]`**:

Según la documentación de LangGraph:

> *"The `add_messages` function is used as a reducer that handles message deduplication by ID. This ensures messages accumulate correctly across graph steps."*

Al usar `add_messages` como reducer, cada vez que un nodo retorna `{"messages": [HumanMessage(...), AIMessage(...)]}`, estos se **agregan** al historial existente en lugar de reemplazarlo. El checkpointer guarda este historial acumulado, y en la siguiente invocación con el mismo `thread_id`, el estado restaurado incluye todos los mensajes previos.

### 5.4 `src/agents/memory.py` — Utilidades de memoria

Módulo con funciones para interactuar con el Store:

| Función | Descripción |
|---|---|
| `search_user_memories()` | Búsqueda semántica de memorias por query + user_id |
| `get_all_user_memories()` | Lista todas las memorias de un usuario |
| `save_user_memory()` | Guarda una memoria nueva en el namespace `(user_id, type)` |
| `update_user_memory()` | Actualiza una memoria existente |
| `delete_user_memory()` | Elimina una memoria |
| `format_memories_as_context()` | Convierte memorias a texto para el system prompt |
| `should_remember()` | Detecta patrones en el mensaje que indican info memorable |
| `extract_memorable_info()` | Extrae la info a guardar del mensaje |

**¿Por qué detección por patrones y no por LLM?**

La detección actual usa pattern matching simple ("me llamo...", "trabajo en...", etc.) por eficiencia. Un LLM agregaría latencia y costo por cada mensaje. En producción se puede migrar a extracción con LLM como mejora futura, priorizando calidad sobre velocidad.

### 5.5 `src/agents/orchestrator/node.py` — Carga de memorias

El orquestador es el primer nodo del grafo y se encarga de cargar memorias del Store:

```python
async def orchestrator_node(
    state: RAGState,
    config: RunnableConfig,
    *,
    store: BaseStore,  # ← Inyectado automáticamente por LangGraph
) -> dict:
    user_id = get_user_id_from_config(config)

    # Búsqueda semántica: encuentra memorias relevantes al mensaje actual
    user_memories = await search_user_memories(
        store=store, user_id=user_id, query=state["message"], limit=5
    )
    memory_context = format_memories_as_context(user_memories)

    return {
        "current_agent": target_agent,
        "user_memories": user_memories,
        "memory_context": memory_context,
    }
```

**¿Por qué el parámetro `store` con `*`?**

Según la documentación oficial:

> *"When you compile a graph with `store=my_store`, LangGraph will automatically inject the store into any node function that accepts `store` as a keyword-only argument."*

El `*` antes de `store: BaseStore` lo convierte en keyword-only, lo que permite a LangGraph detectarlo e inyectarlo automáticamente al ejecutar el nodo.

### 5.6 `src/agents/public_agent/node.py` y `private_agent/node.py` — Guardado de memorias

Ambos agentes:

1. **Reciben** `memory_context` del orquestador y lo inyectan en el system prompt.
2. **Guardan** información memorable del usuario al final de cada interacción.
3. **Acumulan** mensajes en `state.messages` para el checkpointer.

```python
async def public_agent_node(state, config, *, store: BaseStore):
    # Incluir memoria en el prompt
    system_prompt = PUBLIC_AGENT_SYSTEM_PROMPT
    if state.get("memory_context"):
        system_prompt += f"\n\n{state['memory_context']}"

    # ... (RAG retrieval + generation) ...

    # Guardar info memorable
    if should_remember(message):
        memorable_info = extract_memorable_info(message)
        await save_user_memory(store, user_id, memorable_info)

    # Retornar mensajes para el checkpointer
    return {
        "response": response_text,
        "messages": [HumanMessage(content=message), AIMessage(content=response_text)],
    }
```

---

## 6. Integración con el API Gateway

### 6.1 Flujo de datos

```
Frontend                       API Gateway                    RAG Service
   │                               │                              │
   │  POST /api/v1/chatbot/stream  │                              │
   │  {message, session_id}        │                              │
   │  Authorization: Bearer JWT    │                              │
   │ ─────────────────────────────►│                              │
   │                               │                              │
   │                               │  Extraer user_id del JWT     │
   │                               │  Extraer tenant_id del JWT   │
   │                               │                              │
   │                               │  POST /threads               │
   │                               │  POST /threads/{id}/runs/stream
   │                               │  config.configurable:        │
   │                               │    thread_id = session_id    │
   │                               │    user_id = jwt.user_id     │
   │                               │    tenant_id = jwt.tenant_id │
   │                               │ ────────────────────────────►│
   │                               │                              │
   │                               │        SSE Stream            │
   │                               │ ◄────────────────────────────│
   │        SSE Stream             │                              │
   │ ◄─────────────────────────────│                              │
```

### 6.2 Archivos involucrados

| Archivo (API Gateway) | Responsabilidad |
|---|---|
| `app/presentation/http/routes/chat.py` | Extrae `user_id` y `tenant_id` del JWT |
| `app/application/services/chat_service.py` | Pasa IDs al `RagClient`, guarda mensajes en DB |
| `app/infrastructure/http/rag_client.py` | Cliente HTTP que se comunica con el RAG via SSE |

### 6.3 Configuración (`configurable`)

El `thread_id` se usa para el checkpointer (short-term) y el `user_id` para el store (long-term):

```python
# En rag_client.py
config = {
    "configurable": {
        "thread_id": session_id,    # → Checkpointer (short-term)
        "user_id": str(user_id),    # → Store (long-term)
        "tenant_id": str(tenant_id),
        "user_role": user_role,
    }
}
```

Para usuarios anónimos (sin JWT), se usan UUIDs por defecto:

```python
ANONYMOUS_USER_ID = UUID("00000000-0000-0000-0000-000000000000")
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
```

La long-term memory **no se activa** para usuarios anónimos (`user_id == "anonymous"` se ignora en todas las funciones de memoria).

---

## 7. Configuración e Infraestructura

### 7.1 Variables de entorno requeridas

```bash
# PostgreSQL (para checkpointer + store + documentos)
POSTGRES_URI=postgresql://eai_user:password@postgres:5432/enterpriseaigatewaydev

# OpenAI (para embeddings de búsqueda semántica en el Store)
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small  # Opcional, default: text-embedding-3-small
```

### 7.2 Docker Compose

```yaml
# infra/dev/docker-compose.yaml
agentic-rag:
  environment:
    POSTGRES_URI: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    OPENAI_API_KEY: ${OPENAI_API_KEY}
    EMBEDDING_MODEL: ${EMBEDDING_MODEL}
  command: ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "2024", "--reload"]
  depends_on:
    postgres:
      condition: service_healthy
```

**`--reload`** habilita hot-reload en desarrollo: al modificar archivos en `src/`, uvicorn reinicia automáticamente el servidor y ejecuta `checkpointer.setup()` + `store.setup()` de nuevo (idempotentes).

### 7.3 Dockerfile

```dockerfile
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "2024"]
```

En producción (Kubernetes) se elimina `--reload` y se usa el CMD del Dockerfile directamente.

### 7.4 Dependencias (`pyproject.toml`)

```toml
dependencies = [
    "langgraph>=1.0.4",
    "langgraph-checkpoint-postgres>=2.0.0",  # AsyncPostgresSaver
    "psycopg[binary,pool]>=3.1.0",           # Driver PostgreSQL async
    "fastapi>=0.100.0",                       # Servidor custom
    "uvicorn[standard]>=0.20.0",              # ASGI server
    # ... otras dependencias
]
```

### 7.5 `langgraph.json` (backward-compatible)

```json
{
    "python_version": "3.12",
    "dependencies": ["."],
    "graphs": {
        "rag_generation": "./src/agents/graph.py:agent"
    },
    "store": {
        "type": "postgres",
        "uri": "${POSTGRES_URI}",
        "index": {
            "embed": "openai:text-embedding-3-small",
            "dims": 1536,
            "fields": ["$"]
        }
    }
}
```

Este archivo se mantiene para compatibilidad con `langgraph dev` (el grafo `agent` se exporta sin checkpointer), pero el **modo principal de ejecución** es el servidor custom.

---

## 8. Detección y Almacenamiento de Memorias

### 8.1 Patrones detectados automáticamente

El sistema detecta información memorable cuando el mensaje contiene:

| Patrón | Ejemplo | Tipo de memoria |
|---|---|---|
| `me llamo` / `mi nombre es` | "Me llamo Emiliano" | `facts` |
| `soy` / `trabajo en` / `trabajo como` | "Trabajo en ventas" | `facts` |
| `recuerda que` / `no olvides` | "Recuerda que prefiero resúmenes cortos" | `facts` |
| `prefiero` / `me gusta` / `no me gusta` | "Prefiero respuestas en español" | `facts` |
| `mi email es` / `mi correo es` | "Mi email es emi@empresa.com" | `facts` |
| `vivo en` / `mi empresa es` | "Vivo en Buenos Aires" | `facts` |
| `mi departamento es` / `mi equipo es` | "Mi equipo es Data Engineering" | `facts` |

### 8.2 Formato de almacenamiento

```python
# Namespace en el Store
namespace = (user_id, "facts")

# Valor almacenado
value = {
    "data": "Me llamo Emiliano y trabajo en Data Oilers",
    "type": "facts",
    "created_at": "2026-02-07T15:30:00+00:00",
    "metadata": {},
}
```

### 8.3 Recuperación por búsqueda semántica

Cuando el usuario envía un mensaje, el orquestador busca memorias relevantes:

```python
# Si el usuario dice "¿Qué sabes de mí?"
# El Store busca embeddings similares a ese query
memories = await store.asearch(
    (user_id, "facts"),
    query="¿Qué sabes de mí?",
    limit=5,
)
# → Retorna: ["Me llamo Emiliano", "Trabajo en Data Oilers", ...]
```

La búsqueda semántica usa el modelo `text-embedding-3-small` de OpenAI (1536 dimensiones), configurado al crear el Store.

---

## 9. Pruebas Realizadas

### 9.1 Persistencia short-term (checkpointer)

| Prueba | Resultado |
|---|---|
| Enviar "Hola, me llamo Emiliano" en thread `test-002` | ✅ Respuesta correcta |
| Enviar "¿Cómo me llamo?" en el mismo thread | ✅ "Te llamas Emiliano" |
| **Reiniciar el contenedor** (`docker compose restart`) | — |
| Enviar "¿Puedes repetir mi nombre?" en el mismo thread | ✅ "Tu nombre es Emiliano" (14 checkpoints preservados) |

### 9.2 Persistencia long-term (store)

| Prueba | Resultado |
|---|---|
| Detectar "me llamo Emiliano" como memorable | ✅ `should_remember()` retorna True |
| Guardar en Store con `save_user_memory()` | ✅ Almacenado en PostgreSQL |
| Buscar con `search_user_memories()` | ✅ Retorna memoria relevante |

### 9.3 Streaming SSE

| Prueba | Resultado |
|---|---|
| Formato `event: events` | ✅ Compatible con `rag_client.py` |
| `data.event = on_chat_model_stream` | ✅ Tokens de streaming |
| `data.metadata.langgraph_node` | ✅ Correcto para filtrar nodos |
| Evento final `on_chain_end` | ✅ Sources incluidas |

### 9.4 Tablas en PostgreSQL

```sql
SELECT thread_id, COUNT(*) FROM checkpoints GROUP BY thread_id;
--  thread_id   | count
-- ------------ | -----
--  test-002    |    14    ← Thread de prueba con 3 conversaciones
--  d1260146-.. |     6    ← Thread creado desde el frontend
```

---

## 10. Archivos del Proyecto

### Archivos creados

| Archivo | Descripción |
|---|---|
| `src/server.py` | Servidor custom FastAPI con lifespan, AsyncPostgresSaver + AsyncPostgresStore |
| `src/agents/memory.py` | Utilidades para memoria long-term (CRUD + detección + formato) |
| `docs/MEMORY_IMPLEMENTATION.md` | Esta documentación |

### Archivos modificados

| Archivo | Cambios |
|---|---|
| `src/agents/graph.py` | Exporta `create_graph_builder()` (builder sin compilar) + `agent` (backward-compat) |
| `src/agents/state.py` | Campos `user_memories` y `memory_context` en `RAGState` |
| `src/agents/orchestrator/node.py` | Inyección de `store`, carga de memorias al inicio del grafo |
| `src/agents/public_agent/node.py` | Inyección de `store`, memory_context en prompt, guardado de memorias |
| `src/agents/private_agent/node.py` | Inyección de `store`, memory_context en prompt, guardado de memorias |
| `pyproject.toml` | Dependencias: `fastapi`, `uvicorn`, `langgraph-checkpoint-postgres`, `psycopg` |
| `Dockerfile` | CMD actualizado a `uvicorn src.server:app` |
| `docker-compose.yaml` | Command actualizado a `uvicorn` con `--reload` |
| `langgraph.json` | Configuración de Store (backward-compatible con `langgraph dev`) |
| `app/infrastructure/http/rag_client.py` | Método `stream()` con `user_id` y `tenant_id` en config |
| `app/application/services/chat_service.py` | Soporte para `user_id` y `tenant_id`, normalización de sources |
| `app/presentation/http/routes/chat.py` | Extracción de usuario autenticado del JWT |

---

## 11. Preparación para Kubernetes

El servidor custom está diseñado pensando en un deploy futuro en Kubernetes con Google Cloud:

| Aspecto | Implementación |
|---|---|
| **Health checks** | `GET /info` y `GET /ok` para liveness/readiness probes |
| **Graceful shutdown** | `asynccontextmanager` cierra pools de conexiones al apagar |
| **Connection pooling** | `AsyncConnectionPool` con límites configurables |
| **Stateless** | Todo el estado está en PostgreSQL, los pods son intercambiables |
| **Configuración** | Via variables de entorno (`POSTGRES_URI`, `OPENAI_API_KEY`) |
| **Hot-reload** | Solo en desarrollo (`--reload`), no en producción |

Para migrar a Google Cloud SQL:

```bash
# Solo cambiar la variable de entorno
POSTGRES_URI=postgresql://user:pass@google-cloud-sql-ip:5432/dbname
```

---

## 12. Próximos Pasos (Mejoras Futuras)

1. **Extracción inteligente de memorias con LLM**: Reemplazar pattern matching por un LLM que extraiga solo la información relevante del mensaje.
2. **Deduplicación de memorias**: Evitar guardar información duplicada o contradictoria.
3. **Memorias con TTL**: Expiración automática de memorias antiguas.
4. **Memorias a nivel de tenant**: Información compartida entre usuarios del mismo tenant.
5. **UI para gestión de memorias**: Permitir al usuario ver, editar y eliminar sus memorias.
6. **Resumen automático de conversaciones**: Al finalizar un thread, generar un resumen y guardarlo como memoria long-term.

---

## 13. Troubleshooting

### Error: "POSTGRES_URI no está configurado"
- Verificar que la variable `POSTGRES_URI` exista en `.env.general` o en el environment del docker-compose.
- Formato esperado: `postgresql://user:password@host:port/database`

### Las conversaciones no persisten entre reinicios
- Verificar que el servicio esté usando `uvicorn src.server:app` (no `langgraph dev`).
- Verificar que las tablas `checkpoints`, `checkpoint_blobs`, etc. existan en PostgreSQL.
- Verificar los logs al inicio: debe decir "✅ AsyncPostgresSaver inicializado".

### La memoria long-term no funciona
- Verificar que el usuario esté autenticado (user_id ≠ "anonymous").
- Verificar que `OPENAI_API_KEY` esté configurado (necesario para embeddings).
- Verificar que las tablas `store` y `store_vectors` existan en PostgreSQL.

### Error: "Embeddings failed"
- Verificar conectividad con la API de OpenAI.
- Verificar que el modelo de embeddings (`text-embedding-3-small`) esté disponible en tu cuenta.

### El streaming no funciona desde el API Gateway
- Verificar que el endpoint `/threads/{id}/runs/stream` responda con `Content-Type: text/event-stream`.
- Verificar que `X-Accel-Buffering: no` esté en los headers (necesario si hay nginx/proxy).

### Las fuentes no se muestran en el frontend
- El RAG envía `title` y `relevance_score`; el API Gateway normaliza a `source_name` y `score`.
- El frontend filtra fuentes sin nombre válido. Verificar que los documentos tengan `title` en su metadata.

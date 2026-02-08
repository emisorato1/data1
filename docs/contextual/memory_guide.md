<div align="center">

# 🧠 GUÍA DE GESTIÓN DE MEMORIA PARA SISTEMA RAG EMPRESARIAL

## Estrategias de Corto y Largo Plazo

---

**Proyecto:** Enterprise AI Platform  
**Versión:** 1.0 | **Fecha:** Febrero 2026

---

| Metadato | Valor |
|:---------|:------|
| **Autor** | Equipo de Arquitectura |
| **Clasificación** | Documento Técnico de Referencia |
| **Audiencia** | Arquitectos de Soluciones, Ingenieros ML/AI |
| **Estado** | Versión Inicial |

</div>

---

# 📋 ÍNDICE

1. [Introducción y Conceptos Fundamentales](#1-introducción-y-conceptos-fundamentales)
2. [Taxonomía de Memoria en Sistemas RAG](#2-taxonomía-de-memoria-en-sistemas-rag)
3. [Estrategias de Memoria de Corto Plazo](#3-estrategias-de-memoria-de-corto-plazo)
4. [Estrategias de Memoria de Largo Plazo](#4-estrategias-de-memoria-de-largo-plazo)
5. [Integración con Stack Tecnológico Actual](#5-integración-con-stack-tecnológico-actual)
6. [Tablas Comparativas y Análisis de Costos](#6-tablas-comparativas-y-análisis-de-costos)
7. [Recomendaciones para Enterprise AI Platform](#7-recomendaciones-para-enterprise-ai-platform)
8. [Implementación Práctica](#8-implementación-práctica)
9. [Observabilidad con Langfuse](#9-observabilidad-con-langfuse)
10. [Roadmap de Implementación](#10-roadmap-de-implementación)

---

# 1. INTRODUCCIÓN Y CONCEPTOS FUNDAMENTALES

## 1.1 ¿Por qué es Crítica la Memoria en RAG?

Los sistemas RAG tradicionales tienen una limitación fundamental: **cada consulta es independiente**. Sin memoria, el sistema:

- ❌ No recuerda conversaciones previas del usuario
- ❌ No aprende de interacciones pasadas
- ❌ No puede personalizar respuestas
- ❌ Repite información ya proporcionada
- ❌ Pierde contexto en conversaciones multi-turno

> 💡 **Analogía:** Un RAG sin memoria es como un empleado con amnesia que olvida cada conversación al terminar.

## 1.2 Tipos de Memoria en Sistemas de IA

Inspirados en la cognición humana, los sistemas de IA implementan tres tipos principales de memoria:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TAXONOMÍA DE MEMORIA EN LLM AGENTS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │  MEMORIA SEMÁNTICA  │  │ MEMORIA EPISÓDICA   │  │ MEMORIA PROCEDURAL  │  │
│  │     (Hechos)        │  │    (Eventos)        │  │    (Habilidades)    │  │
│  ├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤  │
│  │ • Conocimiento      │  │ • Historial de      │  │ • Cómo ejecutar     │  │
│  │   general           │  │   conversaciones    │  │   tareas            │  │
│  │ • Hechos sobre      │  │ • Interacciones     │  │ • Flujos de trabajo │  │
│  │   entidades         │  │   específicas       │  │ • Reglas aprendidas │  │
│  │ • Relaciones        │  │ • Contexto temporal │  │ • Patrones de uso   │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│           │                        │                        │               │
│           ▼                        ▼                        ▼               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    IMPLEMENTACIÓN TÉCNICA                            │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  Vector Stores     │  Checkpointers      │  System Prompts          │   │
│  │  Knowledge Graphs  │  Message History    │  Tool Definitions        │   │
│  │  Entity Memory     │  Session Storage    │  Learned Procedures      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1.3 Arquitectura de Memoria de Dos Capas

La práctica estándar en 2024-2025 es implementar un **sistema de memoria de dos capas**:

| Capa | Alcance | Persistencia | Propósito |
|:-----|:--------|:-------------|:----------|
| **Corto Plazo** | Sesión actual | Temporal (thread) | Mantener contexto conversacional |
| **Largo Plazo** | Cross-sesión | Permanente (BD) | Aprender de interacciones, personalizar |

---

# 2. TAXONOMÍA DE MEMORIA EN SISTEMAS RAG

## 2.1 Memoria de Corto Plazo (Short-Term Memory)

### Definición
Retención de información inmediata dentro de una sesión de conversación. Limitada al contexto actual.

### Características

| Aspecto | Descripción |
|:--------|:------------|
| **Duración** | Durante la sesión activa |
| **Almacenamiento** | In-memory o checkpointer |
| **Tamaño** | Limitado por ventana de contexto del LLM |
| **Uso** | Mantener coherencia en diálogos multi-turno |

### Tipos Principales en LangChain/LangGraph

```python
# 1. ConversationBufferMemory: Almacena el historial completo sin procesar. Útil para sesiones cortas donde el contexto íntegro es vital.
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory()

# 2. ConversationBufferWindowMemory: Mantiene una ventana deslizante de las últimas K interacciones para controlar el consumo de tokens.
from langchain.memory import ConversationBufferWindowMemory
memory = ConversationBufferWindowMemory(k=10)

# 3. ConversationSummaryMemory: Utiliza un LLM para resumir la conversación progresivamente, ideal para diálogos muy extensos.
from langchain.memory import ConversationSummaryMemory
memory = ConversationSummaryMemory(llm=llm)

# 4. LangGraph Checkpointers: El estándar moderno para persistencia de estado en agentes, permitiendo hilos persistentes y recuperación de errores.
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver(conn_string)
```

## 2.2 Memoria de Largo Plazo (Long-Term Memory)

### Definición
Retención de información a través de múltiples sesiones. Permite aprendizaje y personalización continua.

### Características

| Aspecto | Descripción |
|:--------|:------------|
| **Duración** | Permanente (hasta eliminación explícita) |
| **Almacenamiento** | Base de datos, vector store, knowledge graph |
| **Tamaño** | Virtualmente ilimitado |
| **Uso** | Personalización, aprendizaje de preferencias, historial |

### Implementaciones Comunes

| Implementación | Descripción | Caso de Uso |
|:---------------|:------------|:------------|
| **Vector Store Memory** | Embeddings de conversaciones pasadas | Búsqueda semántica de contexto histórico |
| **Entity Memory** | Extracción y almacenamiento de entidades | Recordar información sobre personas, lugares |
| **Knowledge Graph Memory** | Grafo de relaciones entre conceptos | Razonamiento complejo sobre relaciones |
| **LangGraph Store** | JSON documents en namespaces | Preferencias de usuario cross-thread |
| **Mem0** | Capa de memoria inteligente | Memoria auto-mejorable para agentes |

---

# 3. ESTRATEGIAS DE MEMORIA DE CORTO PLAZO

## 3.1 Comparativa de Estrategias

| Estrategia | Token Usage | Costo Relativo | Pérdida de Info | Latencia | Mejor Para |
|:-----------|:-----------:|:--------------:|:---------------:|:--------:|:-----------|
| **Buffer Completo** | 🔴 Alto | 🔴 Alto | ✅ Ninguna | 🔴 Alta | Conversaciones cortas |
| **Buffer Window (k=10)** | 🟡 Medio | 🟡 Medio | 🟡 Moderada | 🟡 Media | Balance general |
| **Summary Memory** | 🟢 Bajo | 🟢 Bajo* | 🟡 Detalles | 🟡 Media | Conversaciones largas |
| **Summary Buffer** | 🟡 Medio | 🟡 Medio | 🟢 Mínima | 🟡 Media | **Recomendado** |
| **Token Buffer** | 🟢 Controlado | 🟢 Predecible | 🟡 Variable | 🟢 Baja | Control preciso de costos |

> *Summary Memory tiene costo adicional por llamadas LLM para resumir

### ¿Por qué Summary Buffer es recomendado?

**Summary Buffer** combina lo mejor de dos mundos: mantiene los mensajes más recientes en su forma original (para preservar detalles críticos del contexto inmediato) mientras almacena un resumen comprimido de la conversación anterior (para no perder el hilo general).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUMMARY BUFFER: ESTRUCTURA HÍBRIDA                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Contexto enviado al LLM:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [RESUMEN] Turnos 1-15: El usuario preguntó sobre políticas de       │   │
│  │ vacaciones y RRHH respondió con los procedimientos. Luego consultó  │   │
│  │ sobre beneficios de salud y mostró interés en el plan familiar.     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [TURNO 16] Usuario: ¿Y cuánto cubre el plan dental?                 │   │
│  │ [TURNO 16] Asistente: El plan dental cubre hasta $500 anuales...    │   │
│  │ [TURNO 17] Usuario: ¿Puedo agregar a mi esposa?                     │   │
│  │ [TURNO 17] Asistente: Sí, puede agregar dependientes...             │   │
│  │ [TURNO 18] Usuario: ¿Cuál es el proceso?                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ✅ Resumen = Contexto histórico comprimido (~200-500 tokens)              │
│  ✅ Últimos K turnos = Detalles exactos del contexto reciente (~800 tok)   │
│  ✅ Total = ~1,000-1,300 tokens (vs. ~4,000 con buffer completo)           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Ventajas clave de Summary Buffer:**

| Aspecto | Beneficio |
|:--------|:----------|
| **Pérdida mínima de información** | El resumen preserva la esencia de turnos antiguos, mientras los recientes están completos |
| **Control de tokens** | Mantiene el contexto predecible (~1K tokens) independientemente de la duración de la conversación |
| **Coherencia conversacional** | El LLM entiende tanto el "dónde venimos" (resumen) como el "dónde estamos" (turnos recientes) |
| **Costo-efectivo** | Reduce tokens ~60-75% vs. buffer completo, con mínimo impacto en calidad |

### Relación entre Summary Buffer y Checkpointers

> 💡 **Concepto clave:** Summary Buffer es una **estrategia de gestión de contexto**, mientras que los Checkpointers son un **mecanismo de persistencia**. Son complementarios, no alternativos.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA COMBINADA: CHECKPOINTER + SUMMARY BUFFER           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AsyncPostgresSaver (Checkpointer)                 │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │  Persiste el STATE COMPLETO del grafo en cada super-step:     │  │   │
│  │  │  • messages: Lista completa de todos los mensajes             │  │   │
│  │  │  • retrieved_context: Documentos recuperados                   │  │   │
│  │  │  • memory_context: Preferencias, entidades                     │  │   │
│  │  │  • current_summary: Resumen acumulado (para Summary Buffer)   │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                       │   │
│  │                              ▼                                       │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │  thread_id = "session_abc123"                                  │  │   │
│  │  │  checkpoint_id = "step_47"                                     │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Summary Buffer (Estrategia de Contexto)           │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │  Antes de invocar al LLM, transforma el estado persistido:    │  │   │
│  │  │                                                                │  │   │
│  │  │  messages_for_llm = [                                          │  │   │
│  │  │      SystemMessage(content=system_prompt),                     │  │   │
│  │  │      HumanMessage(content=f"Contexto previo: {summary}"),     │  │   │
│  │  │      *messages[-k:]  # Últimos K mensajes completos            │  │   │
│  │  │  ]                                                             │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  RESULTADO:                                                                 │
│  ✅ Checkpointer: Persistencia completa para recuperación y debugging      │
│  ✅ Summary Buffer: Contexto optimizado para cada llamada al LLM           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**¿Por qué usar ambos juntos?**

| Sin Checkpointer | Con Checkpointer |
|:-----------------|:-----------------|
| ❌ Se pierde el estado si el proceso se reinicia | ✅ Estado recuperable desde PostgreSQL |
| ❌ No hay historial para debugging | ✅ Puedes "viajar en el tiempo" a cualquier step |
| ❌ Sin soporte para human-in-the-loop | ✅ Pausar y reanudar conversaciones |
| ❌ Reconstruir resumen desde cero en cada sesión | ✅ Resumen persistido y acumulativo |

| Sin Summary Buffer | Con Summary Buffer |
|:-------------------|:-------------------|
| ❌ Contexto crece indefinidamente | ✅ Contexto controlado (~1K tokens) |
| ❌ Costo de tokens aumenta linealmente | ✅ Costo predecible por turno |
| ❌ Riesgo de exceder ventana de contexto | ✅ Siempre dentro de límites |
| ❌ Latencia alta en conversaciones largas | ✅ Latencia consistente |

**Implementación combinada recomendada:**

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import trim_messages, SystemMessage

class RAGStateWithSummary(TypedDict):
    messages: Annotated[list, add_messages]
    current_summary: str  # Resumen acumulado de turnos anteriores
    # ... otros campos

async def summarize_if_needed(state: RAGStateWithSummary) -> dict:
    """Nodo que actualiza el resumen cuando hay muchos mensajes."""
    messages = state["messages"]
    
    # Si hay más de K mensajes, resumir los antiguos
    if len(messages) > 10:
        old_messages = messages[:-5]  # Todos menos los últimos 5
        
        # Generar resumen con LLM
        new_summary = await llm.ainvoke(
            f"Resume esta conversación:\n{format_messages(old_messages)}\n"
            f"Resumen previo: {state.get('current_summary', '')}"
        )
        
        return {
            "current_summary": new_summary.content,
            "messages": messages[-5:]  # Mantener solo los últimos 5
        }
    
    return {}  # Sin cambios

# El checkpointer persiste automáticamente el resumen actualizado
graph = StateGraph(RAGStateWithSummary)
graph.add_node("summarize", summarize_if_needed)
# ... otros nodos

agent = graph.compile(checkpointer=await get_checkpointer())
```

> 📌 **Recomendación para Enterprise AI Platform:** Implementar `AsyncPostgresSaver` como base de persistencia (Sección 3.2) y añadir lógica de summarization como nodo opcional del grafo. Esto permite beneficiarse de ambos mecanismos sin complejidad adicional.

## 3.2 LangGraph Checkpointers (Enfoque Recomendado 2024+)

LangChain ha deprecado las clases de memoria individuales desde v0.3.1. **LangGraph con checkpointers es el enfoque recomendado**.

### Tipos de Checkpointers

| Checkpointer | Persistencia | Producción | Async | Costo |
|:-------------|:------------:|:----------:|:-----:|:-----:|
| **MemorySaver** | ❌ In-memory | ❌ No | ✅ Sí | Gratis |
| **SqliteSaver** | ✅ Archivo | 🟡 Desarrollo | ✅ Sí | Gratis |
| **PostgresSaver** | ✅ BD | ✅ Sí | ✅ Sí | Cloud SQL |
| **AsyncPostgresSaver** | ✅ BD | ✅ Sí | ✅ Sí | Cloud SQL |

### Implementación para Enterprise AI Platform

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph
from psycopg_pool import AsyncConnectionPool

# Configuración de conexión async para producción
async def get_checkpointer():
    pool = AsyncConnectionPool(
        conninfo="postgresql://user:pass@cloudsql-instance/db",
        min_size=5,
        max_size=20
    )
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()  # Crea tablas si no existen
    return checkpointer

# Compilación del grafo con checkpointer
async def build_graph():
    checkpointer = await get_checkpointer()
    
    graph = StateGraph(RAGState)
    # ... definir nodos y edges ...
    
    return graph.compile(checkpointer=checkpointer)

# Uso con thread_id para persistencia
async def invoke_with_memory(graph, message: str, session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    result = await graph.ainvoke(
        {"message": message},
        config=config
    )
    return result
```

## 3.3 Gestión de Ventana de Contexto

### Problema: Overflow de Tokens

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EVOLUCIÓN DEL CONTEXTO                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Turno 1:  [System] [User1] [Assistant1]                   ~2K tok  │
│  Turno 5:  [System] [U1] [A1] ... [U5] [A5]               ~10K tok  │
│  Turno 20: [System] [U1] [A1] ... [U20] [A20]             ~40K tok  │
│            ──────────────────────────────────────────────           │
│                         ⚠️ LÍMITE DE CONTEXTO ⚠️                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Soluciones Implementables

| Técnica | Implementación | Impacto en Tokens | Impacto en Calidad |
|:--------|:---------------|:-----------------:|:------------------:|
| **trim_messages** | `from langchain_core.messages import trim_messages` | 🟢 -50-80% | 🟡 Pierde contexto antiguo |
| **Summarization Node** | Nodo LangGraph que resume al superar umbral | 🟢 -60-90% | 🟢 Preserva esencia |
| **Sliding Window** | Mantener solo últimos N mensajes | 🟢 -70-90% | 🟡 Corte abrupto |
| **Semantic Compression** | Embeddings + retrieval de mensajes relevantes | 🟢 -80-95% | 🟢 Contexto relevante |

### Implementación de trim_messages

```python
from langchain_core.messages import trim_messages, SystemMessage

def manage_context(messages: list, max_tokens: int = 4000):
    """Gestiona el contexto manteniendo mensajes dentro del límite."""
    return trim_messages(
        messages,
        max_tokens=max_tokens,
        strategy="last",  # Mantener los más recientes
        token_counter=len,  # O usar tiktoken para precisión
        include_system=True,  # Siempre mantener system prompt
        start_on="human",  # Empezar en mensaje humano
    )
```

---

# 4. ESTRATEGIAS DE MEMORIA DE LARGO PLAZO

## 4.1 Comparativa de Enfoques

| Enfoque | Descripción | Complejidad | Costo | Mejor Para |
|:--------|:------------|:-----------:|:-----:|:-----------|
| **Vector Store Memory** | Embeddings de conversaciones | 🟡 Media | 🟡 Medio | Contexto histórico semántico |
| **PostgreSQL Tables** | Tablas relacionales de preferencias | 🟢 Baja | 🟢 Bajo | Datos estructurados |
| **LangGraph Store** | JSON en namespaces | 🟢 Baja | 🟢 Bajo | Preferencias simples |
| **Entity Memory** | Extracción automática de entidades | 🟡 Media | 🟡 Medio | Recordar personas/lugares |
| **Knowledge Graph** | Neo4j/NetworkX | 🔴 Alta | 🔴 Alto | Relaciones complejas |
| **Mem0** | Memoria inteligente auto-mejorable | 🟡 Media | 🟡 Medio | Personalización avanzada |

## 4.2 LangGraph Store para Memoria Cross-Thread

### Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH MEMORY STORE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Namespace: ("users", "user_123", "preferences")                    │
│  ├── Key: "communication_style" → {"value": "formal", "updated":..}│
│  ├── Key: "topics_of_interest" → {"value": ["finanzas", "rrhh"]}   │
│  └── Key: "last_interaction" → {"value": "2026-02-02T21:00:00"}    │
│                                                                      │
│  Namespace: ("users", "user_123", "entities")                       │
│  ├── Key: "mentioned_people" → {"value": [{"name": "Juan",...}]}   │
│  └── Key: "mentioned_projects" → {"value": ["Proyecto Alpha"]}     │
│                                                                      │
│  Namespace: ("system", "learned_patterns")                          │
│  └── Key: "common_queries" → {"value": [...]}                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Implementación con PostgreSQL Backend

```python
from langgraph.store.postgres import PostgresStore
from langgraph.store.base import Item

async def setup_memory_store():
    store = PostgresStore(
        conn_string="postgresql://user:pass@host/db"
    )
    await store.setup()
    return store

async def save_user_preference(store, user_id: str, key: str, value: dict):
    """Guarda preferencia de usuario en memoria de largo plazo."""
    namespace = ("users", user_id, "preferences")
    await store.aput(
        namespace=namespace,
        key=key,
        value=value
    )

async def get_user_context(store, user_id: str) -> dict:
    """Recupera todo el contexto de un usuario."""
    namespace = ("users", user_id, "preferences")
    items = await store.alist(namespace=namespace)
    return {item.key: item.value for item in items}

async def search_relevant_memories(store, user_id: str, query: str):
    """Búsqueda semántica en memorias del usuario."""
    namespace_prefix = ("users", user_id)
    results = await store.asearch(
        namespace_prefix=namespace_prefix,
        query=query,  # Requiere embeddings configurados
        limit=5
    )
    return results
```

## 4.3 Mem0: Capa de Memoria Inteligente

### ¿Qué es Mem0?

Mem0 es una capa de memoria auto-mejorable para agentes LLM que:
- Identifica automáticamente información importante
- Actualiza y consolida memorias existentes
- Proporciona retrieval inteligente basado en contexto
- Se integra nativamente con LangChain/LangGraph

### Comparativa: LangGraph Store vs Mem0

| Aspecto | LangGraph Store | Mem0 |
|:--------|:----------------|:-----|
| **Almacenamiento** | Manual (put/get) | Automático (aprende) |
| **Extracción de info** | Desarrollador implementa | Automático con LLM |
| **Actualización** | Sobreescritura manual | Merge inteligente |
| **Búsqueda** | Por namespace/key | Semántica + contexto |
| **Complejidad** | 🟢 Baja | 🟡 Media |
| **Costo** | 🟢 Solo storage | 🟡 Storage + LLM calls |
| **Personalización** | 🟢 Total control | 🟡 Configuración limitada |

### Integración de Mem0 con LangGraph

```python
from mem0 import Memory
from langchain_openai import ChatOpenAI

# Configuración de Mem0 con PostgreSQL
config = {
    "vector_store": {
        "provider": "pgvector",
        "config": {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "dbname": "mem0_db"
        }
    },
    "llm": {
        "provider": "langchain",
        "config": {
            "model": "gemini-2.0-flash",
            "temperature": 0
        }
    }
}

memory = Memory.from_config(config)

# Añadir memoria automáticamente
memory.add(
    messages=[
        {"role": "user", "content": "Mi proyecto favorito es el de migración a GCP"},
        {"role": "assistant", "content": "Entendido, tomaré nota de tu preferencia"}
    ],
    user_id="user_123"
)

# Recuperar memorias relevantes
relevant_memories = memory.search(
    query="¿Qué proyectos le interesan al usuario?",
    user_id="user_123"
)

# Integración en nodo de LangGraph
def memory_enriched_node(state: RAGState, store: Memory):
    user_id = state["session_id"]
    query = state["message"]
    
    # Recuperar contexto de memoria
    memories = store.search(query, user_id=user_id, limit=5)
    
    # Enriquecer contexto
    memory_context = "\n".join([m["memory"] for m in memories])
    
    return {
        **state,
        "memory_context": memory_context
    }
```

## 4.4 Vector Store Memory con pgvector

### Arquitectura para Historial Conversacional

```sql
-- Tabla para almacenar embeddings de conversaciones
CREATE TABLE conversation_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(50) NOT NULL, -- 'user' | 'assistant'
    content TEXT NOT NULL,
    embedding vector(768), -- Matryoshka truncated
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Índice para búsqueda vectorial
CREATE INDEX ON conversation_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Índice para filtrado por usuario
CREATE INDEX ON conversation_embeddings (user_id, created_at DESC);
```

### Implementación Python

```python
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_postgres import PGVector

# Configuración del vector store para memoria
embeddings = VertexAIEmbeddings(
    model_name="text-embedding-004",
    project="your-project"
)

memory_vectorstore = PGVector(
    connection=connection_string,
    embeddings=embeddings,
    collection_name="conversation_memory",
    use_jsonb=True
)

async def store_conversation_turn(
    user_id: str,
    session_id: str,
    message: str,
    response: str
):
    """Almacena un turno de conversación en memoria vectorial."""
    
    # Crear documento combinado para embedding
    combined = f"Usuario: {message}\nAsistente: {response}"
    
    await memory_vectorstore.aadd_texts(
        texts=[combined],
        metadatas=[{
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "type": "conversation_turn"
        }]
    )

async def retrieve_relevant_history(
    user_id: str,
    query: str,
    k: int = 5
) -> list:
    """Recupera conversaciones históricas relevantes."""
    
    results = await memory_vectorstore.asimilarity_search_with_score(
        query=query,
        k=k,
        filter={"user_id": user_id}
    )
    
    return [
        {
            "content": doc.page_content,
            "score": score,
            "metadata": doc.metadata
        }
        for doc, score in results
    ]
```

---

# 5. INTEGRACIÓN CON STACK TECNOLÓGICO ACTUAL

## 5.1 Stack Actual de Enterprise AI Platform

| Componente | Tecnología | Uso en Memoria |
|:-----------|:-----------|:---------------|
| **Orquestación** | LangGraph | Gestión de estado, checkpointing |
| **LLM** | Gemini (Vertex AI) | Generación, summarization |
| **Vector Store** | PostgreSQL + pgvector | Embeddings, memoria semántica |
| **Observabilidad** | Langfuse | Traces de memoria |
| **Base de Datos** | Cloud SQL Enterprise | Persistencia de checkpoints |
| **Cache** | Redis | Cache semántico, sesiones |

## 5.2 Arquitectura de Memoria Propuesta

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DE MEMORIA - ENTERPRISE AI PLATFORM          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌──────────────────────────────────────────────────┐  │
│  │   USUARIO   │────▶│               RAG GENERATION SERVICE              │  │
│  └─────────────┘     │  ┌────────────────────────────────────────────┐  │  │
│                      │  │              LANGGRAPH AGENT                │  │  │
│                      │  │  ┌──────────────────────────────────────┐  │  │  │
│                      │  │  │         SHORT-TERM MEMORY            │  │  │  │
│                      │  │  │  • AsyncPostgresSaver (checkpoints)  │  │  │  │
│                      │  │  │  • Thread-based conversations        │  │  │  │
│                      │  │  │  • Message trimming (4K tokens)      │  │  │  │
│                      │  │  └──────────────────────────────────────┘  │  │  │
│                      │  │                     │                       │  │  │
│                      │  │                     ▼                       │  │  │
│                      │  │  ┌──────────────────────────────────────┐  │  │  │
│                      │  │  │          LONG-TERM MEMORY            │  │  │  │
│                      │  │  │  • PostgresStore (preferences)       │  │  │  │
│                      │  │  │  • pgvector (conversation history)   │  │  │  │
│                      │  │  │  • Entity extraction (opcional)      │  │  │  │
│                      │  │  └──────────────────────────────────────┘  │  │  │
│                      │  └────────────────────────────────────────────┘  │  │
│                      └──────────────────────────────────────────────────┘  │
│                                          │                                  │
│                                          ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         CLOUD SQL ENTERPRISE                          │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │  checkpoints    │  │  memory_store   │  │ conversation_embeds │   │  │
│  │  │  (LangGraph)    │  │  (preferences)  │  │    (pgvector)       │   │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                          │                                  │
│                                          ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                            LANGFUSE                                   │  │
│  │  • Memory retrieval traces  • Token usage analytics                   │  │
│  │  • Memory update events     • Cost per memory operation               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.3 Esquema de Base de Datos

```sql
-- ============================================================================
-- TABLAS PARA GESTIÓN DE MEMORIA - ENTERPRISE AI PLATFORM
-- ============================================================================

-- 1. Checkpoints de LangGraph (creada automáticamente por AsyncPostgresSaver)
-- Tabla: langgraph_checkpoints

-- 2. Memoria de largo plazo: Preferencias de usuario
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    preference_key VARCHAR(255) NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

-- 3. Memoria de largo plazo: Entidades extraídas
CREATE TABLE extracted_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL, -- 'person', 'project', 'department'
    entity_name VARCHAR(500) NOT NULL,
    entity_data JSONB,
    mention_count INTEGER DEFAULT 1,
    first_mentioned_at TIMESTAMP DEFAULT NOW(),
    last_mentioned_at TIMESTAMP DEFAULT NOW(),
    embedding vector(768)
);

-- 4. Memoria de largo plazo: Historial conversacional embebido
CREATE TABLE conversation_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    turn_number INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    summary TEXT, -- Resumen opcional del turno
    embedding vector(768),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- 5. Índices para búsqueda eficiente
CREATE INDEX idx_user_prefs_user ON user_preferences(user_id);
CREATE INDEX idx_entities_user_type ON extracted_entities(user_id, entity_type);
CREATE INDEX idx_conv_memory_user ON conversation_memory(user_id, created_at DESC);

-- Índice HNSW para búsqueda vectorial en conversaciones
CREATE INDEX idx_conv_memory_embedding ON conversation_memory 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Índice HNSW para búsqueda de entidades similares
CREATE INDEX idx_entities_embedding ON extracted_entities 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

---

# 6. TABLAS COMPARATIVAS Y ANÁLISIS DE COSTOS

## 6.1 Comparativa de Estrategias de Memoria de Corto Plazo

| Estrategia | Tokens/Turno | Costo estimado (1K conversaciones) | Latencia Adicional | Complejidad | Recomendación |
|:-----------|:------------:|:----------------------------------:|:------------------:|:-----------:|:-------------:|
| **Buffer Completo** | ~4,000 | ~$4.00 | +200ms | 🟢 Baja | ⚠️ Solo conv. cortas |
| **Window (k=10)** | ~2,000 | ~$2.00 | +100ms | 🟢 Baja | ✅ Balance |
| **Summary** | ~500 | ~$1.50* | +500ms | 🟡 Media | ✅ Conv. largas |
| **Summary Buffer** | ~1,000 | ~$1.75* | +300ms | 🟡 Media | ⭐ **Recomendado** |
| **LangGraph + Trim** | ~1,500 | ~$1.50 | +50ms | 🟢 Baja | ⭐ **Recomendado** |

> *Incluye costo de llamadas LLM para summarization

## 6.2 Comparativa de Almacenamiento de Memoria de Largo Plazo

| Solución | Costo Mensual Base | Costo por 1M Memorias | Latencia Query | Escalabilidad | Complejidad Ops |
|:---------|:------------------:|:---------------------:|:--------------:|:-------------:|:---------------:|
| **PostgreSQL + pgvector** | ~$150 (Cloud SQL) | ~$0.15 storage | <50ms | 🟡 Hasta 100M | 🟢 Baja |
| **PostgresStore (LangGraph)** | ~$150 (Cloud SQL) | ~$0.10 storage | <30ms | 🟡 Hasta 100M | 🟢 Baja |
| **Redis Stack** | ~$200 | ~$5.00 (in-memory) | <10ms | 🟡 Media | 🟡 Media |
| **Pinecone** | ~$70 (starter) | ~$0.25 | <50ms | 🟢 Alta | 🟢 Baja |
| **Mem0 (self-hosted)** | ~$200 | ~$0.20 + LLM calls | <100ms | 🟡 Media | 🟡 Media |
| **Mem0 Cloud** | ~$100+ | Pay per operation | <100ms | 🟢 Alta | 🟢 Muy baja |

## 6.3 Análisis de Costo Total por Escenario

### Escenario: 10,000 usuarios activos, 50 conversaciones/usuario/mes

| Componente | Escenario A: Básico | Escenario B: Intermedio | Escenario C: Avanzado |
|:-----------|:-------------------:|:-----------------------:|:---------------------:|
| **Short-term** | Buffer Window | LangGraph + Trim | LangGraph + Summary |
| **Long-term** | Ninguna | PostgresStore | PostgresStore + pgvector + Mem0 |
| **Storage** | ~10 GB | ~50 GB | ~100 GB |
| **Cloud SQL** | $150/mes | $200/mes | $300/mes |
| **LLM (memoria)** | $0 | $50/mes | $200/mes |
| **Redis** | $0 | $0 | $100/mes |
| **Total Mensual** | **$150** | **$250** | **$600** |
| **Funcionalidades** | ❌ Sin persistencia | ✅ Persistencia básica | ✅ Personalización completa |

## 6.4 ROI de Implementación de Memoria

| Métrica | Sin Memoria | Con Memoria Básica | Con Memoria Avanzada |
|:--------|:-----------:|:------------------:|:--------------------:|
| **Tasa de resolución 1er contacto** | ~60% | ~75% | ~85% |
| **Satisfacción usuario (NPS)** | +20 | +35 | +50 |
| **Tiempo promedio resolución** | 5 min | 3.5 min | 2.5 min |
| **Consultas repetidas** | 30% | 15% | 8% |
| **Costo operativo relativo** | 1.0x | 1.1x | 1.3x |
| **Valor para negocio** | Base | +40% | +80% |

---

# 7. RECOMENDACIONES PARA ENTERPRISE AI PLATFORM

## 7.1 Estrategia Recomendada: Implementación Progresiva

### Fase 1: Memoria de Corto Plazo (Semana 1-2)

| Componente | Decisión | Justificación |
|:-----------|:---------|:--------------|
| **Checkpointer** | AsyncPostgresSaver | Ya tenemos Cloud SQL, async para producción |
| **Gestión de contexto** | trim_messages (4K tokens) | Balance costo/calidad |
| **Persistencia** | thread_id = session_id | Alineado con estado actual |

### Fase 2: Memoria de Largo Plazo Básica (Semana 3-4)

| Componente | Decisión | Justificación |
|:-----------|:---------|:--------------|
| **Preferencias** | PostgresStore (namespaces) | Simple, nativo LangGraph |
| **Historial vectorial** | Usar pgvector existente | Sin infra adicional |
| **Entidades** | Extracción básica con LLM | Mejora personalización |

### Fase 3: Memoria Avanzada (Mes 2-3)

| Componente | Decisión | Justificación |
|:-----------|:---------|:--------------|
| **Mem0** | Evaluar integración | Auto-mejora de memoria |
| **Semantic cache** | Redis para queries similares | Reduce costos LLM |
| **Knowledge Graph** | POC si hay necesidad | Relaciones complejas |

## 7.2 Configuración Recomendada Final

```python
# config/memory_config.py
from dataclasses import dataclass
from typing import Literal

@dataclass
class MemoryConfig:
    # Short-term memory
    short_term_strategy: Literal["buffer", "window", "summary", "trim"] = "trim"
    max_context_tokens: int = 4000
    trim_strategy: Literal["first", "last"] = "last"
    
    # Long-term memory
    enable_long_term: bool = True
    preferences_backend: Literal["postgres_store", "redis", "mem0"] = "postgres_store"
    conversation_history_backend: Literal["pgvector", "none"] = "pgvector"
    max_history_per_user: int = 1000
    
    # Entity memory
    enable_entity_extraction: bool = True
    entity_extraction_model: str = "gemini-2.0-flash"
    
    # Performance
    async_operations: bool = True
    connection_pool_size: int = 20
    
    # Observability
    trace_memory_operations: bool = True
    langfuse_enabled: bool = True

# Configuración por defecto para producción
PRODUCTION_CONFIG = MemoryConfig(
    short_term_strategy="trim",
    max_context_tokens=4000,
    enable_long_term=True,
    preferences_backend="postgres_store",
    conversation_history_backend="pgvector",
    enable_entity_extraction=True,
    async_operations=True,
    trace_memory_operations=True
)
```

## 7.3 Decisión Final: Matriz de Priorización

| Funcionalidad | Prioridad | Esfuerzo | Impacto | Fase |
|:--------------|:---------:|:--------:|:-------:|:----:|
| AsyncPostgresSaver checkpointing | 🔴 Alta | 🟢 Bajo | 🔴 Alto | 1 |
| trim_messages para gestión contexto | 🔴 Alta | 🟢 Bajo | 🟡 Medio | 1 |
| PostgresStore para preferencias | 🟡 Media | 🟢 Bajo | 🟡 Medio | 2 |
| Historial en pgvector | 🟡 Media | 🟡 Medio | 🟡 Medio | 2 |
| Extracción de entidades | 🟢 Baja | 🟡 Medio | 🟡 Medio | 3 |
| Integración Mem0 | 🟢 Baja | 🔴 Alto | 🔴 Alto | 3+ |
| Semantic cache Redis | 🟢 Baja | 🟡 Medio | 🟡 Medio | 3+ |

---

# 8. IMPLEMENTACIÓN PRÁCTICA

## 8.1 Estructura de Archivos Propuesta

```
services/rag-generation/
├── src/
│   ├── agents/
│   │   ├── state.py          # RAGState actualizado con memoria
│   │   ├── graph.py          # Grafo con checkpointer
│   │   └── nodes/
│   │       ├── memory_retrieval.py    # Nodo de recuperación de memoria
│   │       └── memory_update.py       # Nodo de actualización de memoria
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── config.py         # MemoryConfig
│   │   ├── checkpointer.py   # Factory para checkpointers
│   │   ├── store.py          # PostgresStore wrapper
│   │   ├── conversation_memory.py    # Historial vectorial
│   │   └── entity_extractor.py       # Extracción de entidades
│   └── config/
│       └── memory_config.py
```

## 8.2 RAGState Actualizado con Memoria

```python
# src/agents/state.py (actualizado)
from typing import Annotated, Literal, TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

class MemoryContext(TypedDict):
    """Contexto de memoria recuperado."""
    user_preferences: dict
    relevant_history: list[dict]
    extracted_entities: list[dict]
    
class RAGState(TypedDict):
    # Identificación
    session_id: str
    user_id: str  # NUEVO: para memoria cross-session
    user_role: Literal["public", "private"]
    
    # Conversación
    message: str
    messages: Annotated[list, add_messages]
    
    # Contexto RAG
    retrieved_context: list[dict]
    
    # NUEVO: Contexto de memoria
    memory_context: Optional[MemoryContext]
    
    # Estado
    current_agent: str
    
    # Resultado
    response: str
    sources: list[dict]
    
    # Metadata
    metadata: dict
```

## 8.3 Checkpointer Factory

```python
# src/memory/checkpointer.py
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
import os

class CheckpointerFactory:
    _instance = None
    _pool = None
    _checkpointer = None
    
    @classmethod
    async def get_checkpointer(cls) -> AsyncPostgresSaver:
        if cls._checkpointer is None:
            conn_string = os.getenv("DATABASE_URL")
            
            cls._pool = AsyncConnectionPool(
                conninfo=conn_string,
                min_size=5,
                max_size=20,
                open=False  # Abrir explícitamente
            )
            await cls._pool.open()
            
            cls._checkpointer = AsyncPostgresSaver(cls._pool)
            await cls._checkpointer.setup()
        
        return cls._checkpointer
    
    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            cls._checkpointer = None
```

## 8.4 Memory Store Wrapper

```python
# src/memory/store.py
from langgraph.store.postgres import AsyncPostgresStore
from typing import Optional
import os

class MemoryStore:
    _instance = None
    _store = None
    
    @classmethod
    async def get_store(cls) -> AsyncPostgresStore:
        if cls._store is None:
            conn_string = os.getenv("DATABASE_URL")
            cls._store = AsyncPostgresStore(conn_string)
            await cls._store.setup()
        return cls._store
    
    @classmethod
    async def save_preference(
        cls, 
        user_id: str, 
        key: str, 
        value: dict
    ):
        store = await cls.get_store()
        namespace = ("users", user_id, "preferences")
        await store.aput(namespace, key, value)
    
    @classmethod
    async def get_preferences(cls, user_id: str) -> dict:
        store = await cls.get_store()
        namespace = ("users", user_id, "preferences")
        items = [item async for item in store.alist(namespace)]
        return {item.key: item.value for item in items}
    
    @classmethod
    async def save_entity(
        cls,
        user_id: str,
        entity_type: str,
        entity_name: str,
        entity_data: dict
    ):
        store = await cls.get_store()
        namespace = ("users", user_id, "entities", entity_type)
        await store.aput(namespace, entity_name, entity_data)
```

## 8.5 Nodo de Recuperación de Memoria

```python
# src/agents/nodes/memory_retrieval.py
from langfuse.decorators import observe
from ..state import RAGState, MemoryContext
from ...memory.store import MemoryStore
from ...memory.conversation_memory import ConversationMemory

@observe(name="memory_retrieval")
async def memory_retrieval_node(state: RAGState) -> dict:
    """Recupera contexto de memoria relevante para la consulta."""
    
    user_id = state.get("user_id", state["session_id"])
    query = state["message"]
    
    # 1. Recuperar preferencias del usuario
    preferences = await MemoryStore.get_preferences(user_id)
    
    # 2. Recuperar historial relevante (búsqueda semántica)
    relevant_history = await ConversationMemory.search_relevant(
        user_id=user_id,
        query=query,
        limit=5
    )
    
    # 3. Recuperar entidades mencionadas previamente
    entities = await MemoryStore.get_entities(user_id)
    
    memory_context: MemoryContext = {
        "user_preferences": preferences,
        "relevant_history": relevant_history,
        "extracted_entities": entities
    }
    
    return {"memory_context": memory_context}
```

## 8.6 Nodo de Actualización de Memoria

```python
# src/agents/nodes/memory_update.py
from langfuse.decorators import observe
from ..state import RAGState
from ...memory.store import MemoryStore
from ...memory.conversation_memory import ConversationMemory
from ...memory.entity_extractor import EntityExtractor

@observe(name="memory_update")
async def memory_update_node(state: RAGState) -> dict:
    """Actualiza la memoria de largo plazo después de una conversación."""
    
    user_id = state.get("user_id", state["session_id"])
    
    # 1. Guardar turno de conversación
    await ConversationMemory.store_turn(
        user_id=user_id,
        session_id=state["session_id"],
        user_message=state["message"],
        assistant_response=state["response"]
    )
    
    # 2. Extraer y guardar entidades mencionadas
    entities = await EntityExtractor.extract(
        text=state["message"] + " " + state["response"]
    )
    
    for entity in entities:
        await MemoryStore.save_entity(
            user_id=user_id,
            entity_type=entity["type"],
            entity_name=entity["name"],
            entity_data=entity
        )
    
    # 3. Detectar y guardar preferencias implícitas
    # (implementación futura con análisis de patrones)
    
    return state  # Sin cambios al estado, solo side effects
```

## 8.7 Grafo Actualizado con Memoria

```python
# src/agents/graph.py (actualizado)
from langgraph.graph import StateGraph, END
from .state import RAGState, InputState, OutputState
from .nodes.memory_retrieval import memory_retrieval_node
from .nodes.memory_update import memory_update_node
from ..memory.checkpointer import CheckpointerFactory

async def build_agent():
    checkpointer = await CheckpointerFactory.get_checkpointer()
    
    # Definir el grafo
    graph = StateGraph(RAGState, input=InputState, output=OutputState)
    
    # Nodos
    graph.add_node("memory_retrieval", memory_retrieval_node)
    graph.add_node("query_rewriter", query_rewriter_node)
    graph.add_node("vector_search", vector_search_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("generate_response", generate_response_node)
    graph.add_node("memory_update", memory_update_node)
    
    # Flujo con memoria
    graph.set_entry_point("memory_retrieval")
    graph.add_edge("memory_retrieval", "query_rewriter")
    graph.add_edge("query_rewriter", "vector_search")
    graph.add_edge("vector_search", "orchestrator")
    graph.add_edge("orchestrator", "generate_response")
    graph.add_edge("generate_response", "memory_update")
    graph.add_edge("memory_update", END)
    
    return graph.compile(checkpointer=checkpointer)

# Instancia global del agente
agent = None

async def get_agent():
    global agent
    if agent is None:
        agent = await build_agent()
    return agent
```

---

# 9. OBSERVABILIDAD CON LANGFUSE

## 9.1 Trazabilidad de Operaciones de Memoria

```python
# src/memory/instrumentation.py
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
import os

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

@observe(name="memory_operation")
async def traced_memory_operation(
    operation: str,
    user_id: str,
    details: dict
):
    """Wrapper para trazar operaciones de memoria."""
    
    langfuse_context.update_current_observation(
        metadata={
            "operation": operation,
            "user_id": user_id,
            **details
        }
    )
    
    # La operación real se ejecuta en el contexto
    return details

# Uso en código
@observe(name="preference_save")
async def save_preference_traced(user_id: str, key: str, value: dict):
    await MemoryStore.save_preference(user_id, key, value)
    
    langfuse_context.update_current_observation(
        metadata={
            "preference_key": key,
            "user_id": user_id
        }
    )
```

## 9.2 Métricas Clave para Dashboard

| Métrica | Descripción | Alerta si |
|:--------|:------------|:----------|
| `memory.retrieval.latency_p95` | Latencia de recuperación de memoria | > 100ms |
| `memory.retrieval.hit_rate` | Tasa de hits en memoria relevante | < 60% |
| `memory.store.write_latency_p95` | Latencia de escritura a memoria | > 200ms |
| `memory.tokens.saved_by_trim` | Tokens ahorrados por trimming | Monitoreo |
| `memory.entities.extracted_per_session` | Entidades extraídas promedio | Monitoreo |
| `memory.preferences.updates_per_user` | Actualizaciones de preferencias | Monitoreo |

## 9.3 Configuración de Traces en Langfuse

```python
# Ejemplo de trace completo con memoria
@observe()
async def handle_query(session_id: str, user_id: str, message: str):
    agent = await get_agent()
    
    config = {
        "configurable": {
            "thread_id": session_id
        }
    }
    
    # El trace incluirá automáticamente:
    # - memory_retrieval (con métricas)
    # - query_rewriter
    # - vector_search
    # - generate_response
    # - memory_update (con métricas)
    
    result = await agent.ainvoke(
        {
            "message": message,
            "session_id": session_id,
            "user_id": user_id,
            "user_role": "private"
        },
        config=config
    )
    
    return result
```

---

# 10. ROADMAP DE IMPLEMENTACIÓN

## 10.1 Timeline Propuesto

```
2026
────────────────────────────────────────────────────────────────────────────────
FEBRERO                    MARZO                      ABRIL
Sem1  Sem2  Sem3  Sem4    Sem1  Sem2  Sem3  Sem4    Sem1  Sem2  Sem3  Sem4
 │     │     │     │       │     │     │     │       │     │     │     │
 └─────┴─────┴─────┴───────┴─────┴─────┴─────┴───────┴─────┴─────┴─────┘
 │─── FASE 1 ───│         │─── FASE 2 ─────│        │─── FASE 3 ───────│
 Short-term                Long-term                  Avanzado
 Memory                    Memory                     (Opcional)

FASE 1 (Febrero Sem 1-2):
├── AsyncPostgresSaver setup
├── trim_messages implementación  
├── Tests de persistencia
└── Langfuse traces básicos

FASE 2 (Febrero Sem 3 - Marzo Sem 2):
├── PostgresStore para preferencias
├── Historial conversacional pgvector
├── Nodos memory_retrieval/update
└── Tests de integración

FASE 3 (Marzo Sem 3 - Abril):
├── Extracción de entidades
├── Evaluación Mem0
├── Semantic cache Redis
└── Optimización y tuning
```

## 10.2 Checklist de Implementación

### Fase 1: Memoria de Corto Plazo
- [ ] Instalar `langgraph-checkpoint-postgres`
- [ ] Crear `CheckpointerFactory` con connection pooling
- [ ] Actualizar `graph.py` para usar checkpointer
- [ ] Implementar `trim_messages` en estado
- [ ] Configurar `thread_id` = `session_id`
- [ ] Agregar tests de persistencia de sesión
- [ ] Verificar traces en Langfuse

### Fase 2: Memoria de Largo Plazo
- [ ] Crear tablas SQL según esquema
- [ ] Implementar `MemoryStore` wrapper
- [ ] Crear `ConversationMemory` con pgvector
- [ ] Implementar nodo `memory_retrieval`
- [ ] Implementar nodo `memory_update`
- [ ] Actualizar `RAGState` con `MemoryContext`
- [ ] Tests de recuperación semántica
- [ ] Dashboard en Langfuse

### Fase 3: Memoria Avanzada
- [ ] POC de extracción de entidades
- [ ] Evaluación de Mem0
- [ ] Implementar semantic cache
- [ ] Benchmarks de performance
- [ ] Documentación final

## 10.3 Métricas de Éxito

| Métrica | Objetivo Fase 1 | Objetivo Fase 2 | Objetivo Fase 3 |
|:--------|:---------------:|:---------------:|:---------------:|
| **Persistencia de sesión** | 100% | 100% | 100% |
| **Latencia adicional memoria** | <50ms | <100ms | <150ms |
| **Tasa contexto relevante** | N/A | >70% | >85% |
| **Reducción queries repetidas** | N/A | -20% | -40% |
| **Satisfacción usuario** | Baseline | +15% | +30% |

---

# ANEXO A: REFERENCIAS Y DOCUMENTACIÓN

## Documentación Oficial

| Recurso | URL | Versión |
|:--------|:----|:--------|
| LangGraph Memory | https://langchain-ai.github.io/langgraph/concepts/memory/ | 2025 |
| LangGraph Persistence | https://langchain-ai.github.io/langgraph/concepts/persistence/ | 2025 |
| LangChain Memory (Legacy) | https://python.langchain.com/docs/modules/memory/ | v0.2 |
| pgvector | https://github.com/pgvector/pgvector | 0.7+ |
| Langfuse Tracing | https://langfuse.com/docs/tracing | 2025 |
| Mem0 Documentation | https://docs.mem0.ai/ | 2025 |

## Papers y Artículos Relevantes

1. **"Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory"** - arXiv 2025
2. **"A Survey on the Memory Mechanism of Large Language Model based Agents"** - arXiv 2024
3. **"Retrieval-Augmented Generation for Large Language Models"** - Survey 2024

---

# ANEXO B: GLOSARIO

| Término | Definición |
|:--------|:-----------|
| **Checkpointer** | Componente que persiste el estado del grafo LangGraph |
| **Thread** | Identificador único de una conversación persistida |
| **Namespace** | Organización jerárquica de memorias en LangGraph Store |
| **trim_messages** | Función para reducir mensajes respetando límites de tokens |
| **Semantic Memory** | Memoria de hechos y conocimiento general |
| **Episodic Memory** | Memoria de eventos e interacciones específicas |
| **Procedural Memory** | Memoria de cómo ejecutar tareas |
| **Mem0** | Capa de memoria inteligente auto-mejorable para LLM agents |

---

<div align="center">

**Documento generado para Enterprise AI Platform**  
**Febrero 2026**

</div>

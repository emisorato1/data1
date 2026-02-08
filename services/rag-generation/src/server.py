"""Servidor FastAPI custom para RAG Generation.

Reemplaza `langgraph dev` para proveer control completo del lifecycle,
incluyendo persistencia de conversaciones con AsyncPostgresSaver.

Endpoints (compatibles con la API Gateway existente):
  GET  /info                              → Health check
  POST /threads                           → Crear/reconocer thread
  POST /threads/{id}/runs                 → Ejecutar grafo (async)
  GET  /threads/{id}/runs/{run_id}/join   → Esperar resultado del run
  POST /threads/{id}/runs/stream          → Stream de ejecución (SSE)

Persistencia:
  - Checkpointer (AsyncPostgresSaver): Conversaciones en PostgreSQL
  - Store (AsyncPostgresStore): Long-term memory con búsqueda semántica

Uso:
  uvicorn src.server:app --host 0.0.0.0 --port 2024

Pensado para Kubernetes:
  - Startup/shutdown con lifecycle hooks
  - Connection pools async con límites configurables
  - Health check en /info y /ok
"""

import os
import json
import uuid
import asyncio
import logging
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore

from src.agents.graph import create_graph_builder

logger = logging.getLogger(__name__)

# =============================================================================
# Configuración
# =============================================================================

POSTGRES_URI = os.environ.get("POSTGRES_URI", "")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")


# =============================================================================
# Serialización de objetos LangChain → JSON
# =============================================================================

def _make_serializable(obj: Any) -> Any:
    """Convierte objetos LangChain/Pydantic a tipos JSON-serializables.

    Maneja recursivamente dicts, listas y objetos con model_dump/dict/content.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "content"):
        result = {"content": obj.content}
        if hasattr(obj, "type"):
            result["type"] = obj.type
        return result
    return str(obj)


# =============================================================================
# Almacenamiento de runs en memoria
# =============================================================================

class RunManager:
    """Gestiona runs asíncronos del grafo.

    Almacena tareas asyncio y sus resultados para el patrón
    POST /runs → GET /join.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}
        self._results: dict[str, Any] = {}

    async def start_run(
        self,
        run_id: str,
        graph: Any,
        input_data: dict,
        config: dict,
    ) -> None:
        """Inicia la ejecución del grafo en background."""
        task = asyncio.create_task(
            self._execute(run_id, graph, input_data, config)
        )
        self._tasks[run_id] = task

    async def _execute(
        self,
        run_id: str,
        graph: Any,
        input_data: dict,
        config: dict,
    ) -> None:
        """Ejecuta el grafo y almacena el resultado."""
        try:
            result = await graph.ainvoke(input_data, config)
            self._results[run_id] = _make_serializable(result)
        except Exception as e:
            logger.error(f"Error ejecutando run {run_id}: {e}")
            self._results[run_id] = {"error": str(e)}

    async def join(self, run_id: str, timeout: float = 120.0) -> dict | None:
        """Espera a que un run termine y retorna su resultado."""
        task = self._tasks.pop(run_id, None)
        if task is not None:
            try:
                await asyncio.wait_for(task, timeout=timeout)
            except asyncio.TimeoutError:
                task.cancel()
                return {"error": "Run timed out"}

        return self._results.pop(run_id, None)


# =============================================================================
# Application Lifespan (startup / shutdown)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle de la aplicación: inicializa y cierra recursos."""

    if not POSTGRES_URI:
        raise RuntimeError(
            "POSTGRES_URI no está configurado. "
            "Establecer la variable de entorno antes de iniciar el servidor."
        )

    logger.info("🚀 Iniciando RAG Generation server...")

    # 1. Checkpointer — persistencia de conversaciones
    async with AsyncPostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer:
        await checkpointer.setup()
        logger.info("✅ AsyncPostgresSaver inicializado (tablas verificadas)")

        # 2. Store — long-term memory con búsqueda semántica
        async with AsyncPostgresStore.from_conn_string(
            POSTGRES_URI,
            index={
                "embed": f"openai:{EMBEDDING_MODEL}",
                "dims": 1536,
                "fields": ["$"],
            },
        ) as store:
            await store.setup()
            logger.info("✅ AsyncPostgresStore inicializado (tablas verificadas)")

            # 3. Compilar grafo con persistencia
            graph_builder = create_graph_builder()
            graph = graph_builder.compile(
                checkpointer=checkpointer,
                store=store,
            )
            logger.info("✅ Grafo RAG compilado con checkpointer + store")

            # Guardar en app.state
            app.state.graph = graph
            app.state.run_manager = RunManager()

            logger.info("🟢 RAG Generation server listo en puerto 2024")

            yield

    # Shutdown — los context managers cierran los pools automáticamente
    logger.info("🛑 RAG Generation server detenido")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="RAG Generation Service",
    description="Servicio RAG multi-agente con persistencia PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)


# =============================================================================
# Health Check
# =============================================================================

@app.get("/info")
async def info():
    """Health check compatible con docker-compose healthcheck."""
    return {
        "version": "1.0.0",
        "status": "ok",
        "persistence": "postgresql",
    }


@app.get("/ok")
async def health():
    """Health check simple."""
    return {"ok": True}


# =============================================================================
# Thread Management
# =============================================================================

@app.post("/threads")
async def create_thread(request: Request):
    """Crear o reconocer un thread.

    Con checkpointer, los threads son implícitos: existen cuando hay
    un checkpoint para ese thread_id. Este endpoint es un no-op que
    mantiene compatibilidad con la API Gateway.
    """
    body = await request.json()
    thread_id = body.get("thread_id", str(uuid.uuid4()))

    return JSONResponse(
        content={
            "thread_id": thread_id,
            "metadata": body.get("metadata", {}),
            "status": "ok",
        },
        status_code=200,
    )


# =============================================================================
# Run Management (no-streaming)
# =============================================================================

@app.post("/threads/{thread_id}/runs")
async def create_run(thread_id: str, request: Request):
    """Ejecutar el grafo de forma asíncrona.

    Inicia la ejecución en background y retorna un run_id.
    Usar GET /threads/{thread_id}/runs/{run_id}/join para obtener el resultado.
    """
    body = await request.json()
    input_data = body.get("input", {})
    config = body.get("config", {})

    # Inyectar thread_id en configurable para el checkpointer
    configurable = config.get("configurable", {})
    configurable["thread_id"] = thread_id
    config["configurable"] = configurable

    run_id = str(uuid.uuid4())
    run_manager: RunManager = request.app.state.run_manager

    await run_manager.start_run(
        run_id=run_id,
        graph=request.app.state.graph,
        input_data=input_data,
        config=config,
    )

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "status": "pending",
    }


@app.get("/threads/{thread_id}/runs/{run_id}/join")
async def join_run(thread_id: str, run_id: str, request: Request):
    """Esperar a que un run termine y obtener el resultado.

    Retorna el estado final del grafo envuelto en {"values": {...}}.
    """
    run_manager: RunManager = request.app.state.run_manager
    result = await run_manager.join(run_id)

    if result is None:
        return JSONResponse(
            content={"error": "Run not found"},
            status_code=404,
        )

    if "error" in result:
        return JSONResponse(
            content={"error": result["error"]},
            status_code=500,
        )

    return {"values": result}


# =============================================================================
# Streaming (SSE)
# =============================================================================

@app.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, request: Request):
    """Ejecutar el grafo en modo streaming (Server-Sent Events).

    Emite eventos compatibles con el formato esperado por rag_client.py:
      event: events
      data: {"event": "on_chat_model_stream", "data": {...}, "metadata": {...}}
    """
    body = await request.json()
    input_data = body.get("input", {})
    config = body.get("config", {})
    stream_mode = body.get("stream_mode", "events")

    # Inyectar thread_id en configurable
    configurable = config.get("configurable", {})
    configurable["thread_id"] = thread_id
    config["configurable"] = configurable

    graph = request.app.state.graph

    async def event_generator():
        """Genera eventos SSE desde astream_events del grafo."""
        final_state = {}

        try:
            async for event in graph.astream_events(
                input_data, config, version="v2"
            ):
                event_type = event.get("event", "")
                event_name = event.get("name", "")

                # Serializar el evento completo
                serialized = _make_serializable(event)

                # Emitir como SSE con event type = stream_mode
                data_str = json.dumps(serialized, ensure_ascii=False)
                yield f"event: {stream_mode}\ndata: {data_str}\n\n"

                # Capturar estado final del grafo raíz
                if event_type == "on_chain_end" and not event.get("parent_ids"):
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict):
                        final_state = output

        except Exception as e:
            logger.error(f"Error en streaming: {e}")
            error_data = json.dumps(
                {"event": "error", "data": {"error": str(e)}}
            )
            yield f"event: {stream_mode}\ndata: {error_data}\n\n"

        # Evento final de cierre
        end_event = {
            "event": "on_chain_end",
            "name": "rag_generation",
            "data": {"output": _make_serializable(final_state)},
            "metadata": {},
        }
        end_str = json.dumps(end_event, ensure_ascii=False)
        yield f"event: {stream_mode}\ndata: {end_str}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

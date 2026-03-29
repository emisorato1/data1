"""Nodo generate: generación de respuesta RAG con Gemini.

Genera la respuesta final del pipeline RAG usando GeminiClient.
Soporta streaming (yield tokens incrementalmente) y generación completa.
Incluye metadata: sources usadas, latencia, y tokens consumidos.

Si no hay contexto relevante, retorna respuesta de fallback explícita
en lugar de arriesgar una alucinación.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage

from src.config.settings import settings
from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.llm.prompts.system_prompt import RAG_FALLBACK_MESSAGE, build_rag_prompt
from src.infrastructure.observability.langfuse_client import observe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

_FALLBACK_RESPONSE = RAG_FALLBACK_MESSAGE

_GREETING_RESPONSE = "¡Hola! Soy el asistente de documentación bancaria interna. ¿En qué puedo ayudarte hoy?"

# ── Módulo-level client (lazy init via factory) ──────────────────────

_client: GeminiClient | None = None


def _get_client() -> GeminiClient:
    """Retorna el GeminiClient singleton del módulo.

    Permite inyección en tests vía ``set_generate_client()``.
    """
    global _client
    if _client is None:
        _client = GeminiClient(model=GeminiModel.FLASH)
    return _client


def set_generate_client(client: GeminiClient | None) -> None:
    """Inyecta un GeminiClient custom (para tests o configuración).

    Pasar ``None`` resetea al default (lazy init).
    """
    global _client
    _client = client


# ── Helpers ──────────────────────────────────────────────────────────


def _build_sources_text(sources: list[dict]) -> str:
    """Formatea la lista de sources como texto numerado para el prompt."""
    if not sources:
        return "Sin fuentes disponibles."
    lines = []
    for src in sources:
        idx = src.get("index", "?")
        name = src.get("document_name", "Documento desconocido")
        page = src.get("page", "N/A")
        lines.append(f"{idx}. {name} (p.{page})")
    return "\n".join(lines)


def _estimate_tokens(text: str) -> int:
    """Estimación rápida de tokens (1 token ~ 4 caracteres en español)."""
    return len(text) // 4


def format_user_memories(user_memories: list[dict]) -> str:
    """Formatea la lista de memorias limitando su longitud total.

    Aplica el peso de memorias vs documentos truncando si excede el
    límite configurado en settings.memory_max_chars.
    """
    if not user_memories:
        return ""

    memories_list: list[str] = []
    current_chars = 0
    max_chars = settings.memory_max_chars

    for m in user_memories:
        content = m.get("content", "")
        if not content:
            continue

        line = f"- {content}"
        # Si sumar la siguiente memoria excede el límite (y ya tenemos al menos una), paramos
        if current_chars + len(line) > max_chars and memories_list:
            logger.info("generate: Truncando memorias para respetar memory_max_chars (%d)", max_chars)
            break

        memories_list.append(line)
        current_chars += len(line) + 1  # +1 por el salto de línea

    return "\n".join(memories_list)


# ── Nodo principal ───────────────────────────────────────────────────


@observe(name="rag_generate")
async def generate_node(state: RAGState, config: dict | None = None) -> dict:
    """Genera la respuesta RAG con citaciones usando Gemini Flash.

    Acepta ``config`` de LangGraph para propagar callbacks de streaming.

    Returns
    -------
    dict
        response: str con la respuesta generada.
        messages: list con AIMessage para el historial.
        sources: list[dict] propagadas desde assemble_context.
    """
    query = state.get("query", "")
    query_type = state.get("query_type", "consulta")

    # ── Saludo: respuesta directa sin LLM ────────────────────────
    if query_type == "saludo":
        logger.info("generate: saludo detectado, respuesta directa")
        return {
            "response": _GREETING_RESPONSE,
            "messages": [AIMessage(content=_GREETING_RESPONSE)],
        }

    # ── Sin contexto: fallback explícito ─────────────────────────
    context_text = state.get("context_text", "")
    sources = state.get("sources", [])

    if not context_text.strip():
        logger.warning("generate: sin contexto disponible, retornando fallback")
        return {
            "response": _FALLBACK_RESPONSE,
            "messages": [AIMessage(content=_FALLBACK_RESPONSE)],
            "sources": [],
        }

    # ── Generación con contexto ──────────────────────────────────
    sources_text = _build_sources_text(sources)
    user_memories = state.get("user_memories", [])

    # Formatear las memorias respetando el límite de peso
    memories_text = format_user_memories(user_memories)

    prompt = build_rag_prompt(
        context=context_text,
        sources=sources_text,
        query=query,
        user_memories=memories_text,
    )

    client = _get_client()

    start_time = time.monotonic()
    # Pasamos config para que astream_events capture tokens individuales
    response_text = await client.generate(prompt, config=config)
    latency_ms = (time.monotonic() - start_time) * 1000

    input_tokens = _estimate_tokens(prompt)
    output_tokens = _estimate_tokens(response_text)

    logger.info(
        "generate: respuesta generada en %.0fms, ~%d tokens entrada, ~%d tokens salida",
        latency_ms,
        input_tokens,
        output_tokens,
    )

    return {
        "response": response_text,
        "messages": [AIMessage(content=response_text)],
        "sources": sources,
    }


@observe(name="rag_generate_stream")
async def generate_stream_node(state: RAGState) -> AsyncIterator[dict]:
    """Versión streaming del nodo generate.

    Yield tokens incrementalmente para SSE. Acumula la respuesta
    completa al final para actualizar el estado.

    Yields
    ------
    dict
        Actualizaciones parciales del estado con tokens incrementales.
    """
    query = state.get("query", "")
    query_type = state.get("query_type", "consulta")

    # ── Saludo: yield directo ────────────────────────────────────
    if query_type == "saludo":
        yield {
            "response": _GREETING_RESPONSE,
            "messages": [AIMessage(content=_GREETING_RESPONSE)],
        }
        return

    # ── Sin contexto: fallback ───────────────────────────────────
    context_text = state.get("context_text", "")
    sources = state.get("sources", [])

    if not context_text.strip():
        yield {
            "response": _FALLBACK_RESPONSE,
            "messages": [AIMessage(content=_FALLBACK_RESPONSE)],
            "sources": [],
        }
        return

    # ── Streaming con contexto ───────────────────────────────────
    sources_text = _build_sources_text(sources)
    user_memories = state.get("user_memories", [])

    # Formatear las memorias respetando el límite de peso
    memories_text = format_user_memories(user_memories)

    prompt = build_rag_prompt(
        context=context_text,
        sources=sources_text,
        query=query,
        user_memories=memories_text,
    )

    client = _get_client()

    start_time = time.monotonic()
    accumulated: list[str] = []

    async for token in client.generate_stream(prompt):
        accumulated.append(token)
        # Emitimos el progreso parcial para que el streaming sea fluido
        yield {
            "response": "".join(accumulated),
        }

    full_response = "".join(accumulated)
    latency_ms = (time.monotonic() - start_time) * 1000

    logger.info(
        "generate_stream: flujo finalizado en %.0fms, %d chunks",
        latency_ms,
        len(accumulated),
    )

    # Actualización final con metadata completa
    yield {
        "response": full_response,
        "messages": [AIMessage(content=full_response)],
        "sources": sources,
    }

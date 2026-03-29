"""Nodo respond_greeting: genera respuesta natural a saludos con Gemini Flash Lite.

Reemplaza la respuesta hardcodeada de respond_blocked para saludos.
Invoca el LLM con un prompt minimalista para generar una respuesta
conversacional y contextual al saludo específico del usuario.

Incluye fallback hardcodeado si el LLM falla (timeout, error).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage

from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.llm.prompts.system_prompt import build_greeting_prompt
from src.infrastructure.observability.langfuse_client import observe

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

_GREETING_FALLBACK = (
    "¡Hola! Soy el asistente de documentación bancaria interna de Banco Macro. ¿En qué puedo ayudarte hoy?"
)

# ── Module-level LLM client (lazy init) ──────────────────────────────

_llm_client: GeminiClient | None = None


def _get_llm_client() -> GeminiClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = GeminiClient(model=GeminiModel.FLASH_LITE, temperature=0.7)
    return _llm_client


def set_greeting_llm_client(client: GeminiClient | None) -> None:
    """Inyecta un GeminiClient custom (para tests)."""
    global _llm_client
    _llm_client = client


# ── Nodo principal ────────────────────────────────────────────────────


@observe(name="rag_respond_greeting")
async def respond_greeting_node(state: RAGState) -> dict:
    """Genera una respuesta natural al saludo del usuario.

    Invoca Gemini Flash Lite con un prompt minimalista.
    Si el LLM falla, retorna un fallback hardcodeado.
    """
    query: str = state.get("query", "")

    try:
        client = _get_llm_client()
        prompt = build_greeting_prompt(query)
        text = await client.generate(prompt)
        logger.info("respond_greeting: LLM response generated, query=%.80s", query)
    except Exception:
        logger.exception("respond_greeting: LLM failed, using fallback")
        text = _GREETING_FALLBACK

    return {
        "response": text,
        "messages": [AIMessage(content=text)],
    }

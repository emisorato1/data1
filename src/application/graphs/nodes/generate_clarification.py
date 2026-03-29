"""Nodo generate_clarification: genera opciones de clarificación estructuradas.

Se ejecuta cuando ambiguity_detector clasifica una query como AMBIGUOUS.
Usa solo la metadata de los documentos recuperados (títulos y áreas),
NO el contenido completo de los chunks, para evitar que el LLM responda
directamente en lugar de pedir clarificación.

El formato de salida incluye opciones numeradas (1., 2., etc.) compatibles
con el evaluador _OPTIONS_RE de evals/runner/evaluator.py.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage

from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.llm.prompts.clarification_prompt import (
    CLARIFICATION_SYSTEM_PROMPT,
    build_clarification_prompt,
)
from src.infrastructure.observability.langfuse_client import observe

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# Respuesta de fallback si el LLM falla — garantiza formato con opciones
_FALLBACK_CLARIFICATION = (
    "Tu consulta puede referirse a varios temas. ¿Podrías especificar qué necesitás?\n"
    "1. Información general sobre el tema\n"
    "2. Proceso o trámite relacionado\n"
    "¿Cuál de estas opciones te interesa?"
)

# ── Module-level LLM client (lazy init) ──────────────────────────────

_llm_client: GeminiClient | None = None


def _get_llm_client() -> GeminiClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = GeminiClient(model=GeminiModel.FLASH_LITE, temperature=0.3)
    return _llm_client


def set_clarification_llm_client(client: GeminiClient | None) -> None:
    """Inyecta un GeminiClient custom (para tests)."""
    global _llm_client
    _llm_client = client


# ── Helpers ──────────────────────────────────────────────────────────


def _extract_topics_from_chunks(reranked_chunks: list[dict]) -> list[str]:
    """Extrae temas únicos de la metadata de chunks (sin contenido).

    Prioriza el campo `area_funcional` y `title` de cada chunk.
    Limita a 4 temas para no sobrecargar el prompt de clarificación.
    """
    seen: set[str] = set()
    topics: list[str] = []

    for chunk in reranked_chunks:
        area = chunk.get("area_funcional") or chunk.get("metadata", {}).get("area_funcional", "")
        title = chunk.get("title") or chunk.get("metadata", {}).get("title", "")

        # Construir etiqueta: área + título si están disponibles
        if area and title and area.lower() not in title.lower():
            label = f"{area}: {title}"
        elif title:
            label = title
        elif area:
            label = area
        else:
            continue

        if label not in seen:
            seen.add(label)
            topics.append(label)

        if len(topics) >= 4:
            break

    return topics


# ── Nodo principal ────────────────────────────────────────────────────


@observe(name="rag_generate_clarification")
async def generate_clarification_node(state: RAGState) -> dict:
    """Genera una respuesta de clarificación con opciones numeradas.

    La respuesta usa solo metadata de documentos recuperados, garantizando
    que el LLM no puede responder directamente con el contenido.
    """
    query: str = state.get("query", "")
    reranked_chunks: list[dict] = state.get("reranked_chunks", [])

    topics = _extract_topics_from_chunks(reranked_chunks)

    # Si no hay topics disponibles, usar temas genéricos del dominio
    if not topics:
        topics = [
            "Información general sobre el tema",
            "Proceso o trámite relacionado",
        ]

    user_message = build_clarification_prompt(query=query, topics=topics)

    try:
        client = _get_llm_client()
        # Concatenar system prompt + user message para Gemini Flash Lite
        full_prompt = f"{CLARIFICATION_SYSTEM_PROMPT}\n\n{user_message}"
        response_text = await client.generate(full_prompt)
        response_text = response_text.strip()
    except Exception:
        logger.exception("generate_clarification: LLM failed, using fallback")
        response_text = _FALLBACK_CLARIFICATION

    logger.info(
        "generate_clarification: query=%.80s topics=%s",
        query,
        topics,
    )

    return {
        "response": response_text,
        "messages": [AIMessage(content=response_text)],
        "needs_clarification": True,
        # Guardamos la query original para que el siguiente turno sepa de qué hablamos
        "query": query, 
    }

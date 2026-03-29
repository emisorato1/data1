"""Nodo respond_blocked: respuesta predefinida para queries bloqueadas o fuera de dominio.

Maneja dos tipos de query que no requieren retrieval:
- "fuera_dominio": respuesta indicando que la query esta fuera del alcance.
- "blocked" / otros: respuesta de bloqueo por guardrail de entrada.

Nota: "saludo" ya no llega a este nodo — es manejado por respond_greeting_node.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

_OUT_OF_DOMAIN_RESPONSE = (
    "Esa consulta está fuera de mi área de conocimiento. "
    "Estoy preparado para responder preguntas sobre documentación "
    "bancaria interna, políticas, procedimientos y temas de RRHH."
)

_BLOCKED_RESPONSE = (
    "Lo siento, no puedo procesar esta consulta. "
    "Por favor, reformulá tu pregunta sobre temas relacionados "
    "con las políticas y procedimientos del banco."
)


def respond_blocked_node(state: RAGState) -> dict:
    """Genera respuesta para queries bloqueadas o fuera de dominio."""
    query_type = state.get("query_type", "blocked")

    text = _OUT_OF_DOMAIN_RESPONSE if query_type == "fuera_dominio" else _BLOCKED_RESPONSE

    logger.info("respond_blocked: query_type=%s", query_type)

    return {
        "response": text,
        "messages": [AIMessage(content=text)],
    }

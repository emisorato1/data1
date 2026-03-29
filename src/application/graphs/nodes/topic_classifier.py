"""Nodo topic_classifier: clasifica queries por dominio tematico.

Segundo nivel de clasificacion post-input-guardrail que usa LLM (Gemini
Flash) con few-shot para detectar queries fuera del dominio bancario con
mayor precision que la heuristica de keywords de classify_intent.

Ubicacion en el grafo: classify_intent -> guardrail_input -> topic_classifier -> [routing]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.config.topic_config import topic_config
from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.observability.langfuse_client import observe
from src.infrastructure.security.guardrails.topic_guard import (
    TopicCategory,
    TopicGuard,
)

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# ── Module-level guard (lazy init via factory) ───────────────────────

_guard: TopicGuard | None = None


def _get_guard() -> TopicGuard:
    """Retorna el TopicGuard singleton del modulo.

    Usa Gemini Flash para clasificacion con few-shot prompting.
    Permite inyeccion en tests via ``set_topic_guard()``.
    """
    global _guard
    if _guard is None:
        client = GeminiClient(model=GeminiModel.FLASH, temperature=0.0)
        from src.config.settings import settings

        enable_llm = settings.environment != "development"
        _guard = TopicGuard(llm_client=client, enable_llm=enable_llm)
    return _guard


def set_topic_guard(guard: TopicGuard | None) -> None:
    """Inyecta un TopicGuard custom (para tests o configuracion).

    Pasar ``None`` resetea al default (lazy init).
    """
    global _guard
    _guard = guard


# ── Nodo principal ───────────────────────────────────────────────────


@observe(name="rag_topic_classifier")
async def topic_classifier_node(state: RAGState) -> dict:
    """Clasifica la query por dominio tematico usando LLM.

    - Saludos y queries ya bloqueadas se saltan.
    - ON_TOPIC: continua pipeline sin cambios.
    - OFF_TOPIC: cortocircuita con query_type="fuera_dominio".
    - AMBIGUOUS: continua pipeline con warning log.

    Returns
    -------
    dict
        - guardrail_passed: bool
        - query_type: str (solo cambia si OFF_TOPIC)
        - response: str (solo si OFF_TOPIC — mensaje de deflexion)
    """
    query = state.get("query", "")
    query_type = state.get("query_type", "consulta")

    # Skip: solo saludos y bloqueados; fuera_dominio se evalua con LLM
    if query_type in ("saludo", "blocked"):
        logger.debug("topic_classifier: skipping, query_type=%s", query_type)
        return {}  # No modificar estado - preservar guardrail_passed del nodo anterior

    guard = _get_guard()
    result = await guard.classify(query)

    if result.category == TopicCategory.ON_TOPIC:
        logger.debug("topic_classifier: ON_TOPIC query=%.80s", query)
        return {"guardrail_passed": True, "query_type": "consulta"}

    if result.category == TopicCategory.OFF_TOPIC:
        logger.info(
            "topic_classifier: OFF_TOPIC query=%.80s reason=%s",
            query,
            result.explanation,
        )
        return {
            "guardrail_passed": False,
            "query_type": "fuera_dominio",
            "response": topic_config.deflection_response,
        }

    # AMBIGUOUS: let it through with a warning
    logger.warning(
        "topic_classifier: AMBIGUOUS query=%.80s reason=%s",
        query,
        result.explanation,
    )
    return {"guardrail_passed": True}

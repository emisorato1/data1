"""Nodo guardrail_input: validación de seguridad de la query del usuario.

Ejecuta validación doble capa (pattern matching + LLM classifier) antes
de que la query llegue al pipeline de retrieval/generación.

Si se detecta una amenaza, cortocircuita el pipeline con un mensaje seguro
predefinido en lugar de lanzar una excepción — el usuario recibe una
respuesta amable, no un error.

Ubicación en el grafo: classify_intent → guardrail_input → [routing]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.observability.langfuse_client import observe
from src.infrastructure.security.guardrails.input_validator import (
    InputValidator,
    ThreatCategory,
)

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# ── Respuestas seguras predefinidas ──────────────────────────────────

_BLOCKED_RESPONSES: dict[ThreatCategory, str] = {
    ThreatCategory.PROMPT_INJECTION: (
        "No puedo procesar esta consulta. Si necesitás información sobre "
        "políticas o procedimientos bancarios, por favor reformulá tu pregunta."
    ),
    ThreatCategory.JAILBREAK: (
        "No puedo procesar esta consulta. Estoy diseñado para responder "
        "preguntas sobre documentación bancaria interna. ¿En qué puedo ayudarte?"
    ),
    ThreatCategory.QUERY_TOO_LONG: (
        "Tu consulta es demasiado larga. Por favor, reformulala de forma más concisa (máximo 2000 caracteres)."
    ),
    ThreatCategory.TOKEN_SMUGGLING: (
        "Por seguridad, no proceso tokens ni credenciales de autenticación. "
        "Si tenés consultas sobre configuración de accesos, contactá al área de IT."
    ),
}

_DEFAULT_BLOCKED_RESPONSE = (
    "No puedo procesar esta consulta. Por favor, reformulá tu pregunta "
    "sobre temas relacionados con la documentación bancaria."
)

# ── Module-level validator (lazy init via factory) ───────────────────

_validator: InputValidator | None = None


def _get_validator() -> InputValidator:
    """Retorna el InputValidator singleton del módulo.

    Usa Gemini Flash Lite para el clasificador LLM — ultra-baja latencia.
    Permite inyección en tests vía ``set_input_validator()``.
    """
    global _validator
    if _validator is None:
        client = GeminiClient(model=GeminiModel.FLASH_LITE, temperature=0.0)
        from src.config.settings import settings

        enable_llm = settings.environment != "development"
        _validator = InputValidator(llm_client=client, enable_llm=enable_llm)
    return _validator


def set_input_validator(validator: InputValidator | None) -> None:
    """Inyecta un InputValidator custom (para tests o configuración).

    Pasar ``None`` resetea al default (lazy init).
    """
    global _validator
    _validator = validator


# ── Nodo principal ───────────────────────────────────────────────────


@observe(name="rag_validate_input")
async def validate_input_node(state: RAGState) -> dict:
    """Valida la query del usuario contra amenazas de seguridad.

    Si la query es segura, retorna ``guardrail_passed=True`` sin modificar
    el flujo. Si es insegura, retorna ``guardrail_passed=False`` con
    ``query_type`` cambiado a ``"blocked"`` para cortocircuitar al nodo
    ``respond_blocked``.

    Returns
    -------
    dict
        - guardrail_passed: bool
        - query_type: str (solo se cambia si se bloquea)
        - response: str (solo si se bloquea — mensaje predefinido)
    """
    query = state.get("query", "")
    query_type = state.get("query_type", "consulta")

    # Saludos no necesitan validación de seguridad
    if query_type == "saludo":
        logger.debug("guardrail_input: saludo, skipping validation")
        return {"guardrail_passed": True}

    validator = _get_validator()
    result = await validator.validate(query)

    if result.is_safe:
        logger.debug("guardrail_input: query SAFE")
        return {"guardrail_passed": True}

    # ── Query bloqueada ──────────────────────────────────────────
    blocked_response = _BLOCKED_RESPONSES.get(result.threat_category, _DEFAULT_BLOCKED_RESPONSE)

    logger.warning(
        "guardrail_input: query BLOCKED — category=%s, rule=%s, layer=%s, query=%.100s",
        result.threat_category,
        result.matched_rule,
        result.detection_layer,
        query,
    )

    return {
        "guardrail_passed": False,
        "query_type": "blocked",
        "response": blocked_response,
    }

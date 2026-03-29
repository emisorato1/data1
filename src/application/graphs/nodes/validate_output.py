"""Nodo guardrail_output: validacion de la respuesta antes de entregarla.

Ejecuta validacion de faithfulness heuristica y deteccion de datos
sensibles (PII argentino) sobre la respuesta generada por el LLM.

Si la validacion falla, reemplaza la respuesta con un mensaje de
fallback seguro y marca ``guardrail_passed=False``.

Logging del resultado a Langfuse via el decorador ``observe()``.

Ubicacion en el flujo: post-generate (invocado desde stream_response).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.infrastructure.observability.langfuse_client import observe
from src.infrastructure.security.guardrails.output_validator import (
    FALLBACK_MESSAGE,
    OutputGuardrailResult,
    OutputValidator,
)

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# ── Module-level validator (lazy init via factory) ───────────────────

_validator: OutputValidator | None = None


def _get_validator() -> OutputValidator:
    """Retorna el OutputValidator singleton del modulo.

    Permite inyeccion en tests via ``set_output_validator()``.
    """
    global _validator
    if _validator is None:
        _validator = OutputValidator()
    return _validator


def set_output_validator(validator: OutputValidator | None) -> None:
    """Inyecta un OutputValidator custom (para tests o configuracion).

    Pasar ``None`` resetea al default (lazy init).
    """
    global _validator
    _validator = validator


# ── Nodo principal ───────────────────────────────────────────────────


@observe(name="guardrail_output")
def validate_output_node(state: RAGState) -> dict:
    """Valida la respuesta generada antes de entregarla al usuario.

    Checks:
    1. Deteccion de datos sensibles (DNI, CUIT/CUIL, CBU).
    2. Faithfulness heuristica (keyword overlap con el contexto).

    Si falla cualquier check, reemplaza ``response`` con el fallback
    message y marca ``guardrail_passed=False``.

    Returns
    -------
    dict
        - guardrail_passed: bool
        - response: str (solo se cambia si se bloquea)
    """
    response = state.get("response", "")
    context = state.get("context_text", "")

    # Sin respuesta: nada que validar
    if not response.strip():
        logger.debug("guardrail_output: empty response, skipping")
        return {"guardrail_passed": True}

    validator = _get_validator()
    result: OutputGuardrailResult = validator.validate(
        response=response,
        context=context,
    )

    if result.is_safe:
        logger.info(
            "guardrail_output: PASSED (faithfulness=%.2f)",
            result.faithfulness_score,
        )
        return {"guardrail_passed": True}

    # ── Respuesta bloqueada ──────────────────────────────────────
    logger.warning(
        "guardrail_output: BLOCKED — reason=%s, detail=%s, response=%.100s",
        result.reason,
        result.detail,
        response,
    )

    return {
        "guardrail_passed": False,
        "response": FALLBACK_MESSAGE,
    }


# ── Funcion standalone para uso fuera del grafo ─────────────────────


@observe(name="guardrail_output_validate")
def validate_output(response: str, context: str) -> tuple[bool, str]:
    """Valida una respuesta fuera del contexto del grafo LangGraph.

    Convenience function para integrar en ``stream_response.py``
    sin necesitar un ``RAGState``.

    Parameters
    ----------
    response:
        Texto generado por el LLM.
    context:
        Texto del contexto RAG (chunks ensamblados).

    Returns
    -------
    tuple[bool, str]
        ``(is_safe, final_response)`` — si es safe, retorna la respuesta
        original; si no, retorna el fallback message.
    """
    if not response.strip():
        return True, response

    validator = _get_validator()
    result = validator.validate(response=response, context=context)

    if result.is_safe:
        logger.info(
            "guardrail_output: PASSED (faithfulness=%.2f)",
            result.faithfulness_score,
        )
        return True, response

    logger.warning(
        "guardrail_output: BLOCKED — reason=%s, detail=%s",
        result.reason,
        result.detail,
    )
    return False, FALLBACK_MESSAGE

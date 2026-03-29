"""Nodo guardrail_pii_output: deteccion y manejo de PII en respuestas.

Escanea la respuesta generada por el LLM buscando PII argentino
(DNI, CUIT/CUIL, CBU, telefono, email) y aplica la accion configurada:
- **redact**: reemplaza PII con tokens surrogate ([DNI], [CUIT], etc.)
- **block**: rechaza la respuesta completa si hay >= N PIIs

Excluye false-positives: normativas, articulos legales, fechas.

Logging de detecciones a Langfuse via ``observe()`` decorator y
score reporting.

Ubicacion en el flujo: post-generation, pre-response.

Spec: T4-S9-01
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.config.settings import settings
from src.infrastructure.observability.langfuse_client import get_langfuse, observe
from src.infrastructure.security.guardrails.pii_detector import (
    PiiAction,
    PiiDetectionResult,
    PiiOutputDetector,
)

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────

FALLBACK_MESSAGE_PII = (
    "No puedo proporcionar esa informacion porque contiene datos personales sensibles. "
    "Consulte con su oficial de cuenta."
)

# ── Module-level detector (lazy init via factory) ─────────────────────

_detector: PiiOutputDetector | None = None


def _get_detector() -> PiiOutputDetector:
    """Return the PiiOutputDetector singleton.

    Allows injection in tests via ``set_pii_detector()``.
    """
    global _detector
    if _detector is None:
        _detector = PiiOutputDetector(
            default_action=PiiAction(settings.pii_output_action),
            block_threshold=settings.pii_output_block_threshold,
        )
    return _detector


def set_pii_detector(detector: PiiOutputDetector | None) -> None:
    """Inject a custom PiiOutputDetector (for tests or configuration).

    Pass ``None`` to reset to default (lazy init).
    """
    global _detector
    _detector = detector


# ── Langfuse reporting ────────────────────────────────────────────────


def _report_pii_detection(result: PiiDetectionResult, trace_id: str | None = None) -> None:
    """Send PII detection event to Langfuse."""
    langfuse = get_langfuse()
    if langfuse is None:
        logger.debug("guardrail_pii_output: Langfuse not available, skipping report")
        return

    try:
        langfuse.score(  # type: ignore[attr-defined]
            name="pii_output_detection",
            value=float(result.pii_count),
            trace_id=trace_id,
            comment=(
                f"PII detected: {', '.join(result.detected_types)} | "
                f"count={result.pii_count} | action={result.action_taken}"
            ),
        )
        logger.debug(
            "guardrail_pii_output: reported PII detection to Langfuse (count=%d, types=%s)",
            result.pii_count,
            result.detected_types,
        )
    except Exception:
        logger.exception("guardrail_pii_output: failed to report PII detection to Langfuse")


# ── Node function ─────────────────────────────────────────────────────


@observe(name="guardrail_pii_output")
def guardrail_pii_output_node(state: RAGState) -> dict:
    """Scan the generated response for PII and apply redact/block action.

    Flow:
    1. Detect PII in the response using regex patterns.
    2. If no PII: pass through unchanged.
    3. If PII found and action=REDACT: replace PII with surrogate tokens.
    4. If PII found and action=BLOCK (or count >= threshold): replace
       response with fallback message.
    5. Log detections to Langfuse.

    Returns
    -------
    dict
        - guardrail_passed: bool (False if blocked)
        - response: str (redacted or fallback if PII found)
        - pii_detected: list[str] (detected PII type labels)
    """
    response = state.get("response", "")

    if not response.strip():
        logger.debug("guardrail_pii_output: empty response, skipping")
        return {"guardrail_passed": True, "pii_detected": []}

    detector = _get_detector()
    result = detector.detect(response)

    if not result.has_pii:
        logger.debug("guardrail_pii_output: no PII detected")
        return {"guardrail_passed": True, "pii_detected": []}

    # Report to Langfuse
    _report_pii_detection(result)

    if result.was_blocked:
        logger.warning(
            "guardrail_pii_output: BLOCKED — pii_count=%d (>= threshold=%d), types=%s",
            result.pii_count,
            detector.block_threshold,
            result.detected_types,
        )
        return {
            "guardrail_passed": False,
            "response": FALLBACK_MESSAGE_PII,
            "pii_detected": list(result.detected_types),
        }

    # Redact mode: replace PII with tokens, response still delivered
    logger.info(
        "guardrail_pii_output: REDACTED — pii_count=%d, types=%s",
        result.pii_count,
        result.detected_types,
    )
    return {
        "guardrail_passed": True,
        "response": result.redacted_text,
        "pii_detected": list(result.detected_types),
    }

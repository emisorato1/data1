"""Nodo validate_faithfulness: LLM-as-judge faithfulness scoring.

Evalua si la respuesta generada esta soportada por el contexto recuperado.
Usa Gemini Flash como judge para scoring semantico (reemplaza la heuristica
de keyword overlap del output_validator).

Flujo:
1. Evalua faithfulness con LLM-as-judge -> score 0.0 a 1.0
2. Si score >= threshold -> pasa, envia score a Langfuse
3. Si score < threshold -> retry con prompt restrictivo (max 1 retry)
4. Si retry tambien falla -> respuesta generica segura

Ubicacion en el grafo: post-generate (no integrado al grafo aun — Wave 2)

Spec: T4-S9-02
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.config.settings import settings
from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.observability.langfuse_client import get_langfuse, observe
from src.infrastructure.security.guardrails.faithfulness_judge import (
    FaithfulnessJudge,
    FaithfulnessResult,
)

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────

FALLBACK_RESPONSE = (
    "No puedo responder con certeza basandome en la documentacion disponible. "
    "Por favor, consulte con su oficial de cuenta."
)

_RESTRICTIVE_REGEN_PROMPT = """\
Eres un asistente bancario que SOLO puede responder con informacion del contexto proporcionado.

REGLAS ESTRICTAS:
- Solo usa informacion que este EXPLICITAMENTE en el contexto.
- NO agregues informacion adicional, suposiciones o inferencias.
- Si el contexto no contiene la informacion suficiente, responde que no puedes confirmar.
- Cita las fuentes cuando sea posible.

CONTEXTO:
{context}

PREGUNTA DEL USUARIO:
{query}

Responde de forma concisa y profesional, solo con lo que el contexto soporta:
"""

MAX_RETRIES = 1

# ── Module-level judge (lazy init via factory) ────────────────────────

_judge: FaithfulnessJudge | None = None
_regen_client: GeminiClient | None = None


def _get_judge() -> FaithfulnessJudge:
    """Return the FaithfulnessJudge singleton.

    Uses Gemini Flash for judge evaluation.
    Allows injection in tests via ``set_faithfulness_judge()``.
    """
    global _judge
    if _judge is None:
        client = GeminiClient(model=GeminiModel.FLASH, temperature=0.0)
        _judge = FaithfulnessJudge(
            llm_client=client,
            threshold=settings.faithfulness_threshold,
        )
    return _judge


def _get_regen_client() -> GeminiClient:
    """Return the GeminiClient singleton for re-generation.

    Uses Gemini Flash with low temperature for restrictive re-generation.
    Allows injection in tests via ``set_regen_client()``.
    """
    global _regen_client
    if _regen_client is None:
        _regen_client = GeminiClient(model=GeminiModel.FLASH, temperature=0.1)
    return _regen_client


def set_faithfulness_judge(judge: FaithfulnessJudge | None) -> None:
    """Inject a custom FaithfulnessJudge (for tests or configuration).

    Pass ``None`` to reset to default (lazy init).
    """
    global _judge
    _judge = judge


def set_regen_client(client: GeminiClient | None) -> None:
    """Inject a custom GeminiClient for re-generation (for tests).

    Pass ``None`` to reset to default (lazy init).
    """
    global _regen_client
    _regen_client = client


# ── Langfuse score reporting ─────────────────────────────────────────


def _report_faithfulness_score(score: float, trace_id: str | None = None) -> None:
    """Send faithfulness score to Langfuse as trace metadata."""
    langfuse = get_langfuse()
    if langfuse is None:
        logger.debug("validate_faithfulness: Langfuse not available, skipping score report")
        return

    try:
        langfuse.score(  # type: ignore[attr-defined]
            name="faithfulness",
            value=score,
            trace_id=trace_id,
            comment=f"LLM-as-judge faithfulness score: {score:.2f}",
        )
        logger.debug("validate_faithfulness: reported faithfulness score=%.2f to Langfuse", score)
    except Exception:
        logger.exception("validate_faithfulness: failed to report score to Langfuse")


# ── Node function ────────────────────────────────────────────────────


@observe(name="rag_validate_faithfulness")
async def validate_faithfulness_node(state: RAGState) -> dict:
    """Validate response faithfulness using LLM-as-judge.

    Flow:
    1. Score the response against the context.
    2. If faithful (score >= threshold): pass through.
    3. If unfaithful (score < threshold) and retry_count < MAX_RETRIES:
       re-generate with restrictive prompt, then re-score.
    4. If retry also fails: return generic fallback response.

    Returns
    -------
    dict
        - faithfulness_score: float (0.0 to 1.0)
        - guardrail_passed: bool
        - response: str (only changed if blocked/re-generated)
        - retry_count: int (incremented if re-generation happens)
    """
    response = state.get("response", "")
    context = state.get("context_text", "")
    retry_count = state.get("retry_count", 0)

    # Skip faithfulness check if no response or no context
    if not response.strip():
        logger.debug("validate_faithfulness: empty response, skipping")
        return {"faithfulness_score": 1.0, "guardrail_passed": True}

    if not context.strip():
        logger.debug("validate_faithfulness: no context, skipping (fail-open)")
        return {"faithfulness_score": 1.0, "guardrail_passed": True}

    judge = _get_judge()

    # ── First evaluation ─────────────────────────────────────────
    result = await judge.evaluate(response=response, context=context)

    _report_faithfulness_score(result.score)

    if result.is_faithful:
        logger.info(
            "validate_faithfulness: PASSED (score=%.2f, threshold=%.2f)",
            result.score,
            judge.threshold,
        )
        return {
            "faithfulness_score": result.score,
            "guardrail_passed": True,
        }

    # ── Score below threshold: attempt re-generation ─────────────
    logger.warning(
        "validate_faithfulness: FAILED (score=%.2f, threshold=%.2f, reason=%s)",
        result.score,
        judge.threshold,
        result.reason,
    )

    if retry_count >= MAX_RETRIES:
        logger.warning(
            "validate_faithfulness: max retries reached (%d), returning fallback",
            retry_count,
        )
        return {
            "faithfulness_score": result.score,
            "guardrail_passed": False,
            "response": FALLBACK_RESPONSE,
        }

    # ── Re-generate with restrictive prompt ──────────────────────
    logger.info("validate_faithfulness: re-generating with restrictive prompt (retry %d)", retry_count + 1)

    regen_result = await _regenerate_and_rescore(
        query=state.get("query", ""),
        context=context,
        judge=judge,
    )

    if regen_result.is_faithful:
        logger.info(
            "validate_faithfulness: retry PASSED (score=%.2f)",
            regen_result.score,
        )
        _report_faithfulness_score(regen_result.score)
        return {
            "faithfulness_score": regen_result.score,
            "guardrail_passed": True,
            "response": regen_result.reason,  # Contains regenerated response
            "retry_count": retry_count + 1,
        }

    # ── Retry also failed: fallback ──────────────────────────────
    logger.warning(
        "validate_faithfulness: retry also FAILED (score=%.2f), returning fallback",
        regen_result.score,
    )
    _report_faithfulness_score(regen_result.score)
    return {
        "faithfulness_score": regen_result.score,
        "guardrail_passed": False,
        "response": FALLBACK_RESPONSE,
        "retry_count": retry_count + 1,
    }


async def _regenerate_and_rescore(
    *,
    query: str,
    context: str,
    judge: FaithfulnessJudge,
) -> FaithfulnessResult:
    """Re-generate a response with restrictive prompt and re-score it.

    Returns a FaithfulnessResult where ``reason`` contains the regenerated
    response text if faithful, or the original reason if not.
    """
    regen_client = _get_regen_client()

    prompt = _RESTRICTIVE_REGEN_PROMPT.format(context=context, query=query)

    try:
        regenerated = await regen_client.generate(prompt)
    except Exception:
        logger.exception("validate_faithfulness: re-generation failed")
        return FaithfulnessResult(
            score=0.0,
            is_faithful=False,
            reason="Error en re-generacion.",
        )

    # Re-score the regenerated response
    rescore_result = await judge.evaluate(response=regenerated, context=context)

    if rescore_result.is_faithful:
        # Return the regenerated text as the "reason" field
        # The node will use this to update the response
        return FaithfulnessResult(
            score=rescore_result.score,
            is_faithful=True,
            reason=regenerated,
            raw_response=rescore_result.raw_response,
        )

    return rescore_result

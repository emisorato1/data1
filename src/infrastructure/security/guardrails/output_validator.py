"""Output validation guardrail for the RAG pipeline.

Validates the generated response before delivering it to the user:
1. **Faithfulness check** (heuristic): verifies the response has lexical
   support in the provided context using keyword overlap — NOT LLM-as-judge.
2. **Sensitive data detection** (regex): detects Argentine PII patterns
   (DNI, CUIT/CUIL, CBU) and account numbers in the response.

If either check fails, a safe fallback message replaces the response.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import StrEnum

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────

FALLBACK_MESSAGE = "No puedo proporcionar esa informacion. Consulte con su oficial de cuenta."

# Minimum keyword overlap ratio for faithfulness (0.0 - 1.0).
# A response must share at least this fraction of its significant
# keywords with the context to be considered faithful.
DEFAULT_FAITHFULNESS_THRESHOLD = 0.3

# Minimum keyword length to consider (filters stop-words / articles).
MIN_KEYWORD_LENGTH = 4

# ── Rejection reasons ────────────────────────────────────────────────


class OutputRejectionReason(StrEnum):
    """Why an output was rejected."""

    NONE = "none"
    UNFAITHFUL = "unfaithful"
    SENSITIVE_DATA = "sensitive_data"


# ── PII patterns (Argentine) ────────────────────────────────────────

# DNI: 2-digit prefix + 3 digits + 3 digits, separated by dots or not.
# Examples: 32.456.789, 32456789
_DNI_PATTERN = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}\b")

# CUIT / CUIL: XX-XXXXXXXX-X (all dashes) or XXXXXXXXXXX (no dashes).
# Examples: 20-12345678-9, 20123456789
_CUIT_PATTERN = re.compile(r"\b(?:\d{2}-\d{8}-\d|\d{11})\b")

# CBU: exactly 22 consecutive digits.
_CBU_PATTERN = re.compile(r"\b\d{22}\b")

_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (_DNI_PATTERN, "DNI"),
    (_CUIT_PATTERN, "CUIT/CUIL"),
    (_CBU_PATTERN, "CBU"),
]

# ── Result dataclass ─────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class OutputGuardrailResult:
    """Result of output validation."""

    is_safe: bool
    reason: OutputRejectionReason = OutputRejectionReason.NONE
    detail: str = ""
    faithfulness_score: float = 1.0
    detected_pii_types: tuple[str, ...] = ()


# ── Validator class ──────────────────────────────────────────────────


@dataclass
class OutputValidator:
    """Validates LLM-generated responses before delivery.

    Parameters
    ----------
    faithfulness_threshold:
        Minimum keyword overlap ratio (0.0 - 1.0) between response and
        context.  Below this → response is considered unfaithful.
    enable_faithfulness:
        Whether to run the faithfulness check.  Default ``True``.
    enable_pii_check:
        Whether to run PII detection.  Default ``True``.
    """

    faithfulness_threshold: float = DEFAULT_FAITHFULNESS_THRESHOLD
    enable_faithfulness: bool = True
    enable_pii_check: bool = True
    _blocked_count: int = field(default=0, init=False, repr=False)

    @property
    def blocked_count(self) -> int:
        """Number of responses blocked since instantiation."""
        return self._blocked_count

    def validate(self, *, response: str, context: str) -> OutputGuardrailResult:
        """Validate a generated response.

        Parameters
        ----------
        response:
            The LLM-generated text to validate.
        context:
            The RAG context (assembled chunks) that the response should
            be faithful to.

        Returns
        -------
        OutputGuardrailResult
        """
        # ── PII check (fast, run first) ──────────────────────────
        if self.enable_pii_check:
            pii_result = self._check_pii(response)
            if not pii_result.is_safe:
                self._blocked_count += 1
                logger.warning(
                    "Output guardrail BLOCKED (PII): types=%s, response=%.100s",
                    pii_result.detected_pii_types,
                    response,
                )
                return pii_result

        # ── Faithfulness check ───────────────────────────────────
        if self.enable_faithfulness:
            faith_result = self._check_faithfulness(response, context)
            if not faith_result.is_safe:
                self._blocked_count += 1
                logger.warning(
                    "Output guardrail BLOCKED (faithfulness): score=%.2f, threshold=%.2f, response=%.100s",
                    faith_result.faithfulness_score,
                    self.faithfulness_threshold,
                    response,
                )
                return faith_result

        return OutputGuardrailResult(is_safe=True)

    # ── Private methods ──────────────────────────────────────────

    @staticmethod
    def _check_pii(response: str) -> OutputGuardrailResult:
        """Detect Argentine PII patterns in the response."""
        detected: list[str] = []
        for pattern, pii_type in _PII_PATTERNS:
            if pattern.search(response):
                detected.append(pii_type)

        if detected:
            return OutputGuardrailResult(
                is_safe=False,
                reason=OutputRejectionReason.SENSITIVE_DATA,
                detail=f"Detected sensitive data: {', '.join(detected)}",
                detected_pii_types=tuple(detected),
            )

        return OutputGuardrailResult(is_safe=True)

    def _check_faithfulness(self, response: str, context: str) -> OutputGuardrailResult:
        """Heuristic faithfulness: keyword overlap between response and context.

        Extracts significant keywords (length >= MIN_KEYWORD_LENGTH) from
        both texts, then computes the fraction of response keywords that
        appear in the context.  If the response has no significant keywords,
        it is considered faithful (edge case: very short responses).
        """
        response_keywords = _extract_keywords(response)
        context_keywords = _extract_keywords(context)

        if not response_keywords:
            # Very short / trivial response — consider faithful.
            return OutputGuardrailResult(is_safe=True, faithfulness_score=1.0)

        if not context_keywords:
            # No context provided — cannot verify faithfulness.
            # Fail-open: let it through (the generate node already handles
            # the no-context fallback).
            return OutputGuardrailResult(is_safe=True, faithfulness_score=1.0)

        overlap = response_keywords & context_keywords
        score = len(overlap) / len(response_keywords)

        if score < self.faithfulness_threshold:
            return OutputGuardrailResult(
                is_safe=False,
                reason=OutputRejectionReason.UNFAITHFUL,
                detail=(
                    f"Low faithfulness score ({score:.2f} < {self.faithfulness_threshold:.2f}). "
                    f"Response keywords not in context: "
                    f"{sorted(response_keywords - context_keywords)[:10]}"
                ),
                faithfulness_score=score,
            )

        return OutputGuardrailResult(is_safe=True, faithfulness_score=score)


# ── Helpers ──────────────────────────────────────────────────────────


def _extract_keywords(text: str) -> set[str]:
    """Extract significant lowercase keywords from text.

    Filters out words shorter than MIN_KEYWORD_LENGTH and pure numbers.
    """
    words = re.findall(r"[a-záéíóúüñ]+", text.lower())
    return {w for w in words if len(w) >= MIN_KEYWORD_LENGTH and not w.isdigit()}

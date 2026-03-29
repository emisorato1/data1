"""Output PII detector for the RAG pipeline.

Scans LLM-generated responses for Argentine banking PII and applies
configurable actions: ``redact`` (replace with surrogate tokens) or
``block`` (reject the entire response).

Supported PII types:
- DNI: national identity document (XX.XXX.XXX)
- CUIT/CUIL: tax/social-security ID (XX-XXXXXXXX-X)
- CBU: bank account identifier (22 digits)
- Phone: Argentine phone numbers (+54... / 0...)
- Email: email addresses

False-positive exclusions:
- Legal references: Ley N 25.326, Art. 14, Decreto 1234/2020
- Dates: 12.03.2024, 01/01/2025
- Normative numbers: Resolucion 123/2024, Circular A 1234

Spec: T4-S9-01
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import ClassVar

# ── Action enum ──────────────────────────────────────────────────────


class PiiAction(StrEnum):
    """Action to take when PII is detected in output."""

    REDACT = "redact"
    BLOCK = "block"


# ── Detection match ──────────────────────────────────────────────────


@dataclass(frozen=True)
class PiiMatch:
    """A single PII detection in text."""

    pii_type: str
    start: int
    end: int
    value: str


# ── Detection result ─────────────────────────────────────────────────


@dataclass(frozen=True)
class PiiDetectionResult:
    """Result of PII output detection."""

    action_taken: PiiAction
    detected_types: tuple[str, ...]
    matches: tuple[PiiMatch, ...]
    redacted_text: str
    original_text: str
    pii_count: int

    @property
    def has_pii(self) -> bool:
        """True when at least one PII was detected."""
        return self.pii_count > 0

    @property
    def was_blocked(self) -> bool:
        """True when the response was blocked (not just redacted)."""
        return self.action_taken == PiiAction.BLOCK and self.has_pii


# ── False-positive exclusion patterns ────────────────────────────────

# Dates with dots: 12.03.2024, 01.01.2025
_DATE_DOT_PATTERN = re.compile(r"\b\d{1,2}\.\d{2}\.\d{4}\b")

# Dates with slashes: 12/03/2024
_DATE_SLASH_PATTERN = re.compile(r"\b\d{1,2}/\d{2}/\d{4}\b")

# Legal references: Ley 25.326, Ley N 25326, Ley No. 25.326
_LEY_PATTERN = re.compile(r"(?i)\bley\s+(?:n[°o.]?\s*)?[\d.]+\b")

# Articles: Art. 14, Articulo 123
_ART_PATTERN = re.compile(r"(?i)\b(?:art(?:[ií]culo)?\.?\s*)\d+\b")

# Decrees: Decreto 1234/2020
_DECRETO_PATTERN = re.compile(r"(?i)\bdecreto\s+\d+(?:/\d+)?\b")

# Resolutions: Resolucion 123/2024, Circular A 1234
_RESOLUCION_PATTERN = re.compile(r"(?i)\b(?:resoluci[oó]n|circular)\s+[A-Za-z]?\s*\d+(?:/\d+)?\b")

# Normative number after keyword (e.g. "norma 12.345.678")
_NORMA_PATTERN = re.compile(r"(?i)\b(?:norma|normativa|comunicaci[oó]n|disposici[oó]n)\s+[A-Za-z]?\s*[\d.]+\b")

_FALSE_POSITIVE_PATTERNS: list[re.Pattern[str]] = [
    _DATE_DOT_PATTERN,
    _DATE_SLASH_PATTERN,
    _LEY_PATTERN,
    _ART_PATTERN,
    _DECRETO_PATTERN,
    _RESOLUCION_PATTERN,
    _NORMA_PATTERN,
]

# ── PII patterns (Argentine banking) ────────────────────────────────

_SURROGATE_MAP: dict[str, str] = {
    "CBU": "[CBU]",
    "CUIT/CUIL": "[CUIT]",
    "DNI": "[DNI]",
    "EMAIL": "[EMAIL]",
    "PHONE": "[TELEFONO]",
}

# Order matters: most-specific first (CBU 22 digits before CUIT 11 digits).
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # CBU: exactly 22 consecutive digits
    (re.compile(r"\b\d{22}\b"), "CBU"),
    # CUIT/CUIL: XX-XXXXXXXX-X or 11 consecutive digits
    (re.compile(r"\b(?:\d{2}-\d{8}-\d|\d{11})\b"), "CUIT/CUIL"),
    # DNI: 2-digit prefix + 3 digits + 3 digits (dots optional)
    (re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}\b"), "DNI"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "EMAIL"),
    # Argentine phone numbers: +54 or 0 prefix
    (re.compile(r"(?<!\w)(?:\+54|0)\s*(?:\d[\s\-]*){6,12}\d(?!\d)"), "PHONE"),
]


# ── PiiOutputDetector ────────────────────────────────────────────────


@dataclass
class PiiOutputDetector:
    """Detects and handles PII in LLM-generated responses.

    Parameters
    ----------
    default_action:
        Action when PII count is below ``block_threshold``.
        Default: ``PiiAction.REDACT``.
    block_threshold:
        Number of PII detections that triggers an automatic block
        regardless of ``default_action``.  Default: ``3``.
    enable_ner:
        Reserved for future NER integration (spaCy or similar).
        Currently has no effect.  Default: ``False``.
    """

    default_action: PiiAction = PiiAction.REDACT
    block_threshold: int = 3
    enable_ner: bool = False
    _detection_count: int = field(default=0, init=False, repr=False)

    # Class-level patterns
    _PII_PATTERNS: ClassVar[list[tuple[re.Pattern[str], str]]] = _PII_PATTERNS
    _FALSE_POSITIVE_PATTERNS: ClassVar[list[re.Pattern[str]]] = _FALSE_POSITIVE_PATTERNS
    _SURROGATE_MAP: ClassVar[dict[str, str]] = _SURROGATE_MAP

    @property
    def detection_count(self) -> int:
        """Total number of responses where PII was detected."""
        return self._detection_count

    def detect(self, text: str) -> PiiDetectionResult:
        """Scan text for PII and apply the configured action.

        Parameters
        ----------
        text:
            The LLM-generated response to scan.

        Returns
        -------
        PiiDetectionResult
            Contains detection details, action taken, and redacted text.
        """
        if not text.strip():
            return PiiDetectionResult(
                action_taken=self.default_action,
                detected_types=(),
                matches=(),
                redacted_text=text,
                original_text=text,
                pii_count=0,
            )

        # Collect false-positive spans to exclude
        fp_spans = self._collect_false_positive_spans(text)

        # Find all PII matches, excluding false positives
        matches = self._find_matches(text, fp_spans)

        if not matches:
            return PiiDetectionResult(
                action_taken=self.default_action,
                detected_types=(),
                matches=(),
                redacted_text=text,
                original_text=text,
                pii_count=0,
            )

        self._detection_count += 1

        pii_count = len(matches)
        detected_types = tuple(dict.fromkeys(m.pii_type for m in matches))

        # Determine action: block if threshold exceeded
        action = PiiAction.BLOCK if pii_count >= self.block_threshold else self.default_action

        # Build redacted text (only if action is REDACT)
        redacted_text = self._redact(text, matches) if action == PiiAction.REDACT else text

        return PiiDetectionResult(
            action_taken=action,
            detected_types=detected_types,
            matches=tuple(matches),
            redacted_text=redacted_text,
            original_text=text,
            pii_count=pii_count,
        )

    # ── Private helpers ──────────────────────────────────────────

    @staticmethod
    def _collect_false_positive_spans(text: str) -> set[tuple[int, int]]:
        """Collect character spans that match false-positive patterns."""
        spans: set[tuple[int, int]] = set()
        for fp_pattern in _FALSE_POSITIVE_PATTERNS:
            for match in fp_pattern.finditer(text):
                spans.add((match.start(), match.end()))
        return spans

    @staticmethod
    def _is_in_false_positive(start: int, end: int, fp_spans: set[tuple[int, int]]) -> bool:
        """Check if a match span overlaps with any false-positive span."""
        for fp_start, fp_end in fp_spans:
            if start >= fp_start and end <= fp_end:
                return True
            if start < fp_end and end > fp_start:
                return True
        return False

    def _find_matches(self, text: str, fp_spans: set[tuple[int, int]]) -> list[PiiMatch]:
        """Find all PII matches excluding false positives."""
        matches: list[PiiMatch] = []
        matched_spans: set[tuple[int, int]] = set()

        for pattern, pii_type in self._PII_PATTERNS:
            for m in pattern.finditer(text):
                span = (m.start(), m.end())

                # Skip if this span overlaps with an already-matched span
                if any(span[0] < ms_end and span[1] > ms_start for ms_start, ms_end in matched_spans):
                    continue

                # Skip if this is a false positive
                if self._is_in_false_positive(m.start(), m.end(), fp_spans):
                    continue

                matches.append(
                    PiiMatch(
                        pii_type=pii_type,
                        start=m.start(),
                        end=m.end(),
                        value=m.group(),
                    )
                )
                matched_spans.add(span)

        # Sort by position for consistent redaction
        matches.sort(key=lambda x: x.start)
        return matches

    def _redact(self, text: str, matches: list[PiiMatch]) -> str:
        """Replace PII matches with surrogate tokens."""
        # Process in reverse order to preserve indices
        result = text
        for match in reversed(matches):
            surrogate = self._SURROGATE_MAP.get(match.pii_type, "[REDACTED]")
            result = result[: match.start] + surrogate + result[match.end :]
        return result

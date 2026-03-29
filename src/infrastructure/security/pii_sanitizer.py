"""PII sanitizer: regex-based local fallback for Argentine PII patterns.

This module provides a standalone, reusable sanitizer that replaces
personally identifiable information (PII) with semantic surrogate tokens.
It serves as the fallback layer when Cloud DLP is unavailable or disabled.

Supported PII types (Argentine context):
- DNI: national identity document number
- CUIT/CUIL: tax/social-security identification number
- CBU: bank account identifier (22 digits)
- EMAIL: email addresses
- PHONE: Argentine phone numbers (+54 or 0 prefix)

The surrogate tokens are semantic (e.g. [NOMBRE], [DNI]) so that memory
content retains its contextual utility after sanitization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

# ── Surrogate token constants ─────────────────────────────────────────

TOKEN_DNI = "[DNI]"  # noqa: S105
TOKEN_CUIT = "[CUIT]"  # noqa: S105
TOKEN_CBU = "[CBU]"  # noqa: S105
TOKEN_EMAIL = "[EMAIL]"  # noqa: S105
TOKEN_PHONE = "[TELEFONO]"  # noqa: S105
TOKEN_NAME = "[NOMBRE]"  # noqa: S105

# ── Pattern definitions ───────────────────────────────────────────────


@dataclass(frozen=True)
class PiiPattern:
    """Associates a compiled regex pattern with a PII type label and its surrogate token."""

    pattern: re.Pattern[str]
    pii_type: str
    surrogate: str


# Default patterns ordered from most-specific to least-specific to
# avoid partial matches shadowing longer ones (e.g. CBU before CUIT).
_DEFAULT_PATTERNS: list[PiiPattern] = [
    # CBU: exactly 22 consecutive digits — must come before CUIT (11 digits)
    PiiPattern(
        pattern=re.compile(r"\b\d{22}\b"),
        pii_type="CBU",
        surrogate=TOKEN_CBU,
    ),
    # CUIT/CUIL: XX-XXXXXXXX-X or 11 consecutive digits
    PiiPattern(
        pattern=re.compile(r"\b(?:\d{2}-\d{8}-\d|\d{11})\b"),
        pii_type="CUIT/CUIL",
        surrogate=TOKEN_CUIT,
    ),
    # DNI: 2-digit prefix + 3 digits + 3 digits (dots optional)
    # Examples: 32.456.789, 32456789
    PiiPattern(
        pattern=re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}\b"),
        pii_type="DNI",
        surrogate=TOKEN_DNI,
    ),
    # Email addresses
    PiiPattern(
        pattern=re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        pii_type="EMAIL",
        surrogate=TOKEN_EMAIL,
    ),
    # Argentine phone numbers: +54 or 0 prefix followed by 7-13 digits
    # (allows spaces and dashes between digit groups).
    # Uses lookbehind instead of \b because \b fails before '+'.
    PiiPattern(
        pattern=re.compile(r"(?<!\w)(?:\+54|0)\s*(?:\d[\s\-]*){6,12}\d(?!\d)"),
        pii_type="PHONE",
        surrogate=TOKEN_PHONE,
    ),
]


# ── SanitizationResult ────────────────────────────────────────────────


@dataclass(frozen=True)
class SanitizationResult:
    """Result of a sanitization pass."""

    sanitized_text: str
    detected_types: tuple[str, ...]
    was_modified: bool

    @property
    def is_clean(self) -> bool:
        """True when no PII was detected."""
        return not self.was_modified


# ── PiiSanitizer ─────────────────────────────────────────────────────


class PiiSanitizer:
    """Regex-based PII sanitizer for Argentine PII patterns.

    Replaces detected PII with semantic surrogate tokens so that memory
    content retains contextual meaning after sanitization.

    Parameters
    ----------
    extra_patterns:
        Additional :class:`PiiPattern` instances to include on top of
        the built-in defaults.  Useful for project-specific extensions
        (e.g. internal account formats).

    Examples
    --------
    >>> sanitizer = PiiSanitizer()
    >>> result = sanitizer.sanitize("DNI: 32.456.789, email: foo@bar.com")
    >>> result.sanitized_text
    'DNI: [DNI], email: [EMAIL]'
    >>> result.detected_types
    ('DNI', 'EMAIL')
    """

    # Class-level default patterns — shared across instances (immutable)
    _DEFAULT_PATTERNS: ClassVar[list[PiiPattern]] = _DEFAULT_PATTERNS

    def __init__(self, extra_patterns: list[PiiPattern] | None = None) -> None:
        self._patterns: list[PiiPattern] = list(self._DEFAULT_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)

    # ── Public API ────────────────────────────────────────────────

    def sanitize(self, text: str) -> SanitizationResult:
        """Sanitize ``text`` by replacing all detected PII with surrogates.

        Parameters
        ----------
        text:
            Raw text that may contain PII.

        Returns
        -------
        SanitizationResult
            Contains the sanitized text, detected PII types, and a flag
            indicating whether any substitution was made.
        """
        result = text
        detected: list[str] = []

        for pii_pattern in self._patterns:
            if pii_pattern.pattern.search(result):
                detected.append(pii_pattern.pii_type)
                result = pii_pattern.pattern.sub(pii_pattern.surrogate, result)

        return SanitizationResult(
            sanitized_text=result,
            detected_types=tuple(detected),
            was_modified=result != text,
        )

    def detect(self, text: str) -> tuple[str, ...]:
        """Return the PII types detected in ``text`` without modifying it.

        Parameters
        ----------
        text:
            Text to inspect for PII.

        Returns
        -------
        tuple[str, ...]
            Detected PII type labels (e.g. ``("DNI", "EMAIL")``).
        """
        detected: list[str] = []
        for pii_pattern in self._patterns:
            if pii_pattern.pattern.search(text):
                detected.append(pii_pattern.pii_type)
        return tuple(detected)

    @property
    def supported_types(self) -> list[str]:
        """List of PII type labels this sanitizer handles."""
        return [p.pii_type for p in self._patterns]

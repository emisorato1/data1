"""Cloud DLP client with automatic regex fallback.

Wraps the Google Cloud Data Loss Prevention API to sanitize text using
enterprise-grade PII detection for Argentine data types.  When Cloud DLP
is unavailable (disabled via settings, missing credentials, or API error),
the client transparently falls back to the local :class:`PiiSanitizer`
regex engine so that PII sanitization is always applied.

Architecture
------------
- **Primary path**: Cloud DLP ``content.deidentify`` with configured
  InfoTypes (PERSON_NAME, PHONE_NUMBER, EMAIL_ADDRESS) plus custom
  Argentine InfoTypes (ARGENTINA_DNI, ARGENTINA_CUIT_CUIL, ARGENTINA_CBU).
- **Fallback path**: :class:`~.pii_sanitizer.PiiSanitizer` regex engine,
  always applied when ``dlp_enabled=False`` or when the DLP call fails.

Usage
-----
    client = DlpClient(project_id="my-gcp-project")
    result = await client.sanitize("Mi DNI es 32.456.789")
    print(result.sanitized_text)  # "Mi DNI es [DNI]"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.infrastructure.security.pii_sanitizer import PiiSanitizer, SanitizationResult

logger = logging.getLogger(__name__)

# ── DLP InfoType configuration ────────────────────────────────────────

# Standard Google Cloud DLP InfoTypes to include.
_STANDARD_INFO_TYPES: list[str] = [
    "PERSON_NAME",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
]

# Custom Argentine InfoTypes defined via regex.
# Each entry: (info_type_name, display_name, regex, surrogate_token)
_CUSTOM_INFO_TYPES: list[tuple[str, str, str, str]] = [
    (
        "ARGENTINA_DNI",
        "Argentine DNI",
        r"\b\d{2}\.?\d{3}\.?\d{3}\b",
        "[DNI]",
    ),
    (
        "ARGENTINA_CUIT_CUIL",
        "Argentine CUIT/CUIL",
        r"\b(?:\d{2}-\d{8}-\d|\d{11})\b",
        "[CUIT]",
    ),
    (
        "ARGENTINA_CBU",
        "Argentine CBU",
        r"\b\d{22}\b",
        "[CBU]",
    ),
]

# Surrogate token for standard InfoTypes (Cloud DLP replaces with these)
_STANDARD_SURROGATES: dict[str, str] = {
    "PERSON_NAME": "[NOMBRE]",
    "PHONE_NUMBER": "[TELEFONO]",
    "EMAIL_ADDRESS": "[EMAIL]",
}


# ── DlpClient ─────────────────────────────────────────────────────────


@dataclass
class DlpClient:
    """Enterprise PII sanitizer backed by Cloud DLP with local regex fallback.

    Parameters
    ----------
    project_id:
        GCP project ID used for the DLP API calls.  Required when
        ``dlp_enabled=True``.
    dlp_enabled:
        Whether to attempt Cloud DLP calls.  When ``False`` (or when the
        DLP call fails), the local :class:`PiiSanitizer` is used.
    min_likelihood:
        Minimum DLP finding likelihood to act on.
        One of: VERY_UNLIKELY, UNLIKELY, POSSIBLE, LIKELY, VERY_LIKELY.
    extra_info_types:
        Additional InfoType names to pass to Cloud DLP on top of the
        built-in defaults.

    Notes
    -----
    Cloud DLP is called synchronously via the REST API inside an async
    wrapper so it can be awaited from async callers without blocking the
    event loop.
    """

    project_id: str = ""
    dlp_enabled: bool = False
    min_likelihood: str = "POSSIBLE"
    extra_info_types: list[str] | None = None

    def __post_init__(self) -> None:
        self._local_sanitizer = PiiSanitizer()
        self._dlp_client: Any | None = None  # lazy-init on first use

    # ── Public API ────────────────────────────────────────────────

    async def sanitize(self, text: str) -> SanitizationResult:
        """Sanitize ``text``, removing or replacing all detected PII.

        Attempts Cloud DLP when enabled and configured; falls back to the
        local regex sanitizer on any error or when DLP is disabled.

        Parameters
        ----------
        text:
            Raw text to sanitize.

        Returns
        -------
        SanitizationResult
            Sanitized text, detected PII type labels, and a modification flag.
        """
        if not text:
            return SanitizationResult(
                sanitized_text=text,
                detected_types=(),
                was_modified=False,
            )

        if self.dlp_enabled and self.project_id:
            try:
                return await self._sanitize_with_dlp(text)
            except Exception as exc:
                logger.warning(
                    "Cloud DLP sanitization failed — falling back to regex. error=%s",
                    exc,
                )

        # Fallback: local regex sanitizer
        return self._local_sanitizer.sanitize(text)

    def sanitize_sync(self, text: str) -> SanitizationResult:
        """Synchronous sanitization using the local regex engine only.

        Useful in contexts where ``await`` is not available (e.g. sync
        background tasks).  Cloud DLP is never called from this method.

        Parameters
        ----------
        text:
            Raw text to sanitize.

        Returns
        -------
        SanitizationResult
        """
        return self._local_sanitizer.sanitize(text)

    # ── Private helpers ────────────────────────────────────────────

    async def _sanitize_with_dlp(self, text: str) -> SanitizationResult:
        """Call Cloud DLP ``content.deidentify`` and map results to SanitizationResult.

        Raises
        ------
        Exception
            Any error from the DLP API — callers should catch and fallback.
        """
        try:
            import google.cloud.dlp_v2 as dlp_v2  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "google-cloud-dlp is not installed. Install it with: pip install google-cloud-dlp"
            ) from exc

        import asyncio

        client = self._get_dlp_client(dlp_v2)
        parent = f"projects/{self.project_id}"

        # Build deidentify config with surrogate tokens
        info_type_transformations = self._build_info_type_transformations(dlp_v2)

        deidentify_config = dlp_v2.DeidentifyConfig(
            info_type_transformations=dlp_v2.InfoTypeTransformations(transformations=info_type_transformations)
        )

        inspect_config = dlp_v2.InspectConfig(
            info_types=self._build_info_types(dlp_v2),
            custom_info_types=self._build_custom_info_types(dlp_v2),
            min_likelihood=self.min_likelihood,
        )

        item = dlp_v2.ContentItem(value=text)

        request = dlp_v2.DeidentifyContentRequest(
            parent=parent,
            deidentify_config=deidentify_config,
            inspect_config=inspect_config,
            item=item,
        )

        # Run the blocking DLP call in a thread pool to avoid blocking the loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.deidentify_content(request=request),
        )

        sanitized_text = response.item.value
        detected = self._extract_detected_types(text, sanitized_text)

        return SanitizationResult(
            sanitized_text=sanitized_text,
            detected_types=tuple(detected),
            was_modified=sanitized_text != text,
        )

    def _get_dlp_client(self, dlp_v2: Any) -> Any:
        """Return or create the DLP client (lazy singleton)."""
        if self._dlp_client is None:
            self._dlp_client = dlp_v2.DlpServiceClient()
        return self._dlp_client

    def _build_info_types(self, dlp_v2: Any) -> list[Any]:
        """Build the list of standard InfoType objects."""
        names = list(_STANDARD_INFO_TYPES)
        if self.extra_info_types:
            names.extend(self.extra_info_types)
        # Add custom info type names too so they appear in inspect config
        names.extend(name for name, _, _, _ in _CUSTOM_INFO_TYPES)
        return [dlp_v2.InfoType(name=name) for name in names]

    def _build_custom_info_types(self, dlp_v2: Any) -> list[Any]:
        """Build custom InfoType definitions for Argentine PII."""
        custom: list[Any] = []
        for type_name, _display_name, regex, _surrogate in _CUSTOM_INFO_TYPES:
            custom.append(
                dlp_v2.CustomInfoType(
                    info_type=dlp_v2.InfoType(name=type_name),
                    regex=dlp_v2.CustomInfoType.Regex(pattern=regex),
                    likelihood=self.min_likelihood,
                )
            )
        return custom

    def _build_info_type_transformations(self, dlp_v2: Any) -> list[Any]:
        """Build replace-with-info-type transformations for each InfoType."""
        transformations: list[Any] = []

        # Standard InfoTypes — replace with surrogate token
        for type_name in _STANDARD_INFO_TYPES:
            surrogate = _STANDARD_SURROGATES.get(type_name, f"[{type_name}]")
            transformations.append(
                dlp_v2.InfoTypeTransformation(  # type: ignore[attr-defined]
                    info_types=[dlp_v2.InfoType(name=type_name)],  # type: ignore[attr-defined]
                    primitive_transformation=dlp_v2.PrimitiveTransformation(  # type: ignore[attr-defined]
                        replace_config=dlp_v2.ReplaceValueConfig(  # type: ignore[attr-defined]
                            new_value=dlp_v2.Value(string_value=surrogate)  # type: ignore[attr-defined]
                        )
                    ),
                )
            )

        # Custom Argentine InfoTypes
        for type_name, _display_name, _regex, surrogate in _CUSTOM_INFO_TYPES:
            transformations.append(
                dlp_v2.InfoTypeTransformation(  # type: ignore[attr-defined]
                    info_types=[dlp_v2.InfoType(name=type_name)],  # type: ignore[attr-defined]
                    primitive_transformation=dlp_v2.PrimitiveTransformation(  # type: ignore[attr-defined]
                        replace_config=dlp_v2.ReplaceValueConfig(  # type: ignore[attr-defined]
                            new_value=dlp_v2.Value(string_value=surrogate)  # type: ignore[attr-defined]
                        )
                    ),
                )
            )

        return transformations

    @staticmethod
    def _extract_detected_types(original: str, sanitized: str) -> list[str]:
        """Infer detected PII types by comparing original vs sanitized text.

        Since Cloud DLP doesn't directly return the info type labels in the
        deidentify response (only in inspect), we detect which surrogates
        appeared in the sanitized output.
        """
        detected: list[str] = []
        all_surrogates: dict[str, str] = {
            **{v: k for k, v in _STANDARD_SURROGATES.items()},
            **{surrogate: name for name, _, _, surrogate in _CUSTOM_INFO_TYPES},
        }
        for surrogate, type_name in all_surrogates.items():
            if surrogate in sanitized and surrogate not in original:
                detected.append(type_name)
        return detected

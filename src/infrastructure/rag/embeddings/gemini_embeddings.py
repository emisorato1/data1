"""Gemini embedding service using the ``google-genai`` SDK (async native).

Supports dual task types (``RETRIEVAL_DOCUMENT`` for indexing,
``RETRIEVAL_QUERY`` for search) and automatic L2 normalization for
Matryoshka-truncated 768-d vectors.

Batch embedding respects the safe limit of 100 texts per request to avoid
the ordering bug documented in batch-embedding-caveats.md.

See: rag-indexing/references/gemini-embeddings.md
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import settings
from src.infrastructure.rag.embeddings.normalization import (
    normalize_l2,
    normalize_l2_batch,
)
from src.shared.exceptions import ExternalServiceError

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# Safe batch limit — see rag-indexing/references/batch-embedding-caveats.md
_MAX_BATCH_SIZE = 100

# Gemini native dimensionality (text-embedding-004 / gemini-embedding-001)
_NATIVE_DIMENSIONS = 3072


class GeminiEmbeddingService:
    """Async Gemini embedding service with L2 normalization and retry.

    Parameters
    ----------
    api_key:
        Google API key.  Defaults to ``settings.gemini_api_key``.
    model:
        Embedding model name.  Defaults to ``settings.gemini_embedding_model``.
    dimensions:
        Output dimensionality (Matryoshka truncation).  Default ``768``.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int = 768,
    ) -> None:
        if settings.use_vertex_ai:
            import google.auth

            effective_quota = settings.gcp_quota_project_id or settings.gcp_project_id
            credentials, _ = google.auth.default(quota_project_id=effective_quota)
            self._client = genai.Client(
                vertexai=True,
                project=settings.gcp_project_id,
                location=settings.gcp_location,
                credentials=credentials,
            )
        else:
            resolved_key = api_key or settings.gemini_api_key.get_secret_value()
            self._client = genai.Client(api_key=resolved_key)
        self._model = model or settings.gemini_embedding_model
        self._dimensions = dimensions
        self._needs_normalization = dimensions < _NATIVE_DIMENSIONS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed_text(
        self,
        text: str,
        *,
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[float]:
        """Embed a single text and return the normalized vector."""
        embedding = await self._embed_single(text, task_type)
        if self._needs_normalization:
            embedding = normalize_l2(embedding)
        return embedding  # type: ignore[no-any-return]

    async def embed_query(self, text: str) -> list[float]:
        """Embed a search query (uses ``RETRIEVAL_QUERY`` task type)."""
        return await self.embed_text(text, task_type="RETRIEVAL_QUERY")

    async def embed_documents(
        self,
        texts: list[str],
        *,
        on_progress: Callable[[int, int, int], None] | None = None,
    ) -> list[list[float]]:
        """Embed a list of document texts in safe batches of 100.

        Parameters
        ----------
        texts:
            Texts to embed (any length — split internally).
        on_progress:
            Optional callback ``(batch_num, total_batches, total_embedded)``.

        Returns
        -------
        list[list[float]]
            Normalized embeddings in the same order as *texts*.
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        total_batches = (len(texts) + _MAX_BATCH_SIZE - 1) // _MAX_BATCH_SIZE

        for batch_num, start in enumerate(range(0, len(texts), _MAX_BATCH_SIZE)):
            batch = texts[start : start + _MAX_BATCH_SIZE]
            batch_embeddings = await self._embed_batch_with_retry(batch)

            # Validate response count — catch silent ordering bug
            if len(batch_embeddings) != len(batch):
                raise ExternalServiceError(
                    message="Embedding batch count mismatch.",
                    details={
                        "expected": len(batch),
                        "received": len(batch_embeddings),
                        "batch_start": start,
                    },
                )

            all_embeddings.extend(batch_embeddings)

            if on_progress:
                on_progress(batch_num + 1, total_batches, len(all_embeddings))

            logger.info(
                "batch_embedded batch=%d/%d chunks=%d total=%d",
                batch_num + 1,
                total_batches,
                len(batch),
                len(all_embeddings),
            )

        # Normalize the full batch at once (numpy vectorized)
        if self._needs_normalization:
            all_embeddings = normalize_l2_batch(all_embeddings)

        return all_embeddings

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _embed_single(self, text: str, task_type: str) -> list[float]:
        """Call the API for a single text with retry."""
        try:
            response = await self._client.aio.models.embed_content(
                model=self._model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self._dimensions,
                ),
            )
            if not response.embeddings or not response.embeddings[0].values:
                raise ExternalServiceError(
                    message="Gemini returned empty embedding.",
                )
            return response.embeddings[0].values  # type: ignore[no-any-return]
        except ExternalServiceError:
            raise
        except Exception as exc:
            logger.error("embed_single_error error=%s", exc)
            raise ExternalServiceError(
                message=f"Gemini embedding failed: {exc}",
                details={"model": self._model, "task_type": task_type},
            ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _embed_batch_with_retry(
        self,
        batch: list[str],
    ) -> list[list[float]]:
        """Call the API for a batch with retry."""
        try:
            response = await self._client.aio.models.embed_content(
                model=self._model,
                contents=batch,  # type: ignore[arg-type]
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=self._dimensions,
                ),
            )
            if not response.embeddings:
                raise ExternalServiceError(
                    message="Gemini returned no embeddings for batch.",
                )
            return [emb.values for emb in response.embeddings if emb.values]
        except ExternalServiceError:
            raise
        except Exception as exc:
            logger.error("embed_batch_error error=%s", exc)
            raise ExternalServiceError(
                message=f"Gemini batch embedding failed: {exc}",
                details={"model": self._model, "batch_size": len(batch)},
            ) from exc

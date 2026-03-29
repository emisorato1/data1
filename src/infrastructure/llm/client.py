"""Unified Gemini client wrapper for generation and embeddings.

All LLM interactions MUST go through this wrapper. Direct instantiation
of Gemini/Vertex AI clients elsewhere is prohibited (ADR-008).

Supports:
- Gemini 2.0 Flash (complex queries)
- Gemini 2.0 Flash Lite (simple queries, guardrails)
- Streaming and synchronous generation
- Text embeddings with configurable task_type
- Retry with exponential backoff for transient errors (429, 500, 503)
"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import google.auth
from google.api_core.exceptions import (
    InternalServerError,
    ResourceExhausted,
    ServiceUnavailable,
)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import settings
from src.infrastructure.observability.langfuse_client import observe
from src.shared.exceptions import ExternalServiceError, RateLimitError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

# ── Transient exceptions that trigger retry ──────────────────────────
_RETRYABLE_EXCEPTIONS = (
    ResourceExhausted,  # 429
    InternalServerError,  # 500
    ServiceUnavailable,  # 503
)

_MAX_RETRIES = 3
_WAIT_MIN_SECONDS = 1
_WAIT_MAX_SECONDS = 16


class GeminiModel(StrEnum):
    """Available Gemini model variants."""

    FLASH = "flash"
    FLASH_LITE = "flash_lite"


def _model_name(model: GeminiModel) -> str:
    """Resolve a GeminiModel enum to the actual model identifier."""
    mapping = {
        GeminiModel.FLASH: settings.gemini_model_flash,
        GeminiModel.FLASH_LITE: settings.gemini_model_flash_lite,
    }
    return mapping[model]


class GeminiClient:
    """Wrapper around Google Generative AI for generation and embeddings.

    Parameters
    ----------
    model:
        Which model variant to use. Defaults to ``GeminiModel.FLASH``.
    temperature:
        Sampling temperature. ``None`` falls back to ``settings.gemini_temperature``.
    max_tokens:
        Maximum output tokens. ``None`` falls back to ``settings.gemini_max_tokens``.
    safety_settings:
        Optional Vertex AI safety settings dict.
    """

    def __init__(
        self,
        *,
        model: GeminiModel = GeminiModel.FLASH,
        temperature: float | None = None,
        max_tokens: int | None = None,
        safety_settings: dict[str, Any] | None = None,
    ) -> None:
        self._model_enum = model
        self._model_name = _model_name(model)
        self._temperature = temperature if temperature is not None else settings.gemini_temperature
        self._max_tokens = max_tokens if max_tokens is not None else settings.gemini_max_tokens
        self._safety_settings = safety_settings

        self._llm = self._build_chat_model()
        self._embeddings_cache: dict[str, GoogleGenerativeAIEmbeddings] = {}

    def _build_chat_model(self) -> ChatGoogleGenerativeAI:
        kwargs: dict[str, Any] = {
            "model": self._model_name,
            "temperature": self._temperature,
            "max_output_tokens": self._max_tokens,
            "streaming": True,  # Necesario para token-by-token streaming via astream_events
        }

        if settings.use_vertex_ai:
            kwargs["vertexai"] = True
            kwargs["project"] = settings.gcp_project_id
            kwargs["location"] = settings.gcp_location
            effective_quota = settings.gcp_quota_project_id or settings.gcp_project_id
            credentials, _ = google.auth.default(quota_project_id=effective_quota)
            kwargs["credentials"] = credentials
        else:
            kwargs["google_api_key"] = settings.gemini_api_key.get_secret_value()
        if self._safety_settings:
            kwargs["safety_settings"] = self._safety_settings
        return ChatGoogleGenerativeAI(**kwargs)

    def get_langchain_chat_model(self) -> ChatGoogleGenerativeAI:
        """Expose the underlying LangChain chat model for integrations like RAGAS."""
        return self._llm

    def get_langchain_embeddings(self, task_type: str = "RETRIEVAL_QUERY") -> GoogleGenerativeAIEmbeddings:
        """Expose the underlying LangChain embeddings model for integrations like RAGAS."""
        return self._get_embeddings_model(task_type)

    # ── Synchronous generation ───────────────────────────────────────

    @observe(name="llm_generate", as_type="generation")
    async def generate(self, prompt: str, config: dict | None = None, **kwargs: Any) -> str:
        """Generate a complete response for the given prompt.

        Parameters
        ----------
        prompt:
            The full prompt (system + user) to send.
        config:
            Optional LangGraph RunnableConfig for callback propagation.
        **kwargs:
            Additional keyword arguments forwarded to the model invocation.

        Returns
        -------
        str
            The generated text response.

        Raises
        ------
        RateLimitError
            If the API returns 429 after all retries.
        ExternalServiceError
            If the API returns 500/503 after all retries.
        """
        try:
            return await self._generate_with_retry(prompt, config=config, **kwargs)  # type: ignore[no-any-return]
        except ResourceExhausted as exc:
            raise RateLimitError(
                message="Gemini rate limit exceeded after retries.",
                details={"model": self._model_name},
            ) from exc
        except (InternalServerError, ServiceUnavailable) as exc:
            raise ExternalServiceError(
                message=f"Gemini generation failed after retries: {exc}",
                details={"model": self._model_name},
            ) from exc

    @retry(
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(_MAX_RETRIES),
        wait=wait_exponential(min=_WAIT_MIN_SECONDS, max=_WAIT_MAX_SECONDS),
        reraise=True,
    )
    async def _generate_with_retry(self, prompt: str, config: dict | None = None, **kwargs: Any) -> str:
        try:
            # Pasar config para que LangGraph propague callbacks de streaming
            invoke_kwargs = {**kwargs}
            if config:
                invoke_kwargs["config"] = config
            response = await self._llm.ainvoke(prompt, **invoke_kwargs)
            return str(response.content)
        except ResourceExhausted as exc:
            logger.warning("Gemini rate limited (429): %s", exc)
            raise
        except (InternalServerError, ServiceUnavailable) as exc:
            logger.warning("Gemini transient error: %s", exc)
            raise
        except Exception as exc:
            logger.exception("Gemini generation failed: %s", exc)
            raise ExternalServiceError(
                message=f"Gemini generation failed: {exc}",
                details={"model": self._model_name},
            ) from exc

    # ── Structured generation ────────────────────────────────────────

    @observe(name="llm_generate_structured", as_type="generation")
    async def generate_structured(self, prompt: str, schema: Any, config: dict | None = None, **kwargs: Any) -> Any:
        """Generate a structured response for the given prompt.

        Parameters
        ----------
        prompt:
            The full prompt (system + user) to send.
        schema:
            Pydantic model or JSON schema to extract.
        config:
            Optional LangGraph RunnableConfig for callback propagation.
        **kwargs:
            Additional keyword arguments.

        Returns
        -------
        Any
            The extracted object conforming to the schema.
        """
        try:
            return await self._generate_structured_with_retry(prompt, schema, config=config, **kwargs)
        except ResourceExhausted as exc:
            raise RateLimitError(
                message="Gemini rate limit exceeded after retries.",
                details={"model": self._model_name},
            ) from exc
        except (InternalServerError, ServiceUnavailable) as exc:
            raise ExternalServiceError(
                message=f"Gemini generation failed after retries: {exc}",
                details={"model": self._model_name},
            ) from exc

    @retry(
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(_MAX_RETRIES),
        wait=wait_exponential(min=_WAIT_MIN_SECONDS, max=_WAIT_MAX_SECONDS),
        reraise=True,
    )
    async def _generate_structured_with_retry(
        self, prompt: str, schema: Any, config: dict | None = None, **kwargs: Any
    ) -> Any:
        try:
            invoke_kwargs = {**kwargs}
            if config:
                invoke_kwargs["config"] = config
            llm_with_tool = self._llm.with_structured_output(schema)
            return await llm_with_tool.ainvoke(prompt, **invoke_kwargs)
        except ResourceExhausted as exc:
            logger.warning("Gemini rate limited (429): %s", exc)
            raise
        except (InternalServerError, ServiceUnavailable) as exc:
            logger.warning("Gemini transient error: %s", exc)
            raise
        except Exception as exc:
            logger.exception("Gemini generation failed: %s", exc)
            raise ExternalServiceError(
                message=f"Gemini structured generation failed: {exc}",
                details={"model": self._model_name},
            ) from exc

    # ── Streaming generation ─────────────────────────────────────────

    @observe(name="llm_generate_stream", as_type="generation")
    async def generate_stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """Stream tokens from Gemini for the given prompt.

        Parameters
        ----------
        prompt:
            The full prompt to send.
        **kwargs:
            Additional keyword arguments forwarded to the model invocation.

        Yields
        ------
        str
            Individual text chunks as they are generated.

        Raises
        ------
        RateLimitError
            If the API returns 429 after all retries.
        ExternalServiceError
            If the API returns 500/503 after all retries.
        """
        attempt = 0
        while True:
            try:
                async for chunk in self._llm.astream(prompt, **kwargs):
                    content = chunk.content
                    # Si el contenido es una lista (formato de mensajes de LangChain), extraemos el texto
                    if isinstance(content, list):
                        text_parts = []
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text_parts.append(part.get("text", ""))
                            elif isinstance(part, str):
                                text_parts.append(part)
                        content = "".join(text_parts)

                    if content:
                        yield str(content)
                return
            except ResourceExhausted as exc:
                attempt += 1
                if attempt >= _MAX_RETRIES:
                    raise RateLimitError(
                        message="Gemini rate limit exceeded after retries.",
                        details={"model": self._model_name, "attempts": attempt},
                    ) from exc
                logger.warning("Gemini stream rate limited, retry %d/%d", attempt, _MAX_RETRIES)
                import asyncio

                await asyncio.sleep(min(_WAIT_MIN_SECONDS * (2 ** (attempt - 1)), _WAIT_MAX_SECONDS))
            except (InternalServerError, ServiceUnavailable) as exc:
                attempt += 1
                if attempt >= _MAX_RETRIES:
                    raise ExternalServiceError(
                        message=f"Gemini stream failed after retries: {exc}",
                        details={"model": self._model_name, "attempts": attempt},
                    ) from exc
                logger.warning("Gemini stream transient error, retry %d/%d", attempt, _MAX_RETRIES)
                import asyncio

                await asyncio.sleep(min(_WAIT_MIN_SECONDS * (2 ** (attempt - 1)), _WAIT_MAX_SECONDS))
            except Exception as exc:
                logger.exception("Gemini stream failed: %s", exc)
                raise ExternalServiceError(
                    message=f"Gemini stream failed: {exc}",
                    details={"model": self._model_name},
                ) from exc

    # ── Embeddings ───────────────────────────────────────────────────

    def _get_embeddings_model(self, task_type: str) -> GoogleGenerativeAIEmbeddings:
        """Return a cached embeddings model for the given task_type."""
        if task_type not in self._embeddings_cache:
            emb_kwargs: dict[str, Any] = {
                "model": f"models/{settings.gemini_embedding_model}",
                "task_type": task_type,
            }
            if settings.use_vertex_ai:
                emb_kwargs["vertexai"] = True
                emb_kwargs["project"] = settings.gcp_project_id
                emb_kwargs["location"] = settings.gcp_location
                effective_quota = settings.gcp_quota_project_id or settings.gcp_project_id
                emb_credentials, _ = google.auth.default(quota_project_id=effective_quota)
                emb_kwargs["credentials"] = emb_credentials
            else:
                emb_kwargs["google_api_key"] = settings.gemini_api_key.get_secret_value()
            self._embeddings_cache[task_type] = GoogleGenerativeAIEmbeddings(**emb_kwargs)  # type: ignore[call-arg]
        return self._embeddings_cache[task_type]

    @observe(name="embedding_generate")
    async def embed(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Parameters
        ----------
        texts:
            Texts to embed.
        task_type:
            ``RETRIEVAL_DOCUMENT`` for indexing or ``RETRIEVAL_QUERY`` for search.

        Returns
        -------
        list[list[float]]
            One embedding vector per input text.

        Raises
        ------
        RateLimitError
            If the API returns 429 after all retries.
        ExternalServiceError
            If the API returns 500/503 after all retries.
        """
        return await self._embed_with_retry(texts, task_type)  # type: ignore[no-any-return]

    @retry(
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(_MAX_RETRIES),
        wait=wait_exponential(min=_WAIT_MIN_SECONDS, max=_WAIT_MAX_SECONDS),
        reraise=True,
    )
    async def _embed_with_retry(
        self,
        texts: list[str],
        task_type: str,
    ) -> list[list[float]]:
        try:
            embeddings_model = self._get_embeddings_model(task_type)
            return await embeddings_model.aembed_documents(texts)  # type: ignore[no-any-return]
        except ResourceExhausted as exc:
            logger.warning("Gemini embeddings rate limited (429): %s", exc)
            raise
        except (InternalServerError, ServiceUnavailable) as exc:
            logger.warning("Gemini embeddings transient error: %s", exc)
            raise
        except Exception as exc:
            logger.exception("Gemini embeddings failed: %s", exc)
            raise ExternalServiceError(
                message=f"Gemini embeddings failed: {exc}",
                details={"model": settings.gemini_embedding_model, "task_type": task_type},
            ) from exc

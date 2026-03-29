"""Reranking con Vertex AI Discovery Engine Ranking API.

Implementa la segunda pasada de relevancia sobre los resultados de hybrid
search.  El reranker usa un modelo cross-encoder (``semantic-ranker-512``)
que evalúa la relevancia de cada chunk contra la query original.

Pipeline:
    top-20 chunks (RRF) → Vertex AI Ranking → top-5 reordenados

Fallback automático:
    Si Vertex AI falla (timeout, error 5xx, circuit breaker abierto),
    los chunks se retornan ordenados por su score RRF existente.

Circuit breaker (implementación propia sin dependencias extra):
    - Umbral de fallos consecutivos: 5
    - Tiempo de recuperación: 60 segundos
    - Estado: CLOSED (operativo) → OPEN (bloqueado) → CLOSED

Ver:
    - spec T4-S2-02
    - ADR-008: Vertex AI como ecosistema Google unificado
    - rag-retrieval/references/reranking.md
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from langfuse import observe
except ImportError:

    def observe(*args, **kwargs):  # type: ignore[misc]
        """No-op decorator when langfuse is not installed."""

        def decorator(func):
            return func

        if args and callable(args[0]):
            return args[0]
        return decorator


from src.shared.exceptions import ExternalServiceError

if TYPE_CHECKING:
    from src.infrastructure.rag.retrieval.models import StoredChunk

logger = logging.getLogger(__name__)

# ⭐ Timeout para llamadas a Vertex AI (segundos)
VERTEX_AI_TIMEOUT: float = 10.0

# Modelo de reranking según ADR-008 y blueprint
RANKING_MODEL: str = "semantic-ranker-512@latest"

# Número máximo de documentos soportado por la API
MAX_RANKING_RECORDS: int = 200


# ---------------------------------------------------------------------------
# Circuit Breaker (implementación ligera sin dependencias extra)
# ---------------------------------------------------------------------------


@dataclass
class _CircuitBreakerState:
    """Estado interno del circuit breaker para Vertex AI Ranking API."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0

    # Contadores internos
    _consecutive_failures: int = field(default=0, init=False, repr=False)
    _opened_at: float | None = field(default=None, init=False, repr=False)

    @property
    def is_open(self) -> bool:
        """True si el circuito está abierto (Vertex AI bloqueada)."""
        if self._opened_at is None:
            return False
        elapsed = time.monotonic() - self._opened_at
        if elapsed >= self.recovery_timeout:
            # Auto-reset: pasar a estado HALF-OPEN (permitir un intento)
            self._opened_at = None
            self._consecutive_failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold and self._opened_at is None:
            self._opened_at = time.monotonic()
            logger.error(
                "vertex_circuit_breaker_opened",
                extra={
                    "consecutive_failures": self._consecutive_failures,
                    "recovery_timeout_s": self.recovery_timeout,
                },
            )


# ---------------------------------------------------------------------------
# VertexAIReranker
# ---------------------------------------------------------------------------


class VertexAIReranker:
    """Reranker con Vertex AI Discovery Engine Ranking API.

    Toma los top-N chunks de hybrid search y los reordena según relevancia
    semántica contra la query usando ``semantic-ranker-512@latest``.

    Parameters
    ----------
    project_id:
        GCP project ID.  Si se omite, se toma de ``settings.gcp_project_id``.
    location:
        Región de GCP.  Default ``"global"`` (requerido por Ranking API).
    model:
        Modelo de ranking.  Default ``"semantic-ranker-512@latest"``.
    top_k:
        Número de chunks a retornar tras el reranking.
        Según blueprint: 10; según spec T4-S2-02: 5.
        Default: 5 (spec T4-S2-02).
    failure_threshold:
        Fallos consecutivos antes de abrir el circuit breaker (default 5).
    recovery_timeout:
        Segundos hasta intentar reactivar el circuit breaker (default 60).

    Example
    -------
    >>> reranker = VertexAIReranker(project_id="my-project")
    >>> top_chunks = await reranker.rerank(
    ...     query="Comunicación A 7632",
    ...     chunks=hybrid_results,
    ...     top_k=5,
    ... )
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "global",
        model: str = RANKING_MODEL,
        top_k: int = 5,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        # Importación lazy de settings para evitar problemas en tests
        if project_id is None:
            from src.config.settings import Settings

            project_id = Settings().gcp_project_id  # type: ignore[arg-type]

        self._project_id = project_id or ""
        self._location = location
        self._model = model
        self._top_k = top_k
        self._circuit = _CircuitBreakerState(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

        # Cliente lazy: se inicializa la primera vez que se usa
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Inicializa el cliente Discovery Engine de forma lazy."""
        if self._client is None:
            try:
                from google.cloud import discoveryengine_v1 as discoveryengine

                self._client = discoveryengine.RankServiceClient()
            except ImportError as exc:  # pragma: no cover
                raise ExternalServiceError(
                    message="google-cloud-discoveryengine no instalado. "
                    "Instala: pip install google-cloud-discoveryengine",
                    details={"import_error": str(exc)},
                ) from exc
        return self._client

    # ------------------------------------------------------------------
    # Interfaz pública
    # ------------------------------------------------------------------

    @observe(name="vertex_rerank")
    async def rerank(
        self,
        query: str,
        chunks: list[StoredChunk],
        top_k: int | None = None,
    ) -> list[StoredChunk]:
        """Reordena los chunks por relevancia semántica contra la query.

        Si Vertex AI falla o el circuit breaker está abierto, aplica
        fallback automático: ordena por score RRF existente y retorna top-k.

        Parameters
        ----------
        query:
            Texto de la pregunta del usuario.
        chunks:
            Chunks de hybrid search a reordenar.  Máximo 200 por restricción
            de la API; se usan los primeros ``MAX_RANKING_RECORDS`` si hay más.
        top_k:
            Número de chunks a retornar.  Sobreescribe ``self._top_k``.

        Returns
        -------
        list[StoredChunk]
            Chunks reordenados por relevancia, limitados a ``top_k``.
        """
        if not chunks:
            return []

        effective_top_k = top_k if top_k is not None else self._top_k

        # Limitar a MAX_RANKING_RECORDS (restricción Vertex AI API)
        input_chunks = chunks[:MAX_RANKING_RECORDS]

        # Scores pre-reranking (RRF) para logging en Langfuse
        pre_scores = [{"chunk_id": str(c.id), "rrf_score": c.score} for c in input_chunks]
        logger.info(
            "rerank_pre_scores",
            extra={
                "query": query,
                "input_count": len(input_chunks),
                "pre_scores": pre_scores,
            },
        )

        if self._circuit.is_open:
            logger.warning(
                "vertex_circuit_open_fallback",
                extra={
                    "query": query,
                    "chunks_count": len(input_chunks),
                },
            )
            result = self._fallback_rrf(input_chunks, effective_top_k)
            self._log_post_scores(result, source="rrf_fallback")
            return result

        try:
            reranked = await self._vertex_rerank_with_retry(query, input_chunks, effective_top_k)
            self._circuit.record_success()
            self._log_post_scores(reranked, source="vertex_ai")
            return reranked
        except Exception as exc:
            self._circuit.record_failure()
            logger.warning(
                "rerank_fallback_to_rrf",
                extra={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "chunks_count": len(input_chunks),
                },
            )
            result = self._fallback_rrf(input_chunks, effective_top_k)
            self._log_post_scores(result, source="rrf_fallback")
            return result

    # ------------------------------------------------------------------
    # Retry + llamada a Vertex AI
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    async def _vertex_rerank_with_retry(
        self,
        query: str,
        chunks: list[StoredChunk],
        top_k: int,
    ) -> list[StoredChunk]:
        """Llama a Vertex AI Ranking API con retry (máx. 2 intentos)."""
        return await self._vertex_rerank(query, chunks, top_k)

    async def _vertex_rerank(
        self,
        query: str,
        chunks: list[StoredChunk],
        top_k: int,
    ) -> list[StoredChunk]:
        """Llamada directa a Vertex AI Discovery Engine Ranking API.

        Raises
        ------
        ExternalServiceError
            En caso de timeout o error de la API.
        """
        from google.cloud import discoveryengine_v1 as discoveryengine

        client = self._get_client()

        # Construir los RankingRecord (id = índice como str)
        records = [
            discoveryengine.RankingRecord(
                id=str(i),
                content=chunk.content,
            )
            for i, chunk in enumerate(chunks)
        ]

        ranking_config = f"projects/{self._project_id}/locations/{self._location}/rankingConfigs/default_ranking_config"

        request = discoveryengine.RankRequest(
            ranking_config=ranking_config,
            model=self._model,
            query=query,
            records=records,
            top_n=top_k,
        )

        try:
            # Ejecutar en thread para no bloquear el event loop
            response = await asyncio.wait_for(
                asyncio.to_thread(client.rank, request=request),
                timeout=VERTEX_AI_TIMEOUT,
            )
        except TimeoutError as exc:
            logger.error(
                "vertex_rerank_timeout",
                extra={
                    "timeout_s": VERTEX_AI_TIMEOUT,
                    "chunks_count": len(chunks),
                },
            )
            raise ExternalServiceError(
                message="Vertex AI reranking timeout",
                details={"timeout_seconds": VERTEX_AI_TIMEOUT},
            ) from exc
        except Exception as exc:
            logger.error(
                "vertex_rerank_error",
                extra={"error": str(exc)},
            )
            raise ExternalServiceError(
                message="Vertex AI reranking failed",
                details={"error": str(exc)},
            ) from exc

        # Mapear resultados: response.records ya viene ordenado por score
        reranked: list[StoredChunk] = []
        for result in response.records:
            idx = int(result.id)
            chunk = chunks[idx]
            chunk.score = float(result.score)
            reranked.append(chunk)

        logger.info(
            "rerank_completed",
            extra={
                "input_chunks": len(chunks),
                "output_chunks": len(reranked),
                "top_score": reranked[0].score if reranked else 0.0,
            },
        )

        return reranked

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _fallback_rrf(
        self,
        chunks: list[StoredChunk],
        top_k: int,
    ) -> list[StoredChunk]:
        """Fallback: ordena por score RRF existente y retorna top-k.

        Se activa cuando Vertex AI no está disponible.  Los chunks ya
        tienen el score RRF asignado por ``HybridSearchService``.
        """
        sorted_chunks = sorted(chunks, key=lambda c: c.score, reverse=True)
        result = sorted_chunks[:top_k]

        logger.info(
            "rrf_fallback_applied",
            extra={
                "input_chunks": len(chunks),
                "output_chunks": len(result),
            },
        )

        return result

    # ------------------------------------------------------------------
    # Observabilidad
    # ------------------------------------------------------------------

    def _log_post_scores(
        self,
        chunks: list[StoredChunk],
        source: str,
    ) -> None:
        """Registra scores post-reranking para observabilidad en Langfuse.

        Los scores se loguean como metadata del span ``@observe`` activo
        y también en logging estándar para troubleshooting local.

        Parameters
        ----------
        chunks:
            Chunks ya reordenados con su score actualizado.
        source:
            Origen del score: ``"vertex_ai"`` o ``"rrf_fallback"``.
        """
        post_scores = [{"chunk_id": str(c.id), "score": c.score} for c in chunks]

        logger.info(
            "rerank_post_scores",
            extra={
                "source": source,
                "output_count": len(chunks),
                "post_scores": post_scores,
                "top_score": chunks[0].score if chunks else 0.0,
            },
        )

        # Actualizar metadata del span Langfuse activo (si existe)
        try:
            from langfuse import get_client

            langfuse = get_client()
            langfuse.update_current_span(
                metadata={
                    "rerank_source": source,
                    "output_count": len(chunks),
                    "post_scores": post_scores,
                },
            )
        except Exception:  # noqa: S110
            # Langfuse no disponible o span no activo — no es crítico
            pass

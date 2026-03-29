"""Servicio reutilizable para evaluar el pipeline RAG con RAGAS."""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import fmean
from typing import Any, cast

from langchain_core.messages import HumanMessage
from ragas import EvaluationDataset, SingleTurnSample, evaluate  # type: ignore[import-not-found]
from ragas.embeddings.base import LangchainEmbeddingsWrapper  # type: ignore[import-not-found]
from ragas.llms.base import LangchainLLMWrapper  # type: ignore[import-not-found]
from ragas.metrics.collections.answer_relevancy.metric import AnswerRelevancy  # type: ignore[import-not-found]
from ragas.metrics.collections.context_precision.metric import ContextPrecision  # type: ignore[import-not-found]
from ragas.metrics.collections.context_recall.metric import ContextRecall  # type: ignore[import-not-found]
from ragas.metrics.collections.faithfulness.metric import Faithfulness  # type: ignore[import-not-found]

from src.application.graphs.nodes.generate import generate_node
from src.application.graphs.rag_graph import build_rag_graph
from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.observability.langfuse_client import get_langfuse, shutdown_langfuse

logger = logging.getLogger(__name__)

DEFAULT_GOLDEN_DATASET_PATH = "data/golden_dataset_sample.json"
DEFAULT_RAGAS_THRESHOLDS: dict[str, float] = {
    "faithfulness": 0.90,
    "answer_relevancy": 0.85,
    "context_precision": 0.80,
    "context_recall": 0.80,
}
_METRIC_NAMES = tuple(DEFAULT_RAGAS_THRESHOLDS.keys())


@dataclass(slots=True)
class GoldenDatasetEntry:
    question: str
    ground_truth: str
    contexts: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GoldenDatasetEntry":
        question = str(payload.get("question", "")).strip()
        ground_truth = str(payload.get("ground_truth", "")).strip()
        contexts = payload.get("contexts") or []
        if not question:
            raise ValueError("Golden dataset entry missing 'question'")
        if not ground_truth:
            raise ValueError("Golden dataset entry missing 'ground_truth'")
        if not isinstance(contexts, list) or not all(isinstance(item, str) and item.strip() for item in contexts):
            raise ValueError("Golden dataset entry missing valid 'contexts'")
        metadata = payload.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("Golden dataset entry 'metadata' must be an object")
        return cls(
            question=question,
            ground_truth=ground_truth,
            contexts=[item.strip() for item in contexts],
            metadata=metadata,
        )


@dataclass(slots=True)
class QueryExecutionResult:
    question: str
    ground_truth: str
    reference_contexts: list[str]
    response: str
    retrieved_contexts: list[str]
    query_type: str
    sources: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_ragas_sample(self) -> SingleTurnSample:
        return SingleTurnSample(
            user_input=self.question,
            response=self.response,
            retrieved_contexts=self.retrieved_contexts,
            reference=self.ground_truth,
            reference_contexts=self.reference_contexts,
        )


@dataclass(slots=True)
class RagasEvaluationSummary:
    sample_count: int
    metrics: dict[str, float]
    thresholds: dict[str, float]
    below_thresholds: dict[str, float]
    sample_results: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RAGASEvaluator:
    """Evalua respuestas RAG con el pipeline real y metricas RAGAS."""

    def __init__(self) -> None:
        self._rag_graph = build_rag_graph(checkpointer=None)
        self._llm_client = GeminiClient(model=GeminiModel.FLASH)

    def load_golden_dataset(self, dataset_path: str | Path = DEFAULT_GOLDEN_DATASET_PATH) -> list[GoldenDatasetEntry]:
        path = Path(dataset_path)
        raw_data = json.loads(path.read_text(encoding="utf-8"))
        raw_samples = raw_data.get("samples", raw_data) if isinstance(raw_data, dict) else raw_data
        if not isinstance(raw_samples, list) or not raw_samples:
            raise ValueError("Golden dataset must contain a non-empty list of samples")
        return [GoldenDatasetEntry.from_dict(item) for item in raw_samples]

    async def run_queries(self, dataset_entries: list[GoldenDatasetEntry]) -> list[QueryExecutionResult]:
        results: list[QueryExecutionResult] = []

        for entry in dataset_entries:
            graph_input: dict[str, Any] = {
                "query": entry.question,
                "user_id": 0,
                "messages": [HumanMessage(content=entry.question)],
            }
            prep_result = await self._rag_graph.ainvoke(cast("Any", graph_input))
            generation_state = cast("dict[str, Any]", {**prep_result, "query": entry.question})
            generation_result = await generate_node(generation_state)

            chunks = prep_result.get("reranked_chunks") or prep_result.get("retrieved_chunks") or []
            retrieved_contexts = [str(chunk.get("content", "")).strip() for chunk in chunks if chunk.get("content")]
            response = str(generation_result.get("response") or prep_result.get("response") or "").strip()

            results.append(
                QueryExecutionResult(
                    question=entry.question,
                    ground_truth=entry.ground_truth,
                    reference_contexts=entry.contexts,
                    response=response,
                    retrieved_contexts=retrieved_contexts,
                    query_type=str(prep_result.get("query_type", "consulta")),
                    sources=list(generation_result.get("sources") or prep_result.get("sources") or []),
                    metadata=entry.metadata,
                )
            )

        return results

    def compute_metrics(
        self,
        query_results: list[QueryExecutionResult],
        thresholds: dict[str, float] | None = None,
    ) -> RagasEvaluationSummary:
        if not query_results:
            raise ValueError("At least one query result is required to compute RAGAS metrics")

        threshold_values = {**DEFAULT_RAGAS_THRESHOLDS, **(thresholds or {})}
        evaluation_dataset = EvaluationDataset(samples=[result.to_ragas_sample() for result in query_results])

        ragas_llm = LangchainLLMWrapper(self._llm_client.get_langchain_chat_model())
        ragas_embeddings = LangchainEmbeddingsWrapper(self._llm_client.get_langchain_embeddings("RETRIEVAL_QUERY"))
        metrics = [
            Faithfulness(llm=ragas_llm),  # type: ignore[arg-type]
            AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings),  # type: ignore[arg-type]
            ContextPrecision(llm=ragas_llm),  # type: ignore[arg-type]
            ContextRecall(llm=ragas_llm),  # type: ignore[arg-type]
        ]

        evaluation_result = evaluate(
            dataset=evaluation_dataset,
            metrics=metrics,  # type: ignore[arg-type]
            llm=ragas_llm,
            embeddings=ragas_embeddings,
            raise_exceptions=False,
            show_progress=False,
        )

        aggregated_metrics = {
            metric_name: self._mean_metric(evaluation_result[metric_name])  # type: ignore[index,arg-type]
            for metric_name in _METRIC_NAMES
        }
        below_thresholds = {
            metric_name: metric_value
            for metric_name, metric_value in aggregated_metrics.items()
            if metric_value < threshold_values[metric_name]
        }

        sample_results: list[dict[str, Any]] = []
        for query_result, score_row in zip(query_results, evaluation_result.scores, strict=True):  # type: ignore[union-attr]
            sample_results.append(
                {
                    "question": query_result.question,
                    "ground_truth": query_result.ground_truth,
                    "response": query_result.response,
                    "query_type": query_result.query_type,
                    "retrieved_contexts": query_result.retrieved_contexts,
                    "reference_contexts": query_result.reference_contexts,
                    "sources": query_result.sources,
                    "metadata": query_result.metadata,
                    "metrics": {metric_name: float(score_row.get(metric_name) or 0.0) for metric_name in _METRIC_NAMES},
                }
            )

        return RagasEvaluationSummary(
            sample_count=len(query_results),
            metrics=aggregated_metrics,
            thresholds=threshold_values,
            below_thresholds=below_thresholds,
            sample_results=sample_results,
        )

    def evaluate_dataset(
        self,
        dataset_entries: list[GoldenDatasetEntry],
        thresholds: dict[str, float] | None = None,
    ) -> RagasEvaluationSummary:
        query_results = asyncio.run(self.run_queries(dataset_entries))
        return self.compute_metrics(query_results, thresholds=thresholds)

    def send_scores_to_langfuse(self, summary: RagasEvaluationSummary, dataset_path: str) -> None:
        langfuse = get_langfuse()
        if langfuse is None:
            logger.info("langfuse_disabled_skip_ragas_scores")
            return

        try:
            with langfuse.start_as_current_observation(
                as_type="span",
                name="ragas_evaluation",
            ) as span:
                for metric_name, metric_value in summary.metrics.items():
                    span.score(
                        name=metric_name,
                        value=float(metric_value),
                        data_type="NUMERIC",
                        comment=f"RAGAS aggregate metric for dataset {dataset_path}",
                    )
        except Exception:
            logger.exception("langfuse_ragas_score_submission_failed")
        finally:
            shutdown_langfuse()

    @staticmethod
    def _mean_metric(values: list[float | None]) -> float:
        valid_values = [float(value) for value in values if value is not None]
        if not valid_values:
            return 0.0
        return round(fmean(valid_values), 4)

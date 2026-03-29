"""DAG programado de evaluacion RAGAS para monitoreo de calidad del pipeline RAG."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow.sdk import DAG, task

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}

DEFAULT_GOLDEN_DATASET_PATH = "data/golden_dataset_sample.json"
DEFAULT_THRESHOLDS = {
    "faithfulness": 0.90,
    "answer_relevancy": 0.85,
    "context_precision": 0.80,
    "context_recall": 0.80,
}


def _get_schedule() -> str:
    try:
        from airflow.models import Variable

        return str(Variable.get("ragas_evaluation_schedule", default_var="@daily"))
    except Exception:
        return "@daily"


def _get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return url


def _get_sync_connection():
    import psycopg

    url = _get_db_url()
    if "+psycopg" in url:
        url = url.replace("+psycopg", "")
    elif "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    return psycopg.connect(url)


def _resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    project_root = Path(os.environ.get("PROJECT_ROOT", "/opt/airflow"))
    return project_root / path


def _load_thresholds_from_variable() -> dict[str, float]:
    thresholds = DEFAULT_THRESHOLDS
    try:
        from airflow.models import Variable

        raw_thresholds = Variable.get(
            "ragas_evaluation_thresholds",
            default_var=json.dumps(DEFAULT_THRESHOLDS),
        )
        parsed_thresholds = json.loads(raw_thresholds)
        if isinstance(parsed_thresholds, dict):
            thresholds = {key: float(value) for key, value in parsed_thresholds.items()}
    except Exception:
        logger.exception("ragas_thresholds_variable_read_failed")
    return thresholds


def _store_ragas_evaluation(
    *,
    dag_run_id: str,
    dataset_path: str,
    sample_count: int,
    metrics: dict[str, float],
    thresholds: dict[str, float],
    below_thresholds: dict[str, float],
    sample_results: list[dict],
) -> str:
    with _get_sync_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ragas_evaluations (
                    dag_run_id,
                    dataset_path,
                    sample_count,
                    faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall,
                    thresholds,
                    below_thresholds,
                    sample_results
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    dag_run_id,
                    dataset_path,
                    sample_count,
                    metrics["faithfulness"],
                    metrics["answer_relevancy"],
                    metrics["context_precision"],
                    metrics["context_recall"],
                    json.dumps(thresholds),
                    json.dumps(below_thresholds),
                    json.dumps(sample_results),
                ),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("Failed to persist ragas evaluation result")
        conn.commit()
    return str(row[0])


with DAG(
    dag_id="ragas_evaluation",
    description="Evalua diariamente el pipeline RAG contra un golden dataset con metricas RAGAS.",
    start_date=datetime(2025, 1, 1),
    schedule=_get_schedule(),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["evaluation", "rag", "observability", "ragas"],
    params={
        "dataset_path": DEFAULT_GOLDEN_DATASET_PATH,
    },
) as dag:

    @task()
    def load_golden_dataset(**context) -> dict:
        from src.infrastructure.evaluation.ragas_evaluator import RAGASEvaluator

        conf = context["dag_run"].conf or {}
        dataset_path = str(conf.get("dataset_path", DEFAULT_GOLDEN_DATASET_PATH))
        resolved_path = _resolve_project_path(dataset_path)

        evaluator = RAGASEvaluator()
        dataset_entries = evaluator.load_golden_dataset(resolved_path)

        return {
            "dataset_path": str(resolved_path),
            "samples": [
                {
                    "question": sample.question,
                    "ground_truth": sample.ground_truth,
                    "contexts": sample.contexts,
                    "metadata": sample.metadata,
                }
                for sample in dataset_entries
            ],
            "sample_count": len(dataset_entries),
        }

    @task()
    def run_queries(dataset_payload: dict) -> dict:
        from src.infrastructure.evaluation.ragas_evaluator import GoldenDatasetEntry, RAGASEvaluator

        evaluator = RAGASEvaluator()
        entries = [GoldenDatasetEntry.from_dict(sample) for sample in dataset_payload["samples"]]
        query_results = asyncio.run(evaluator.run_queries(entries))

        return {
            "dataset_path": dataset_payload["dataset_path"],
            "sample_count": dataset_payload["sample_count"],
            "query_results": [
                {
                    "question": item.question,
                    "ground_truth": item.ground_truth,
                    "reference_contexts": item.reference_contexts,
                    "response": item.response,
                    "retrieved_contexts": item.retrieved_contexts,
                    "query_type": item.query_type,
                    "sources": item.sources,
                    "metadata": item.metadata,
                }
                for item in query_results
            ],
        }

    @task()
    def compute_metrics(query_payload: dict) -> dict:
        from src.infrastructure.evaluation.ragas_evaluator import QueryExecutionResult, RAGASEvaluator

        evaluator = RAGASEvaluator()
        query_results = [QueryExecutionResult(**item) for item in query_payload["query_results"]]
        thresholds = _load_thresholds_from_variable()
        summary = evaluator.compute_metrics(query_results, thresholds=thresholds)

        return {
            "dataset_path": query_payload["dataset_path"],
            "sample_count": query_payload["sample_count"],
            "metrics": summary.metrics,
            "thresholds": summary.thresholds,
            "below_thresholds": summary.below_thresholds,
            "sample_results": summary.sample_results,
        }

    @task()
    def store_results(metrics_payload: dict, **context) -> dict:
        from src.infrastructure.evaluation.ragas_evaluator import RagasEvaluationSummary, RAGASEvaluator

        dag_run_id = context["dag_run"].run_id
        evaluation_id = _store_ragas_evaluation(
            dag_run_id=dag_run_id,
            dataset_path=metrics_payload["dataset_path"],
            sample_count=int(metrics_payload["sample_count"]),
            metrics=metrics_payload["metrics"],
            thresholds=metrics_payload["thresholds"],
            below_thresholds=metrics_payload["below_thresholds"],
            sample_results=metrics_payload["sample_results"],
        )

        summary = RagasEvaluationSummary(
            sample_count=int(metrics_payload["sample_count"]),
            metrics=metrics_payload["metrics"],
            thresholds=metrics_payload["thresholds"],
            below_thresholds=metrics_payload["below_thresholds"],
            sample_results=metrics_payload["sample_results"],
        )
        evaluator = RAGASEvaluator()
        evaluator.send_scores_to_langfuse(summary, metrics_payload["dataset_path"])

        return {
            "evaluation_id": evaluation_id,
            "dataset_path": metrics_payload["dataset_path"],
            "metrics": metrics_payload["metrics"],
            "thresholds": metrics_payload["thresholds"],
            "below_thresholds": metrics_payload["below_thresholds"],
        }

    @task()
    def alert_on_regression(store_payload: dict) -> dict:
        below_thresholds = store_payload["below_thresholds"]
        if below_thresholds:
            from airflow.exceptions import AirflowException

            message = ", ".join(f"{name}={value:.4f}" for name, value in below_thresholds.items())
            raise AirflowException(f"RAGAS regression detected: {message}")

        logger.info("ragas_evaluation_ok metrics=%s", store_payload["metrics"])
        return {
            "status": "ok",
            "evaluation_id": store_payload["evaluation_id"],
        }

    loaded_dataset = load_golden_dataset()
    query_results = run_queries(loaded_dataset)
    metric_results = compute_metrics(query_results)
    persisted_results = store_results(metric_results)
    alert_on_regression(persisted_results)

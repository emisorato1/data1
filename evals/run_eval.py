"""Entry point: python -m evals.run_eval

Executes golden dataset single-turn questions against a deployed API,
evaluates responses, and generates JSON + Markdown reports.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.infrastructure.security.guardrails.pii_detector import PiiAction, PiiOutputDetector

from evals.runner.api_client import APIClient
from evals.runner.evaluator import evaluate_sample
from evals.runner.langfuse_reporter import send_scores
from evals.runner.reporter import build_report, save_json_report, save_markdown_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────

GOLDEN_DIR = Path(__file__).parent / "datasets" / "golden"
EXPERIMENTS_DIR = Path(__file__).parent / "experiments"

# All evaluation categories
CATEGORIES: dict[str, str] = {
    "retrieval_accuracy": "retrieval_accuracy.json",
    "guardrails_input": "guardrails_input.json",
    "topic_classification": "topic_classification.json",
    "guardrails_output": "guardrails_output.json",
    "system_prompt_behavior": "system_prompt_behavior.json",
    "ambiguous_queries": "ambiguous_queries.json",
    "cache_behavior": "cache_behavior.json",
    "memory_shortterm": "memory_shortterm.json",
    "memory_episodic": "memory_episodic.json",
}


def _get_env(name: str, required: bool = True, default: str = "") -> str:
    """Read an environment variable."""
    value = os.environ.get(name, default)
    if required and not value:
        logger.error("Missing required environment variable: %s", name)
        sys.exit(1)
    return value


def _load_categories(selected: str) -> dict[str, list[dict[str, Any]]]:
    """Load golden dataset samples for selected categories."""
    if selected == "all":
        cats = list(CATEGORIES.keys())
    else:
        cats = [c.strip() for c in selected.split(",") if c.strip()]

    result: dict[str, list[dict[str, Any]]] = {}
    for cat in cats:
        filename = CATEGORIES.get(cat)
        if filename is None:
            logger.warning("Unknown category '%s' — skipping", cat)
            continue
        path = GOLDEN_DIR / filename
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        result[cat] = data["samples"]
        logger.info("Loaded %d samples for %s", len(data["samples"]), cat)

    return result


def _run_category(
    client: APIClient,
    category: str,
    samples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Execute all samples in a category, return result dicts."""
    if category == "memory_shortterm":
        return _run_memory_shortterm(client, category, samples)
    if category == "memory_episodic":
        return _run_memory_episodic(client, category, samples)
    if category == "cache_behavior":
        return _run_cache_behavior(client, category, samples)

    results: list[dict[str, Any]] = []
    for sample in samples:
        sample_id = sample["id"]

        # guardrails_output uses simulated_output, not API call
        if category == "guardrails_output":
            results.append(_evaluate_output_guardrail(sample))
            continue

        # Create isolated conversation
        start = time.monotonic()
        try:
            conv_id = client.create_conversation()
            sse = client.send_message(conv_id, sample["input"])
        except Exception as exc:
            results.append(
                {
                    "id": sample_id,
                    "category": category,
                    "input": sample.get("input", ""),
                    "expected_output": sample.get("expected_output", ""),
                    "expected_behavior": sample.get("expected_behavior", ""),
                    "actual_output": "",
                    "sources": [],
                    "verdict": "fail",
                    "reason": f"connection error: {exc}",
                    "duration_ms": round((time.monotonic() - start) * 1000),
                }
            )
            continue

        duration_ms = round((time.monotonic() - start) * 1000)

        if sse.error:
            results.append(
                {
                    "id": sample_id,
                    "category": category,
                    "input": sample.get("input", ""),
                    "expected_output": sample.get("expected_output", ""),
                    "expected_behavior": sample.get("expected_behavior", ""),
                    "actual_output": sse.content,
                    "sources": sse.sources,
                    "verdict": "fail",
                    "reason": f"SSE error: {sse.error}",
                    "duration_ms": duration_ms,
                }
            )
            continue

        verdict = evaluate_sample(sample, sse.content, sse.guardrail_blocked)
        results.append(
            {
                "id": sample_id,
                "category": category,
                "input": sample.get("input", ""),
                "expected_output": sample.get("expected_output", ""),
                "expected_behavior": sample.get("expected_behavior", ""),
                "actual_output": sse.content,
                "sources": sse.sources,
                "verdict": "pass" if verdict.passed else "fail",
                "reason": verdict.reason,
                "duration_ms": duration_ms,
            }
        )

        status = "PASS" if verdict.passed else "FAIL"
        logger.info("[%s] %s — %s (%dms)", status, sample_id, verdict.reason, duration_ms)

    return results


# ── PII detector for guardrails_output evaluation ────────────
# Lazy-initialized to avoid rebuilding on each sample.
_pii_detector: PiiOutputDetector | None = None

FALLBACK_MESSAGE_PII = (
    "No puedo proporcionar esa informacion porque contiene datos personales sensibles. "
    "Consulte con su oficial de cuenta."
)


def _get_pii_detector() -> PiiOutputDetector:
    """Return a lazily-initialized PiiOutputDetector with production defaults."""
    global _pii_detector
    if _pii_detector is None:
        _pii_detector = PiiOutputDetector(
            default_action=PiiAction.REDACT,
            block_threshold=3,
        )
    return _pii_detector


def _evaluate_output_guardrail(sample: dict[str, Any]) -> dict[str, Any]:
    """Evaluate output guardrail samples using simulated_output (no API call).

    Runs PiiOutputDetector.detect() on the simulated text before evaluation
    so that redaction tokens and block messages are present for the evaluator.
    """
    simulated = sample.get("simulated_output", "")

    detector = _get_pii_detector()
    result = detector.detect(simulated)

    if result.was_blocked:
        actual_output = FALLBACK_MESSAGE_PII
        guardrail_blocked = True
    elif result.has_pii:
        actual_output = result.redacted_text
        guardrail_blocked = False
    else:
        actual_output = simulated
        guardrail_blocked = False

    verdict = evaluate_sample(sample, actual_output, guardrail_blocked=guardrail_blocked)
    return {
        "id": sample["id"],
        "category": "guardrails_output",
        "input": sample.get("scenario", ""),
        "expected_output": sample.get("expected_behavior", ""),
        "expected_behavior": sample.get("expected_behavior", ""),
        "actual_output": actual_output,
        "sources": [],
        "verdict": "pass" if verdict.passed else "fail",
        "reason": verdict.reason,
        "duration_ms": 0,
    }


def _run_memory_shortterm(client: APIClient, category: str, samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for sample in samples:
        sample_id = sample["id"]
        conv_id = client.create_conversation()
        start = time.monotonic()
        last_sse = None
        turn_verdicts: list[tuple[int, Any]] = []
        try:
            for turn_idx, turn in enumerate(sample["turns"]):
                if turn["role"] == "user":
                    last_sse = client.send_message(conv_id, turn["content"])
                elif turn["role"] == "assistant" and last_sse:
                    verdict = evaluate_sample(turn, last_sse.content, last_sse.guardrail_blocked)
                    turn_verdicts.append((turn_idx, verdict))
        except Exception as exc:
            results.append(
                {
                    "id": sample_id,
                    "category": category,
                    "input": sample.get("scenario", ""),
                    "expected_output": "",
                    "expected_behavior": "chain",
                    "actual_output": "",
                    "verdict": "fail",
                    "reason": str(exc),
                    "duration_ms": 0,
                    "sources": [],
                }
            )
            continue

        duration_ms = round((time.monotonic() - start) * 1000)

        # Fail if ANY assistant turn failed
        failed_turns = [(idx, v) for idx, v in turn_verdicts if not v.passed]
        all_passed = len(failed_turns) == 0 and len(turn_verdicts) > 0

        if failed_turns:
            fail_detail = "; ".join(f"turn {idx}: {v.reason}" for idx, v in failed_turns)
            reason = f"failed turns: {fail_detail}"
        elif turn_verdicts:
            reason = turn_verdicts[-1][1].reason
        else:
            reason = "empty chain"

        expected_behavior = sample["turns"][-1].get("expected_behavior", "")
        results.append(
            {
                "id": sample_id,
                "category": category,
                "input": sample.get("scenario", ""),
                "expected_output": "",
                "expected_behavior": expected_behavior,
                "actual_output": last_sse.content if last_sse else "",
                "sources": last_sse.sources if last_sse else [],
                "verdict": "pass" if all_passed else "fail",
                "reason": reason,
                "duration_ms": duration_ms,
            }
        )
        status = "PASS" if all_passed else "FAIL"
        logger.info("[%s] %s — %s (%dms)", status, sample_id, reason, duration_ms)
    return results


def _run_memory_episodic(client: APIClient, category: str, samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    pairs = {}
    for sample in samples:
        pairs.setdefault(sample.get("pair", 0), []).append(sample)

    for pair_id, pair_samples in pairs.items():
        # Execute sequentially: store then recall
        for sample in sorted(pair_samples, key=lambda s: s.get("phase", "") == "recall"):
            sample_id = sample["id"]
            conv_id = client.create_conversation()
            start = time.monotonic()
            try:
                sse = client.send_message(conv_id, sample["input"])
            except Exception as exc:
                results.append(
                    {
                        "id": sample_id,
                        "category": category,
                        "input": sample.get("input", ""),
                        "expected_output": "",
                        "expected_behavior": sample.get("expected_behavior", ""),
                        "actual_output": "",
                        "verdict": "fail",
                        "reason": str(exc),
                        "duration_ms": 0,
                        "sources": [],
                    }
                )
                continue

            duration_ms = round((time.monotonic() - start) * 1000)
            verdict = evaluate_sample(sample, sse.content, sse.guardrail_blocked)
            results.append(
                {
                    "id": sample_id,
                    "category": category,
                    "input": sample.get("input", ""),
                    "expected_output": "",
                    "expected_behavior": sample.get("expected_behavior", ""),
                    "actual_output": sse.content,
                    "sources": sse.sources,
                    "verdict": "pass" if verdict.passed else "fail",
                    "reason": verdict.reason,
                    "duration_ms": duration_ms,
                }
            )
            status = "PASS" if verdict.passed else "FAIL"
            logger.info("[%s] %s (pair %s) — %s (%dms)", status, sample_id, pair_id, verdict.reason, duration_ms)
    return results


def _run_cache_behavior(client: APIClient, category: str, samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for sample in samples:
        sample_id = sample["id"]
        conv_id = client.create_conversation()

        # First call (prime)
        client.send_message(conv_id, sample["input"])

        # Second call (measure time + validate content)
        start = time.monotonic()
        try:
            sse = client.send_message(conv_id, sample["input"])
        except Exception as exc:
            results.append(
                {
                    "id": sample_id,
                    "category": category,
                    "input": sample.get("input", ""),
                    "expected_output": "",
                    "expected_behavior": "cache_hit",
                    "actual_output": "",
                    "verdict": "fail",
                    "reason": str(exc),
                    "duration_ms": 0,
                    "sources": [],
                }
            )
            continue

        duration_ms = round((time.monotonic() - start) * 1000)

        if sse.error:
            verdict_passed = False
            reason = f"SSE error: {sse.error}"
        else:
            # Primary: validate content correctness
            content_verdict = evaluate_sample(sample, sse.content, sse.guardrail_blocked)
            verdict_passed = content_verdict.passed
            reason = f"{content_verdict.reason} ({duration_ms}ms)"

        results.append(
            {
                "id": sample_id,
                "category": category,
                "input": sample.get("input", ""),
                "expected_output": "",
                "expected_behavior": "cache_hit",
                "actual_output": sse.content[:200] if not sse.error else "",
                "sources": sse.sources if not sse.error else [],
                "verdict": "pass" if verdict_passed else "fail",
                "reason": reason,
                "duration_ms": duration_ms,
            }
        )
        status = "PASS" if verdict_passed else "FAIL"
        logger.info("[%s] %s — %s", status, sample_id, reason)
    return results


def main() -> None:
    """Run the evaluation pipeline."""
    api_url = _get_env("EVAL_API_URL", required=False, default="http://localhost:8000")
    email = _get_env("EVAL_USER_EMAIL", required=False, default="admin@banco.com")
    password = _get_env("EVAL_USER_PASSWORD", required=False, default="admin123!")
    categories_filter = _get_env("EVAL_CATEGORIES", required=False, default="all")
    timeout = float(_get_env("EVAL_TIMEOUT", required=False, default="60"))

    run_id = str(uuid.uuid4())
    start_time = datetime.now(UTC)
    logger.info("Starting eval run %s against %s", run_id, api_url)

    # Load datasets
    datasets = _load_categories(categories_filter)
    if not datasets:
        logger.error("No categories to evaluate")
        sys.exit(1)

    # Authenticate and run
    all_results: list[dict[str, Any]] = []
    with APIClient(base_url=api_url, timeout=timeout) as client:
        client.login(email, password)

        for category, samples in datasets.items():
            logger.info("── %s (%d samples) ──", category, len(samples))
            results = _run_category(client, category, samples)
            all_results.extend(results)

    # Build report
    report = build_report(
        run_id=run_id,
        api_url=api_url,
        start_time=start_time,
        results=all_results,
    )

    # Save reports
    output_dir = EXPERIMENTS_DIR / run_id
    json_path = save_json_report(report, output_dir)
    md_path = save_markdown_report(report, output_dir)

    logger.info("JSON report: %s", json_path)
    logger.info("Markdown report: %s", md_path)

    # Langfuse (optional)
    send_scores(report)

    # Terminal summary
    s = report["summary"]
    print(f"\n{'=' * 50}")  # noqa: T201
    print(f"Eval Run: {run_id}")  # noqa: T201
    print(f"Total: {s['total']} | Pass: {s['passed']} | Fail: {s['failed']} | Rate: {s['pass_rate'] * 100:.1f}%")  # noqa: T201
    for cat, data in report["categories"].items():
        print(f"  {cat}: {data['passed']}/{data['total']} ({data['pass_rate'] * 100:.1f}%)")  # noqa: T201
    print(f"{'=' * 50}\n")  # noqa: T201

    # Exit code: 0 if all pass, 1 otherwise
    sys.exit(0 if s["failed"] == 0 else 1)


if __name__ == "__main__":
    main()

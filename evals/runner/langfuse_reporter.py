"""Optional Langfuse integration: send scores from eval runs.

Only activates when LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def is_langfuse_configured() -> bool:
    """Check if Langfuse credentials are available."""
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def send_scores(report: dict[str, Any]) -> None:
    """Send per-sample and per-category scores to Langfuse.

    Creates one trace per eval run, with individual scores for each sample
    and aggregated pass_rate scores per category.
    """
    if not is_langfuse_configured():
        logger.info("Langfuse not configured — skipping score upload")
        return

    try:
        from langfuse import Langfuse
    except ImportError:
        logger.warning("langfuse package not installed — skipping score upload")
        return

    langfuse = Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )

    run_id = report["run_id"]

    trace = langfuse.trace(  # type: ignore[attr-defined]
        name=f"eval_run_{run_id}",
        metadata={
            "run_id": run_id,
            "api_url": report["api_url"],
            "timestamp": report["timestamp"],
            "total": report["summary"]["total"],
            "pass_rate": report["summary"]["pass_rate"],
        },
    )

    # Per-sample scores
    for result in report["results"]:
        trace.score(
            name=result["id"],
            value=1.0 if result["verdict"] == "pass" else 0.0,
            comment=result["reason"],
        )

    # Per-category aggregated scores
    for category, data in report["categories"].items():
        trace.score(
            name=f"eval_{category}_pass_rate",
            value=data["pass_rate"],
            comment=f"{data['passed']}/{data['total']} passed",
        )

    langfuse.flush()
    logger.info("Scores sent to Langfuse (trace: eval_run_%s)", run_id)

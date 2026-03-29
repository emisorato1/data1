"""Conftest for golden evaluation framework.

Provides fixtures for loading golden datasets, configuring eval markers,
and shared utilities for all eval test modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

GOLDEN_DIR = Path(__file__).parent / "datasets" / "golden"


def _load_golden(filename: str) -> dict[str, Any]:
    """Load a golden dataset JSON file."""
    path = GOLDEN_DIR / filename
    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


# ── Dataset fixtures ──


@pytest.fixture(scope="session")
def golden_manifest() -> dict[str, Any]:
    """Load the golden dataset manifest with version and category metadata."""
    return _load_golden("manifest.json")


@pytest.fixture(scope="session")
def retrieval_accuracy_dataset() -> list[dict[str, Any]]:
    """Load retrieval accuracy samples (RA-001..RA-018)."""
    samples: list[dict[str, Any]] = _load_golden("retrieval_accuracy.json")["samples"]
    return samples


@pytest.fixture(scope="session")
def memory_shortterm_dataset() -> list[dict[str, Any]]:
    """Load short-term memory samples (MS-001..MS-009)."""
    samples: list[dict[str, Any]] = _load_golden("memory_shortterm.json")["samples"]
    return samples


@pytest.fixture(scope="session")
def memory_episodic_dataset() -> list[dict[str, Any]]:
    """Load episodic memory samples (ME-001..ME-006)."""
    samples: list[dict[str, Any]] = _load_golden("memory_episodic.json")["samples"]
    return samples


@pytest.fixture(scope="session")
def guardrails_input_dataset() -> list[dict[str, Any]]:
    """Load input guardrails samples (GI-001..GI-009)."""
    samples: list[dict[str, Any]] = _load_golden("guardrails_input.json")["samples"]
    return samples


@pytest.fixture(scope="session")
def topic_classification_dataset() -> list[dict[str, Any]]:
    """Load topic classification samples (TC-001..TC-008)."""
    samples: list[dict[str, Any]] = _load_golden("topic_classification.json")["samples"]
    return samples


@pytest.fixture(scope="session")
def guardrails_output_dataset() -> list[dict[str, Any]]:
    """Load output guardrails samples (GO-001..GO-006)."""
    samples: list[dict[str, Any]] = _load_golden("guardrails_output.json")["samples"]
    return samples


@pytest.fixture(scope="session")
def system_prompt_dataset() -> list[dict[str, Any]]:
    """Load system prompt behavior samples (SP-001..SP-006)."""
    samples: list[dict[str, Any]] = _load_golden("system_prompt_behavior.json")["samples"]
    return samples


@pytest.fixture(scope="session")
def ambiguous_queries_dataset() -> list[dict[str, Any]]:
    """Load ambiguous queries samples (AQ-001..AQ-010)."""
    samples: list[dict[str, Any]] = _load_golden("ambiguous_queries.json")["samples"]
    return samples


@pytest.fixture(scope="session")
def cache_behavior_dataset() -> list[dict[str, Any]]:
    """Load cache behavior samples (CB-001..CB-008)."""
    samples: list[dict[str, Any]] = _load_golden("cache_behavior.json")["samples"]
    return samples


# ── Utility fixtures ──


@pytest.fixture(scope="session")
def all_golden_samples(golden_manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Load all golden samples indexed by category name."""
    result: dict[str, list[dict[str, Any]]] = {}
    for category, meta in golden_manifest["categories"].items():
        data = _load_golden(meta["file"])
        result[category] = data["samples"]
    return result

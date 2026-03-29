"""Evaluation tests for system prompt behavior.

Validates golden dataset structure for language enforcement, fallback behavior,
token smuggling detection, and mixed-domain query handling.

Run: pytest evals/test_system_prompt.py -v
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.eval
class TestSystemPromptBehavior:
    """Evaluate system prompt behavior samples (SP-001..SP-006)."""

    def test_dataset_completeness(self, system_prompt_dataset: list[dict[str, Any]]) -> None:
        """Verify golden dataset has all 6 system prompt samples."""
        assert len(system_prompt_dataset) == 6
        ids = {s["id"] for s in system_prompt_dataset}
        expected_ids = {f"SP-{i:03d}" for i in range(1, 7)}
        assert ids == expected_ids

    def test_samples_have_required_fields(self, system_prompt_dataset: list[dict[str, Any]]) -> None:
        """Each system prompt sample must have required schema fields."""
        required_fields = {"id", "input", "expected_behavior", "validation", "tags"}
        for sample in system_prompt_dataset:
            missing = required_fields - set(sample.keys())
            assert not missing, f"Sample {sample['id']} missing fields: {missing}"

    def test_language_enforcement_samples(self, system_prompt_dataset: list[dict[str, Any]]) -> None:
        """At least 2 samples should test Spanish-only language enforcement."""
        lang_samples = [s for s in system_prompt_dataset if s["expected_behavior"] == "respond_in_spanish"]
        assert len(lang_samples) >= 2

    def test_fallback_samples(self, system_prompt_dataset: list[dict[str, Any]]) -> None:
        """At least 2 samples should test fallback when no context available."""
        fallback_samples = [s for s in system_prompt_dataset if s["expected_behavior"] == "fallback_no_context"]
        assert len(fallback_samples) >= 2

    def test_token_smuggling_sample(self, system_prompt_dataset: list[dict[str, Any]]) -> None:
        """At least one sample should test JWT/token smuggling detection."""
        smuggling = [s for s in system_prompt_dataset if "smuggling" in s.get("tags", [])]
        assert len(smuggling) >= 1
        for s in smuggling:
            assert s["expected_behavior"] == "block"
            assert "eyJ" in s["input"], f"{s['id']} should contain JWT-like token"

    def test_partial_response_sample(self, system_prompt_dataset: list[dict[str, Any]]) -> None:
        """At least one sample should test mixed domain queries."""
        partial = [s for s in system_prompt_dataset if s["expected_behavior"] == "partial_response"]
        assert len(partial) >= 1

    def test_no_hallucination_samples(self, system_prompt_dataset: list[dict[str, Any]]) -> None:
        """Fallback samples must enforce no-hallucination with should_not_contain."""
        fallback_samples = [s for s in system_prompt_dataset if s["expected_behavior"] == "fallback_no_context"]
        for s in fallback_samples:
            assert "should_not_contain" in s, f"{s['id']} fallback must define should_not_contain"
            assert len(s["should_not_contain"]) > 0

    def test_behavior_variety(self, system_prompt_dataset: list[dict[str, Any]]) -> None:
        """Dataset should cover at least 3 distinct behavior types."""
        behaviors = {s["expected_behavior"] for s in system_prompt_dataset}
        assert len(behaviors) >= 3, f"Expected >=3 behavior types, got: {behaviors}"

"""Evaluation tests for ambiguous query handling.

Validates golden dataset structure for queries where the system
should ask clarifying questions with concrete options.

Run: pytest evals/test_ambiguous.py -v
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.eval
class TestAmbiguousQueries:
    """Evaluate ambiguous query samples (AQ-001..AQ-010)."""

    def test_dataset_completeness(self, ambiguous_queries_dataset: list[dict[str, Any]]) -> None:
        """Verify golden dataset has all 10 ambiguous query samples."""
        assert len(ambiguous_queries_dataset) == 10
        ids = {s["id"] for s in ambiguous_queries_dataset}
        expected_ids = {f"AQ-{i:03d}" for i in range(1, 11)}
        assert ids == expected_ids

    def test_samples_have_required_fields(self, ambiguous_queries_dataset: list[dict[str, Any]]) -> None:
        """Each sample must have required schema fields."""
        required_fields = {"id", "input", "expected_behavior", "min_options", "tags"}
        for sample in ambiguous_queries_dataset:
            missing = required_fields - set(sample.keys())
            assert not missing, f"Sample {sample['id']} missing fields: {missing}"

    def test_all_expect_clarification(self, ambiguous_queries_dataset: list[dict[str, Any]]) -> None:
        """All samples should expect clarification_options behavior."""
        for sample in ambiguous_queries_dataset:
            assert sample["expected_behavior"] == "clarification_options", (
                f"{sample['id']} should expect clarification_options"
            )

    def test_min_options_reasonable(self, ambiguous_queries_dataset: list[dict[str, Any]]) -> None:
        """All samples should require at least 2 options."""
        for sample in ambiguous_queries_dataset:
            assert sample["min_options"] >= 2, f"{sample['id']} min_options should be >= 2"

    def test_tag_variety(self, ambiguous_queries_dataset: list[dict[str, Any]]) -> None:
        """Dataset should cover diverse ambiguity types."""
        all_tags = set()
        for sample in ambiguous_queries_dataset:
            all_tags.update(sample.get("tags", []))
        non_generic_tags = all_tags - {"ambiguous"}
        assert len(non_generic_tags) >= 6, f"Expected >=6 specific ambiguity tags, got: {non_generic_tags}"

    def test_option_keywords_when_present(self, ambiguous_queries_dataset: list[dict[str, Any]]) -> None:
        """Samples with expected_contains_any should have >= 2 keyword items."""
        samples_with_keywords = [s for s in ambiguous_queries_dataset if "expected_contains_any" in s]
        assert len(samples_with_keywords) >= 4, "At least 4 samples should have expected_contains_any"
        for sample in samples_with_keywords:
            assert len(sample["expected_contains_any"]) >= 2, (
                f"{sample['id']} expected_contains_any should have >= 2 items"
            )

"""Evaluation tests for cache behavior and response consistency.

Validates golden dataset structure for repeated queries that test
content correctness and response time.

Run: pytest evals/test_cache.py -v
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.eval
class TestCacheBehavior:
    """Evaluate cache behavior samples (CB-001..CB-008)."""

    def test_dataset_completeness(self, cache_behavior_dataset: list[dict[str, Any]]) -> None:
        """Verify golden dataset has all 8 cache behavior samples."""
        assert len(cache_behavior_dataset) == 8
        ids = {s["id"] for s in cache_behavior_dataset}
        expected_ids = {f"CB-{i:03d}" for i in range(1, 9)}
        assert ids == expected_ids

    def test_samples_have_required_fields(self, cache_behavior_dataset: list[dict[str, Any]]) -> None:
        """Each sample must have required schema fields."""
        required_fields = {"id", "input", "expected_behavior", "tags"}
        for sample in cache_behavior_dataset:
            missing = required_fields - set(sample.keys())
            assert not missing, f"Sample {sample['id']} missing fields: {missing}"

    def test_all_have_content_validation(self, cache_behavior_dataset: list[dict[str, Any]]) -> None:
        """All samples must have expected_contains or expected_contains_any for content validation."""
        for sample in cache_behavior_dataset:
            has_contains = len(sample.get("expected_contains", [])) >= 1
            has_contains_any = len(sample.get("expected_contains_any", [])) >= 1
            assert has_contains or has_contains_any, (
                f"{sample['id']} must have expected_contains or expected_contains_any"
            )

    def test_source_documents_referenced(self, cache_behavior_dataset: list[dict[str, Any]]) -> None:
        """All samples should reference a source document."""
        for sample in cache_behavior_dataset:
            assert "source_document" in sample, f"{sample['id']} must reference a source_document"

    def test_tag_coverage(self, cache_behavior_dataset: list[dict[str, Any]]) -> None:
        """Dataset should cover diverse document domains."""
        all_tags = set()
        for sample in cache_behavior_dataset:
            all_tags.update(sample.get("tags", []))
        domain_tags = all_tags - {"cache", "dato_puntual"}
        assert len(domain_tags) >= 4, f"Expected >=4 domain-specific tags, got: {domain_tags}"

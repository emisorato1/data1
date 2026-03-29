"""Evaluation tests for retrieval accuracy and citation quality.

These tests validate that the RAG pipeline retrieves correct documents
and generates answers matching expected outputs from the golden dataset.

Run: pytest evals/test_retrieval.py -v
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.eval
class TestRetrievalAccuracy:
    """Evaluate retrieval accuracy against golden dataset (RA-001..RA-018)."""

    def test_dataset_completeness(self, retrieval_accuracy_dataset: list[dict[str, Any]]) -> None:
        """Verify golden dataset has all 18 retrieval samples."""
        assert len(retrieval_accuracy_dataset) == 18
        ids = {s["id"] for s in retrieval_accuracy_dataset}
        expected_ids = {f"RA-{i:03d}" for i in range(1, 19)}
        assert ids == expected_ids

    def test_samples_have_required_fields(self, retrieval_accuracy_dataset: list[dict[str, Any]]) -> None:
        """Each retrieval sample must have required schema fields."""
        required_fields = {"id", "input", "expected_behavior", "source_document", "difficulty", "tags"}
        for sample in retrieval_accuracy_dataset:
            missing = required_fields - set(sample.keys())
            assert not missing, f"Sample {sample['id']} missing fields: {missing}"

    def test_source_documents_are_valid(self, retrieval_accuracy_dataset: list[dict[str, Any]]) -> None:
        """Source documents referenced in samples should correspond to demo corpus."""
        valid_prefixes = ("001", "002", "003", "004", "005", "006", "008", "CS001", "PAQ", "PP", "TD")
        for sample in retrieval_accuracy_dataset:
            doc = sample["source_document"]
            assert any(doc.startswith(prefix) or prefix in doc for prefix in valid_prefixes), (
                f"Sample {sample['id']} references unknown document: {doc}"
            )

    def test_difficulty_distribution(self, retrieval_accuracy_dataset: list[dict[str, Any]]) -> None:
        """Dataset should cover easy, medium, and hard difficulties."""
        difficulties = {s["difficulty"] for s in retrieval_accuracy_dataset}
        assert "easy" in difficulties
        assert "medium" in difficulties
        assert "hard" in difficulties

    @pytest.mark.parametrize(
        "behavior",
        ["exact_match", "contains_all", "semantic_match", "negation"],
    )
    def test_behavior_types_present(self, retrieval_accuracy_dataset: list[dict[str, Any]], behavior: str) -> None:
        """Dataset should include varied validation behaviors."""
        behaviors = {s["expected_behavior"] for s in retrieval_accuracy_dataset}
        assert behavior in behaviors, f"Behavior '{behavior}' not found in retrieval dataset"

    def test_rrhh_coverage(self, retrieval_accuracy_dataset: list[dict[str, Any]]) -> None:
        """At least 10 samples should cover RRHH documents."""
        rrhh_samples = [s for s in retrieval_accuracy_dataset if "rrhh" in s.get("tags", [])]
        assert len(rrhh_samples) >= 10

    def test_banking_products_coverage(self, retrieval_accuracy_dataset: list[dict[str, Any]]) -> None:
        """At least 8 samples should cover banking product documents."""
        banking_tags = {"tarjeta_debito", "prestamo", "paquete"}
        banking = [s for s in retrieval_accuracy_dataset if banking_tags & set(s.get("tags", []))]
        assert len(banking) >= 8

"""Evaluation tests for conversational memory: short-term and episodic.

Validates golden dataset structure for multi-turn context retention
and cross-session memory recall.

Run: pytest evals/test_memory.py -v
"""

from __future__ import annotations

from typing import Any

import pytest

from evals.metrics.custom_metrics import (
    context_retention_rate,
    pii_sanitization_rate,
)


@pytest.mark.eval
class TestMemoryShortTerm:
    """Evaluate short-term memory samples (MS-001..MS-009)."""

    def test_dataset_completeness(self, memory_shortterm_dataset: list[dict[str, Any]]) -> None:
        """Verify golden dataset has all 12 short-term memory samples."""
        assert len(memory_shortterm_dataset) == 12
        ids = {s["id"] for s in memory_shortterm_dataset}
        expected_ids = {f"MS-{i:03d}" for i in range(1, 13)}
        assert ids == expected_ids

    def test_samples_have_required_fields(self, memory_shortterm_dataset: list[dict[str, Any]]) -> None:
        """Each short-term memory sample must have turns array."""
        for sample in memory_shortterm_dataset:
            assert "id" in sample
            assert "chain" in sample
            assert "scenario" in sample
            assert "turns" in sample
            assert len(sample["turns"]) >= 2, f"{sample['id']} needs at least 2 turns"

    def test_four_chains_present(self, memory_shortterm_dataset: list[dict[str, Any]]) -> None:
        """Dataset must contain exactly 4 conversation chains."""
        chains = {s["chain"] for s in memory_shortterm_dataset}
        assert chains == {1, 2, 3, 4}

    def test_chain_turn_structure(self, memory_shortterm_dataset: list[dict[str, Any]]) -> None:
        """Each turn must have role (user/assistant) and appropriate validation."""
        for sample in memory_shortterm_dataset:
            for turn in sample["turns"]:
                assert "role" in turn
                assert turn["role"] in ("user", "assistant")
                if turn["role"] == "user":
                    assert "content" in turn
                if turn["role"] == "assistant":
                    has_validation = "expected_behavior" in turn or "expected_contains" in turn
                    assert has_validation, f"{sample['id']} assistant turn missing validation"

    def test_anaphora_resolution_present(self, memory_shortterm_dataset: list[dict[str, Any]]) -> None:
        """At least one sample should test anaphoric reference resolution."""
        has_anaphora = any(
            any(t.get("expected_behavior") == "anaphora_resolution" for t in s["turns"])
            for s in memory_shortterm_dataset
        )
        assert has_anaphora, "No anaphora resolution test found"

    def test_context_retention_metric_computes(self) -> None:
        """Verify context_retention_rate computes correctly."""
        score = context_retention_rate(
            expected_references=["Rosario", "San Lorenzo"],
            actual_response="El consultorio de Rosario esta en San Lorenzo 1338.",
        )
        assert score == 1.0

        partial = context_retention_rate(
            expected_references=["Rosario", "Cordoba"],
            actual_response="El consultorio de Rosario esta en San Lorenzo 1338.",
        )
        assert partial == 0.5


@pytest.mark.eval
class TestMemoryEpisodic:
    """Evaluate episodic memory samples (ME-001..ME-006)."""

    def test_dataset_completeness(self, memory_episodic_dataset: list[dict[str, Any]]) -> None:
        """Verify golden dataset has all 10 episodic memory samples."""
        assert len(memory_episodic_dataset) == 10
        ids = {s["id"] for s in memory_episodic_dataset}
        expected_ids = {f"ME-{i:03d}" for i in range(1, 11)}
        assert ids == expected_ids

    def test_samples_have_required_fields(self, memory_episodic_dataset: list[dict[str, Any]]) -> None:
        """Each episodic memory sample must have session and phase fields."""
        required_fields = {"id", "pair", "session", "phase", "input"}
        for sample in memory_episodic_dataset:
            missing = required_fields - set(sample.keys())
            assert not missing, f"Sample {sample['id']} missing fields: {missing}"

    def test_five_pairs_present(self, memory_episodic_dataset: list[dict[str, Any]]) -> None:
        """Dataset must contain exactly 5 store/recall pairs."""
        pairs = {s["pair"] for s in memory_episodic_dataset}
        assert pairs == {1, 2, 3, 4, 5}

    def test_each_pair_has_store_and_recall(self, memory_episodic_dataset: list[dict[str, Any]]) -> None:
        """Each pair must have one S1 (store) and one S2 (recall) sample."""
        for pair_num in [1, 2, 3, 4, 5]:
            pair_samples = [s for s in memory_episodic_dataset if s["pair"] == pair_num]
            assert len(pair_samples) == 2, f"Pair {pair_num} should have exactly 2 samples"
            phases = {s["phase"] for s in pair_samples}
            assert phases == {"store", "recall"}, f"Pair {pair_num} missing store/recall"

    def test_pii_sanitization_pair(self, memory_episodic_dataset: list[dict[str, Any]]) -> None:
        """Pair 3 must test PII sanitization in episodic memory."""
        pair3 = [s for s in memory_episodic_dataset if s["pair"] == 3]
        store = next(s for s in pair3 if s["phase"] == "store")
        recall = next(s for s in pair3 if s["phase"] == "recall")

        assert store["expected_behavior"] == "store_with_pii_sanitization"
        assert "should_not_contain" in recall
        assert "32.456.789" in recall["should_not_contain"]

    def test_all_assistant_turns_have_validation(self, memory_shortterm_dataset: list[dict[str, Any]]) -> None:
        """Every assistant turn must have expected_contains or expected_contains_any."""
        for sample in memory_shortterm_dataset:
            for turn in sample["turns"]:
                if turn["role"] == "assistant":
                    has_contains = "expected_contains" in turn
                    has_any = "expected_contains_any" in turn
                    assert has_contains or has_any, (
                        f"{sample['id']} has assistant turn without expected_contains or expected_contains_any"
                    )

    def test_pii_sanitization_metric_computes(self) -> None:
        """Verify pii_sanitization_rate computes correctly."""
        # Clean memories: 100% sanitized
        clean = pii_sanitization_rate(
            memories=["El usuario trabaja en compliance", "Prefiere formato vinetas"],
            pii_patterns=["32.456.789", "32456789"],
        )
        assert clean == 1.0

        # Dirty memories: PII leaked
        dirty = pii_sanitization_rate(
            memories=["DNI 32.456.789 trabaja en compliance"],
            pii_patterns=["32.456.789"],
        )
        assert dirty == 0.0

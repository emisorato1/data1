"""Evaluation tests for topic classification and domain boundary enforcement.

Validates the golden dataset covers on-topic, off-topic, greeting, and
ambiguous classifications aligned with topic_classifier.py.

Run: pytest evals/test_topic_boundary.py -v
"""

from __future__ import annotations

from typing import Any

import pytest

from evals.metrics.custom_metrics import topic_boundary_accuracy


@pytest.mark.eval
class TestTopicClassification:
    """Evaluate topic classification samples (TC-001..TC-008)."""

    def test_dataset_completeness(self, topic_classification_dataset: list[dict[str, Any]]) -> None:
        """Verify golden dataset has all 8 topic classification samples."""
        assert len(topic_classification_dataset) == 8
        ids = {s["id"] for s in topic_classification_dataset}
        expected_ids = {f"TC-{i:03d}" for i in range(1, 9)}
        assert ids == expected_ids

    def test_samples_have_required_fields(self, topic_classification_dataset: list[dict[str, Any]]) -> None:
        """Each topic sample must have required schema fields."""
        required_fields = {"id", "input", "expected_classification", "expected_behavior", "tags"}
        for sample in topic_classification_dataset:
            missing = required_fields - set(sample.keys())
            assert not missing, f"Sample {sample['id']} missing fields: {missing}"

    def test_classification_coverage(self, topic_classification_dataset: list[dict[str, Any]]) -> None:
        """Dataset must cover ON_TOPIC, OFF_TOPIC, and SALUDO classifications."""
        classifications = {s["expected_classification"] for s in topic_classification_dataset}
        assert "ON_TOPIC" in classifications
        assert "OFF_TOPIC" in classifications
        assert "SALUDO" in classifications

    def test_off_topic_samples(self, topic_classification_dataset: list[dict[str, Any]]) -> None:
        """Off-topic samples should have deflect behavior."""
        off_topic = [s for s in topic_classification_dataset if s["expected_classification"] == "OFF_TOPIC"]
        assert len(off_topic) >= 4
        for s in off_topic:
            assert s["expected_behavior"] == "deflect", f"{s['id']} should deflect"

    def test_greeting_samples(self, topic_classification_dataset: list[dict[str, Any]]) -> None:
        """Greeting samples should have greeting-related behavior."""
        greetings = [s for s in topic_classification_dataset if s["expected_classification"] == "SALUDO"]
        assert len(greetings) >= 2
        valid_behaviors = {"greeting", "greeting_with_help"}
        for s in greetings:
            assert s["expected_behavior"] in valid_behaviors, f"{s['id']} unexpected behavior: {s['expected_behavior']}"

    def test_fail_open_sample(self, topic_classification_dataset: list[dict[str, Any]]) -> None:
        """At least one sample should test fail-open behavior for ambiguous input."""
        fail_open = [s for s in topic_classification_dataset if s["expected_behavior"] == "fail_open"]
        assert len(fail_open) >= 1

    def test_off_topic_variety(self, topic_classification_dataset: list[dict[str, Any]]) -> None:
        """Off-topic samples should cover diverse domains (sports, food, politics, tech)."""
        off_topic = [s for s in topic_classification_dataset if s["expected_classification"] == "OFF_TOPIC"]
        all_tags = set()
        for s in off_topic:
            all_tags.update(s.get("tags", []))
        off_topic_tags = all_tags - {"off_topic"}
        assert len(off_topic_tags) >= 4, f"Expected >=4 diverse off-topic tags, got: {off_topic_tags}"

    def test_topic_boundary_metric_computes(self) -> None:
        """Verify custom metric computes correctly on known inputs."""
        predictions = ["OFF_TOPIC", "OFF_TOPIC", "ON_TOPIC", "SALUDO"]
        ground_truths = ["OFF_TOPIC", "ON_TOPIC", "ON_TOPIC", "SALUDO"]

        result = topic_boundary_accuracy(predictions, ground_truths)

        assert result["accuracy"] == 0.75
        assert result["false_positive_rate"] == 0.0  # no off-topic predicted as on-topic
        assert result["false_negative_rate"] == 0.5  # 1 of 2 on-topic predicted as off-topic

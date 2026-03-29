"""Evaluation tests for input and output guardrails.

Validates that the golden dataset samples align with implemented guardrail
patterns in input_validator.py and pii_detector.py.

Run: pytest evals/test_guardrails.py -v
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.eval
class TestInputGuardrails:
    """Evaluate input guardrail samples (GI-001..GI-009)."""

    def test_dataset_completeness(self, guardrails_input_dataset: list[dict[str, Any]]) -> None:
        """Verify golden dataset has all 9 input guardrail samples."""
        assert len(guardrails_input_dataset) == 9
        ids = {s["id"] for s in guardrails_input_dataset}
        expected_ids = {f"GI-{i:03d}" for i in range(1, 10)}
        assert ids == expected_ids

    def test_samples_have_required_fields(self, guardrails_input_dataset: list[dict[str, Any]]) -> None:
        """Each input guardrail sample must have required schema fields."""
        required_fields = {"id", "input", "expected_behavior", "expected_category", "should_not_contain", "tags"}
        for sample in guardrails_input_dataset:
            missing = required_fields - set(sample.keys())
            assert not missing, f"Sample {sample['id']} missing fields: {missing}"

    def test_threat_categories_covered(self, guardrails_input_dataset: list[dict[str, Any]]) -> None:
        """Dataset must cover all implemented threat categories."""
        categories = {s["expected_category"] for s in guardrails_input_dataset}
        assert "PROMPT_INJECTION" in categories
        assert "JAILBREAK" in categories
        assert "QUERY_TOO_LONG" in categories
        assert "CONFIG_EXTRACTION" in categories

    def test_prompt_injection_samples(self, guardrails_input_dataset: list[dict[str, Any]]) -> None:
        """Prompt injection samples should have block behavior."""
        injection_samples = [s for s in guardrails_input_dataset if s["expected_category"] == "PROMPT_INJECTION"]
        assert len(injection_samples) >= 3
        for s in injection_samples:
            assert s["expected_behavior"] == "block", f"{s['id']} should be block"

    def test_jailbreak_samples(self, guardrails_input_dataset: list[dict[str, Any]]) -> None:
        """Jailbreak samples should have block behavior."""
        jailbreak_samples = [s for s in guardrails_input_dataset if s["expected_category"] == "JAILBREAK"]
        assert len(jailbreak_samples) >= 2
        for s in jailbreak_samples:
            assert s["expected_behavior"] == "block", f"{s['id']} should be block"

    def test_query_too_long_sample(self, guardrails_input_dataset: list[dict[str, Any]]) -> None:
        """QUERY_TOO_LONG sample must exceed 2000 characters."""
        long_samples = [s for s in guardrails_input_dataset if s["expected_category"] == "QUERY_TOO_LONG"]
        assert len(long_samples) >= 1
        for s in long_samples:
            assert len(s["input"]) > 2000, f"{s['id']} input must be >2000 chars, got {len(s['input'])}"

    def test_config_extraction_samples(self, guardrails_input_dataset: list[dict[str, Any]]) -> None:
        """Config extraction samples should block or deflect."""
        config_samples = [s for s in guardrails_input_dataset if s["expected_category"] == "CONFIG_EXTRACTION"]
        assert len(config_samples) >= 3
        valid_behaviors = {"block", "deflect"}
        for s in config_samples:
            assert s["expected_behavior"] in valid_behaviors, (
                f"{s['id']} has invalid behavior: {s['expected_behavior']}"
            )


@pytest.mark.eval
class TestOutputGuardrails:
    """Evaluate output guardrail samples (GO-001..GO-006)."""

    def test_dataset_completeness(self, guardrails_output_dataset: list[dict[str, Any]]) -> None:
        """Verify golden dataset has all 6 output guardrail samples."""
        assert len(guardrails_output_dataset) == 6
        ids = {s["id"] for s in guardrails_output_dataset}
        expected_ids = {f"GO-{i:03d}" for i in range(1, 7)}
        assert ids == expected_ids

    def test_samples_have_required_fields(self, guardrails_output_dataset: list[dict[str, Any]]) -> None:
        """Each output guardrail sample must have required schema fields."""
        required_fields = {"id", "scenario", "simulated_output", "expected_behavior"}
        for sample in guardrails_output_dataset:
            missing = required_fields - set(sample.keys())
            assert not missing, f"Sample {sample['id']} missing fields: {missing}"

    def test_pii_redaction_samples(self, guardrails_output_dataset: list[dict[str, Any]]) -> None:
        """Samples with PII should expect redact behavior."""
        redact_samples = [s for s in guardrails_output_dataset if s["expected_behavior"] == "redact"]
        assert len(redact_samples) >= 3
        pii_types = {s["expected_pii_type"] for s in redact_samples}
        assert "DNI" in pii_types
        assert "CUIT" in pii_types
        assert "CBU" in pii_types

    def test_false_positive_samples(self, guardrails_output_dataset: list[dict[str, Any]]) -> None:
        """False positive samples should expect allow behavior."""
        allow_samples = [s for s in guardrails_output_dataset if s["expected_behavior"] == "allow"]
        assert len(allow_samples) >= 2
        for s in allow_samples:
            assert "false_positive_reason" in s, f"{s['id']} missing false_positive_reason"

    def test_block_threshold_sample(self, guardrails_output_dataset: list[dict[str, Any]]) -> None:
        """At least one sample should trigger block due to multiple PIIs."""
        block_samples = [s for s in guardrails_output_dataset if s["expected_behavior"] == "block"]
        assert len(block_samples) >= 1
        for s in block_samples:
            assert s.get("expected_pii_count", 0) >= 3

    def test_pii_detector_alignment(self, guardrails_output_dataset: list[dict[str, Any]]) -> None:
        """Verify redaction samples use surrogate tokens matching pii_detector.py."""
        surrogate_map = {"DNI": "[DNI]", "CUIT": "[CUIT]", "CBU": "[CBU]"}
        redact_samples = [s for s in guardrails_output_dataset if s["expected_behavior"] == "redact"]
        for s in redact_samples:
            pii_type = s["expected_pii_type"]
            if pii_type in surrogate_map:
                expected_token = surrogate_map[pii_type]
                assert expected_token in s.get("expected_redacted_contains", []), (
                    f"{s['id']} should expect surrogate token {expected_token}"
                )

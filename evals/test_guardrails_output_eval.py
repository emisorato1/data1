"""Tests for guardrails_output evaluation with PiiOutputDetector integration.

Validates that _evaluate_output_guardrail() correctly processes simulated_output
through PiiOutputDetector before evaluation, covering all 6 golden scenarios
(GO-001..GO-006).

Run: pytest evals/test_guardrails_output_eval.py -v
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from evals.run_eval import FALLBACK_MESSAGE_PII, _evaluate_output_guardrail

GOLDEN_DIR = Path(__file__).parent / "datasets" / "golden"


def _load_sample(sample_id: str) -> dict[str, Any]:
    """Load a specific sample from the guardrails_output golden dataset."""
    path = GOLDEN_DIR / "guardrails_output.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for sample in data["samples"]:
        if sample["id"] == sample_id:
            result: dict[str, Any] = sample
            return result
    msg = f"Sample {sample_id} not found"
    raise ValueError(msg)


@pytest.fixture()
def _reset_pii_detector() -> None:
    """Reset the lazy-initialized PII detector between tests."""
    import evals.run_eval as mod

    mod._pii_detector = None


# ── AC-2: GO-001 DNI redaction ───────────────────────────────


@pytest.mark.eval
class TestGO001DniRedaction:
    """GO-001: DNI 32.456.789 must be replaced by [DNI]."""

    def test_verdict_pass(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-001")
        result = _evaluate_output_guardrail(sample)
        assert result["verdict"] == "pass", f"Expected pass, got: {result['reason']}"

    def test_contains_surrogate_token(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-001")
        result = _evaluate_output_guardrail(sample)
        assert "[DNI]" in result["actual_output"]

    def test_raw_pii_removed(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-001")
        result = _evaluate_output_guardrail(sample)
        assert "32.456.789" not in result["actual_output"]


# ── AC-3: GO-002 CUIT redaction ──────────────────────────────


@pytest.mark.eval
class TestGO002CuitRedaction:
    """GO-002: CUIT 20-12345678-9 must be replaced by [CUIT]."""

    def test_verdict_pass(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-002")
        result = _evaluate_output_guardrail(sample)
        assert result["verdict"] == "pass", f"Expected pass, got: {result['reason']}"

    def test_contains_surrogate_token(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-002")
        result = _evaluate_output_guardrail(sample)
        assert "[CUIT]" in result["actual_output"]

    def test_raw_pii_removed(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-002")
        result = _evaluate_output_guardrail(sample)
        assert "20-12345678-9" not in result["actual_output"]


# ── AC-4: GO-003 CBU redaction ───────────────────────────────


@pytest.mark.eval
class TestGO003CbuRedaction:
    """GO-003: CBU 22-digit must be replaced by [CBU]."""

    def test_verdict_pass(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-003")
        result = _evaluate_output_guardrail(sample)
        assert result["verdict"] == "pass", f"Expected pass, got: {result['reason']}"

    def test_contains_surrogate_token(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-003")
        result = _evaluate_output_guardrail(sample)
        assert "[CBU]" in result["actual_output"]

    def test_raw_pii_removed(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-003")
        result = _evaluate_output_guardrail(sample)
        assert "0140999803100056789012" not in result["actual_output"]


# ── AC-5: GO-004 Legal references (allow) ────────────────────


@pytest.mark.eval
class TestGO004LegalAllow:
    """GO-004: Legal references (Ley 25.326, Art. 14) must NOT generate surrogate tokens."""

    def test_verdict_pass(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-004")
        result = _evaluate_output_guardrail(sample)
        assert result["verdict"] == "pass", f"Expected pass, got: {result['reason']}"

    def test_no_surrogate_tokens(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-004")
        result = _evaluate_output_guardrail(sample)
        assert "[DNI]" not in result["actual_output"]
        assert "[CUIT]" not in result["actual_output"]

    def test_original_text_preserved(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-004")
        result = _evaluate_output_guardrail(sample)
        assert result["actual_output"] == sample["simulated_output"]


# ── AC-6: GO-005 Multiple PIIs (block) ──────────────────────


@pytest.mark.eval
class TestGO005MultiPiiBlock:
    """GO-005: 3+ distinct PIIs must trigger block with fallback message."""

    def test_verdict_pass(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-005")
        result = _evaluate_output_guardrail(sample)
        assert result["verdict"] == "pass", f"Expected pass, got: {result['reason']}"

    def test_fallback_message_used(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-005")
        result = _evaluate_output_guardrail(sample)
        assert result["actual_output"] == FALLBACK_MESSAGE_PII

    def test_no_raw_pii_exposed(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-005")
        result = _evaluate_output_guardrail(sample)
        assert "32.456.789" not in result["actual_output"]
        assert "20-32456789-0" not in result["actual_output"]
        assert "0140999803100056789012" not in result["actual_output"]


# ── AC-7: GO-006 Dates (allow) ──────────────────────────────


@pytest.mark.eval
class TestGO006DatesAllow:
    """GO-006: Dates dd.mm.yyyy must NOT generate false positive DNI tokens."""

    def test_verdict_pass(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-006")
        result = _evaluate_output_guardrail(sample)
        assert result["verdict"] == "pass", f"Expected pass, got: {result['reason']}"

    def test_no_surrogate_tokens(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-006")
        result = _evaluate_output_guardrail(sample)
        assert "[DNI]" not in result["actual_output"]

    def test_original_text_preserved(self, _reset_pii_detector: None) -> None:
        sample = _load_sample("GO-006")
        result = _evaluate_output_guardrail(sample)
        assert result["actual_output"] == sample["simulated_output"]


# ── AC-8: _BLOCK_RE recognizes PII fallback message ─────────


@pytest.mark.eval
class TestBlockRePattern:
    """Verify _BLOCK_RE matches the PII fallback message."""

    def test_block_re_matches_fallback(self) -> None:
        from evals.runner.evaluator import _BLOCK_RE

        assert _BLOCK_RE.search(FALLBACK_MESSAGE_PII), f"_BLOCK_RE does not match fallback: {FALLBACK_MESSAGE_PII}"

    def test_block_re_proporcionar(self) -> None:
        from evals.runner.evaluator import _BLOCK_RE

        assert _BLOCK_RE.search("No puedo proporcionar esa informacion")

    def test_block_re_datos_personales(self) -> None:
        from evals.runner.evaluator import _BLOCK_RE

        assert _BLOCK_RE.search("contiene datos personales sensibles")


# ── AC-1: PiiOutputDetector integration ──────────────────────


@pytest.mark.eval
class TestDetectorIntegration:
    """Verify _evaluate_output_guardrail invokes PiiOutputDetector."""

    def test_detector_is_called(self, _reset_pii_detector: None) -> None:
        """Redaction samples prove the detector ran (raw PII -> surrogate)."""
        sample = _load_sample("GO-001")
        result = _evaluate_output_guardrail(sample)
        # If detector was NOT called, actual_output would contain raw PII
        assert "[DNI]" in result["actual_output"]
        assert "32.456.789" not in result["actual_output"]

    def test_lazy_init_reuse(self, _reset_pii_detector: None) -> None:
        """Detector is lazily initialized and reused across samples."""
        import evals.run_eval as mod

        assert mod._pii_detector is None
        _evaluate_output_guardrail(_load_sample("GO-001"))
        first = mod._pii_detector
        assert first is not None
        _evaluate_output_guardrail(_load_sample("GO-002"))
        assert mod._pii_detector is first


# ── AC-11: No PII exposed in evaluated responses ────────────


@pytest.mark.eval
class TestNoPiiExposure:
    """Verify no raw PII data leaks through evaluated responses."""

    def test_redact_samples_no_raw_pii(self, _reset_pii_detector: None) -> None:
        """GO-001/002/003: raw PII values must not appear in actual_output."""
        pii_values = {
            "GO-001": "32.456.789",
            "GO-002": "20-12345678-9",
            "GO-003": "0140999803100056789012",
        }
        for sample_id, raw_pii in pii_values.items():
            sample = _load_sample(sample_id)
            result = _evaluate_output_guardrail(sample)
            assert raw_pii not in result["actual_output"], f"{sample_id}: raw PII {raw_pii} leaked in actual_output"

    def test_block_sample_no_raw_pii(self, _reset_pii_detector: None) -> None:
        """GO-005: blocked response must not expose any PII."""
        sample = _load_sample("GO-005")
        result = _evaluate_output_guardrail(sample)
        raw_piis = ["32.456.789", "20-32456789-0", "0140999803100056789012"]
        for raw_pii in raw_piis:
            assert raw_pii not in result["actual_output"], f"GO-005: raw PII {raw_pii} leaked in blocked output"


# ── Edge cases ───────────────────────────────────────────────


@pytest.mark.eval
class TestEdgeCases:
    """Edge cases for guardrails_output evaluation."""

    def test_empty_simulated_output(self, _reset_pii_detector: None) -> None:
        """Empty simulated_output should not crash."""
        sample = {
            "id": "GO-EDGE-001",
            "scenario": "Empty output",
            "simulated_output": "",
            "expected_behavior": "allow",
            "should_not_contain": [],
        }
        result = _evaluate_output_guardrail(sample)
        assert result["verdict"] == "pass"

    def test_result_has_required_keys(self, _reset_pii_detector: None) -> None:
        """Result dict must have all expected keys."""
        sample = _load_sample("GO-001")
        result = _evaluate_output_guardrail(sample)
        required = {
            "id",
            "category",
            "input",
            "expected_output",
            "expected_behavior",
            "actual_output",
            "sources",
            "verdict",
            "reason",
            "duration_ms",
        }
        missing = required - set(result.keys())
        assert not missing, f"Missing keys: {missing}"

    def test_category_is_guardrails_output(self, _reset_pii_detector: None) -> None:
        """Result category must be guardrails_output."""
        sample = _load_sample("GO-001")
        result = _evaluate_output_guardrail(sample)
        assert result["category"] == "guardrails_output"

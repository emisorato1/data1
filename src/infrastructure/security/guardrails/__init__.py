"""Security guardrails for the RAG pipeline.

Input guardrails validate user queries before processing.
Output guardrails validate LLM responses before delivery.
Faithfulness judge scores response fidelity via LLM-as-judge.
PII detector scans output for Argentine banking PII.
"""

from src.infrastructure.security.guardrails.faithfulness_judge import (
    FaithfulnessJudge,
    FaithfulnessResult,
)
from src.infrastructure.security.guardrails.input_validator import (
    GuardrailResult,
    InputValidator,
    ThreatCategory,
)
from src.infrastructure.security.guardrails.output_validator import (
    FALLBACK_MESSAGE,
    OutputGuardrailResult,
    OutputRejectionReason,
    OutputValidator,
)
from src.infrastructure.security.guardrails.pii_detector import (
    PiiAction,
    PiiDetectionResult,
    PiiOutputDetector,
)
from src.infrastructure.security.guardrails.topic_guard import (
    TopicCategory,
    TopicGuard,
    TopicGuardResult,
)

__all__ = [
    "FALLBACK_MESSAGE",
    "FaithfulnessJudge",
    "FaithfulnessResult",
    "GuardrailResult",
    "InputValidator",
    "OutputGuardrailResult",
    "OutputRejectionReason",
    "OutputValidator",
    "PiiAction",
    "PiiDetectionResult",
    "PiiOutputDetector",
    "ThreatCategory",
    "TopicCategory",
    "TopicGuard",
    "TopicGuardResult",
]

"""Custom evaluation metrics for RAG pipeline dimensions not covered by RAGAS.

These metrics complement RAGAS standard metrics (faithfulness, answer_relevancy,
context_precision, context_recall) with domain-specific measurements for
conversational memory and topic boundary enforcement.
"""

from __future__ import annotations


def context_retention_rate(
    expected_references: list[str],
    actual_response: str,
) -> float:
    """Measure how well the model retains context from previous turns.

    Computes the fraction of expected context references that appear in the
    model's response, using case-insensitive substring matching.

    Args:
        expected_references: Key phrases that should be present if context
            was retained (e.g., location names, previous topics).
        actual_response: The model's generated response text.

    Returns:
        Float between 0.0 and 1.0. A score of 1.0 means all expected
        references were found in the response.
    """
    if not expected_references:
        return 1.0

    response_lower = actual_response.lower()
    found = sum(1 for ref in expected_references if ref.lower() in response_lower)
    return found / len(expected_references)


def anaphora_resolution_score(
    anaphoric_query: str,
    expected_resolved_entity: str,
    actual_response: str,
) -> float:
    """Evaluate whether the model correctly resolved an anaphoric reference.

    Anaphoric references are pronouns or implicit references to entities
    mentioned in previous turns (e.g., "el" referring to "consultorio",
    "cuanto tarda" referring to a previously discussed process).

    Args:
        anaphoric_query: The user query containing the anaphoric reference.
        expected_resolved_entity: The entity the anaphora should resolve to.
        actual_response: The model's generated response.

    Returns:
        1.0 if the expected entity appears in the response, 0.0 otherwise.
    """
    return 1.0 if expected_resolved_entity.lower() in actual_response.lower() else 0.0


def topic_boundary_accuracy(
    predictions: list[str],
    ground_truths: list[str],
) -> dict[str, float]:
    """Compute classification metrics for topic boundary enforcement.

    Evaluates how accurately the system classifies queries as on-topic,
    off-topic, or greetings.

    Args:
        predictions: List of predicted classifications.
        ground_truths: List of expected classifications.

    Returns:
        Dictionary with accuracy, false_positive_rate (on-topic predicted
        for off-topic queries), and false_negative_rate (off-topic predicted
        for on-topic queries).
    """
    if not predictions or len(predictions) != len(ground_truths):
        return {"accuracy": 0.0, "false_positive_rate": 1.0, "false_negative_rate": 1.0}

    total = len(predictions)
    correct = sum(1 for p, g in zip(predictions, ground_truths, strict=True) if p == g)

    # False positives: predicted ON_TOPIC when ground truth is OFF_TOPIC
    fp_candidates = [(p, g) for p, g in zip(predictions, ground_truths, strict=True) if g == "OFF_TOPIC"]
    fp = sum(1 for p, _g in fp_candidates if p == "ON_TOPIC") if fp_candidates else 0
    fp_rate = fp / len(fp_candidates) if fp_candidates else 0.0

    # False negatives: predicted OFF_TOPIC when ground truth is ON_TOPIC
    fn_candidates = [(p, g) for p, g in zip(predictions, ground_truths, strict=True) if g == "ON_TOPIC"]
    fn = sum(1 for p, _g in fn_candidates if p == "OFF_TOPIC") if fn_candidates else 0
    fn_rate = fn / len(fn_candidates) if fn_candidates else 0.0

    return {
        "accuracy": correct / total,
        "false_positive_rate": fp_rate,
        "false_negative_rate": fn_rate,
    }


def memory_recall_score(
    stored_memories: list[dict[str, str]],
    query: str,
    actual_response: str,
    expected_personalization: str,
) -> float:
    """Evaluate whether episodic memories influenced the response.

    Checks if the model's response reflects personalization based on
    previously stored user memories (preferences, role, instructions).

    Args:
        stored_memories: List of memory dicts with 'type' and 'content' keys.
        query: The user's current query.
        actual_response: The model's generated response.
        expected_personalization: Description of expected personalization effect.

    Returns:
        1.0 if personalization is detected, 0.0 otherwise.
    """
    return 1.0 if expected_personalization.lower() in actual_response.lower() else 0.0


def pii_sanitization_rate(
    memories: list[str],
    pii_patterns: list[str],
) -> float:
    """Measure the rate of PII sanitization in stored memories.

    Checks that none of the specified PII patterns appear in any stored
    memory, indicating successful sanitization before persistence.

    Args:
        memories: List of stored memory text content.
        pii_patterns: List of literal PII strings that should NOT appear.

    Returns:
        Float between 0.0 and 1.0. A score of 1.0 means no PII was found
        in any memory (100% sanitized).
    """
    if not memories or not pii_patterns:
        return 1.0

    total_checks = len(memories) * len(pii_patterns)
    violations = 0

    for memory in memories:
        for pattern in pii_patterns:
            if pattern in memory:
                violations += 1

    return 1.0 - (violations / total_checks)

"""Topic classification guardrail for the RAG pipeline.

Classifies user queries as ON_TOPIC, OFF_TOPIC, or AMBIGUOUS using
Gemini Flash with few-shot prompting. Off-topic queries are deflected
with a polite corporate response; ambiguous queries continue with a
warning flag for logging.

Fail-open: if the LLM fails, queries default to ON_TOPIC so
legitimate requests are never blocked (availability > restriction).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from src.config.topic_config import topic_config

if TYPE_CHECKING:
    from src.infrastructure.llm.client import GeminiClient

logger = logging.getLogger(__name__)

# ── Topic categories ─────────────────────────────────────────────────


class TopicCategory(StrEnum):
    """Classification result for a user query."""

    ON_TOPIC = "on_topic"
    OFF_TOPIC = "off_topic"
    AMBIGUOUS = "ambiguous"


# ── Result dataclass ─────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TopicGuardResult:
    """Result of topic classification."""

    category: TopicCategory
    confidence: str = ""
    explanation: str = ""


# ── Classifier prompt ────────────────────────────────────────────────


def _build_classifier_prompt(config=None) -> str:
    """Build the few-shot classification prompt from config."""
    cfg = config or topic_config

    allowed = "\n".join(f"  - {t}" for t in cfg.allowed_topics)
    prohibited = "\n".join(f"  - {t}" for t in cfg.prohibited_topics)

    examples = "\n\n".join(f'Query: "{ex["query"]}"\n{ex["classification"]}' for ex in cfg.few_shot_examples)

    return f"""\
You are a topic classifier for an enterprise banking assistant.

Your ONLY task is to classify whether a user query is related to the banking domain.

ALLOWED topics (ON_TOPIC):
{allowed}

PROHIBITED topics (OFF_TOPIC):
{prohibited}

Classification categories:
- ON_TOPIC: The query is clearly about banking, RRHH, regulations, or internal documentation.
- OFF_TOPIC: The query is clearly unrelated to the banking domain.
- AMBIGUOUS: The query is too short, generic, or unclear to determine the topic.

IMPORTANT:
- Greetings like "hola", "buenos dias" should be classified as ON_TOPIC (handled elsewhere).
- Questions about the assistant's capabilities are ON_TOPIC.
- When in doubt, classify as AMBIGUOUS — never block potentially legitimate queries.

Respond with EXACTLY one line:
ON_TOPIC
or
OFF_TOPIC:<brief_reason>
or
AMBIGUOUS:<brief_reason>

Examples:

{examples}

"""


# Pre-build default prompt at module level
TOPIC_CLASSIFIER_PROMPT = _build_classifier_prompt()

# ── Guard class ──────────────────────────────────────────────────────


@dataclass
class TopicGuard:
    """LLM-based topic classifier using Gemini Flash with few-shot prompting.

    Parameters
    ----------
    llm_client:
        GeminiClient configured with Flash for topic classification.
        If ``None``, all queries are classified as ON_TOPIC (useful in
        tests or when LLM is unavailable).
    enable_llm:
        Whether to run the LLM classifier. Default ``True``.
    """

    llm_client: GeminiClient | None = None
    enable_llm: bool = True
    _classified_count: int = field(default=0, init=False, repr=False)
    _off_topic_count: int = field(default=0, init=False, repr=False)

    @property
    def classified_count(self) -> int:
        """Total number of queries classified since instantiation."""
        return self._classified_count

    @property
    def off_topic_count(self) -> int:
        """Number of queries classified as off-topic since instantiation."""
        return self._off_topic_count

    async def classify(self, query: str) -> TopicGuardResult:
        """Classify a user query as ON_TOPIC, OFF_TOPIC, or AMBIGUOUS.

        Returns
        -------
        TopicGuardResult
            Contains the classification category, confidence, and explanation.
        """
        self._classified_count += 1

        if not self.enable_llm or self.llm_client is None:
            return TopicGuardResult(category=TopicCategory.ON_TOPIC)

        try:
            prompt = f'{TOPIC_CLASSIFIER_PROMPT}\nQuery: "{query}"\n'
            response = await self.llm_client.generate(prompt)
            result = self._parse_response(response.strip())
            if result.category == TopicCategory.OFF_TOPIC:
                self._off_topic_count += 1
            return result
        except Exception:
            # Fail-open: if LLM fails, let query through
            logger.exception("Topic classifier failed, failing open (ON_TOPIC)")
            return TopicGuardResult(category=TopicCategory.ON_TOPIC)

    @staticmethod
    def _parse_response(response: str) -> TopicGuardResult:
        """Parse the LLM classifier response.

        Expected format: ``ON_TOPIC``, ``OFF_TOPIC:<reason>``, or ``AMBIGUOUS:<reason>``
        """
        first_line = response.split("\n")[0].strip()
        upper = first_line.upper()

        if upper == "ON_TOPIC":
            return TopicGuardResult(category=TopicCategory.ON_TOPIC)

        if upper.startswith("OFF_TOPIC"):
            parts = first_line.split(":", 1)
            reason = parts[1].strip() if len(parts) > 1 else "off-topic query"
            return TopicGuardResult(
                category=TopicCategory.OFF_TOPIC,
                explanation=reason,
            )

        if upper.startswith("AMBIGUOUS"):
            parts = first_line.split(":", 1)
            reason = parts[1].strip() if len(parts) > 1 else "ambiguous query"
            return TopicGuardResult(
                category=TopicCategory.AMBIGUOUS,
                explanation=reason,
            )

        # Unrecognized response — fail-open
        logger.warning("Topic classifier returned unrecognized response: %.200s", response)
        return TopicGuardResult(category=TopicCategory.ON_TOPIC)

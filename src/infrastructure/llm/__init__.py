"""LLM infrastructure — Gemini client wrapper and prompt templates.

Public API:
    - GeminiClient: Unified wrapper for generation (sync + streaming) and embeddings.
    - GeminiModel: Enum for model selection (FLASH, FLASH_LITE).
    - SYSTEM_PROMPT_RAG: Base system prompt with 6 mandatory sections.
    - build_rag_prompt: Build a zero-shot RAG prompt with XML delimiters.
    - build_few_shot_prompt: Build a few-shot RAG prompt with banking examples.
    - build_zero_shot_prompt: Build a minimal zero-shot RAG prompt.
"""

from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.llm.prompts.system_prompt import SYSTEM_PROMPT_RAG, build_rag_prompt
from src.infrastructure.llm.prompts.templates.few_shot import build_few_shot_prompt
from src.infrastructure.llm.prompts.templates.zero_shot import build_zero_shot_prompt

__all__ = [
    "SYSTEM_PROMPT_RAG",
    "GeminiClient",
    "GeminiModel",
    "build_few_shot_prompt",
    "build_rag_prompt",
    "build_zero_shot_prompt",
]

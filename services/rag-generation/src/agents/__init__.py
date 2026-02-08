"""Paquete de agentes para RAG Generation.

Exporta helpers de forma lazy para evitar side-effects en import-time,
pero manteniendo una API pública estable para consumers.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "create_graph_builder",
    "RAGState",
    "UserMemory",
    "search_user_memories",
    "save_user_memory",
    "get_user_id_from_config",
    "format_memories_as_context",
    "MEMORY_TYPE_FACTS",
]


def __getattr__(name: str) -> Any:
    if name == "create_graph_builder":
        return import_module("src.agents.graph").create_graph_builder

    if name in {"RAGState", "UserMemory"}:
        state_module = import_module("src.agents.state")
        return getattr(state_module, name)

    if name in {
        "search_user_memories",
        "save_user_memory",
        "get_user_id_from_config",
        "format_memories_as_context",
        "MEMORY_TYPE_FACTS",
    }:
        memory_module = import_module("src.agents.memory")
        return getattr(memory_module, name)

    raise AttributeError(f"module 'src.agents' has no attribute {name!r}")

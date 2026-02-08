"""Agentes del servicio RAG Generation.

Este módulo expone el grafo principal, estados y utilidades de memoria.
"""

from src.agents.graph import create_graph_builder
from src.agents.state import RAGState, UserMemory
from src.agents.memory import (
    search_user_memories,
    save_user_memory,
    get_user_id_from_config,
    format_memories_as_context,
    MEMORY_TYPE_FACTS,
)

__all__ = [
    # Graph
    "create_graph_builder",
    # State
    "RAGState",
    "UserMemory",
    # Memory utilities
    "search_user_memories",
    "save_user_memory",
    "get_user_id_from_config",
    "format_memories_as_context",
    "MEMORY_TYPE_FACTS",
]

"""RAG pipeline state definition for LangGraph."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class RAGState(TypedDict):
    """Estado completo del pipeline RAG.

    Cada nodo del grafo recibe este estado y retorna un dict
    con los campos que desea actualizar.
    """

    # Query del usuario
    query: str
    query_type: str  # "saludo", "consulta", "fuera_dominio"
    query_embedding: list[float]

    # Historial de conversación (reducer: add_messages acumula sin reemplazar)
    messages: Annotated[list[BaseMessage], add_messages]

    # Retrieval
    retrieved_chunks: list[dict]
    reranked_chunks: list[dict]

    # Generación
    context_text: str
    user_memories: list[dict]
    response: str
    sources: list[dict]

    # Faithfulness scoring (spec T4-S9-02)
    faithfulness_score: float

    # PII detection (spec T4-S9-01)
    pii_detected: list[str]

    # Score gate (spec T6-S8-05)
    retrieval_confidence: str  # "suficiente", "insuficiente", "ambiguo"

    # Ambiguity detection (spec T6-S8-07)
    needs_clarification: bool  # True → route to generate_clarification

    # Control de acceso y seguridad
    user_id: int
    permissions: list[str]
    guardrail_passed: bool
    retry_count: int

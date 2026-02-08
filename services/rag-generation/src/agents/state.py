"""State Schema para el grafo de agentes RAG.

Define los estados utilizados en el grafo de agentes.
Incluye soporte para memoria a corto y largo plazo.
"""

from typing import Annotated, Literal, TypedDict, NotRequired
from langgraph.graph.message import add_messages


class RetrievedDocument(TypedDict):
    """Documento recuperado del vector store."""
    
    document_id: str
    chunk_id: str
    content: str
    title: str
    relevance_score: float
    metadata: dict


class Source(TypedDict):
    """Fuente utilizada para generar la respuesta."""
    
    document_id: str
    chunk_id: str
    title: str
    relevance_score: float
    snippet: str


class UserMemory(TypedDict):
    """Memoria del usuario recuperada del store."""
    
    key: str
    data: str
    type: str
    created_at: NotRequired[str]
    metadata: NotRequired[dict]


class RAGState(TypedDict):
    """Estado principal del grafo RAG.
    
    Contiene toda la información necesaria para procesar una consulta.
    Soporta memoria a corto plazo (messages) y largo plazo (user_memories).
    """
    
    # Identificación de la sesión y usuario
    session_id: str
    user_role: Literal["public", "private"]
    
    # Consulta y conversación (short-term memory via checkpointer)
    message: str
    messages: Annotated[list, add_messages]
    
    # Contexto recuperado
    retrieved_context: list[RetrievedDocument]
    
    # Estado del procesamiento
    current_agent: str
    
    # Resultado
    response: str
    sources: list[Source]
    
    # Long-term memory (cross-session via store)
    user_memories: NotRequired[list[UserMemory]]
    memory_context: NotRequired[str]
    
    # Metadata adicional
    metadata: dict

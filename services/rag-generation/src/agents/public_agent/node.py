"""Nodo del Agente Público para el grafo RAG.

Este nodo es responsable de:
1. Recibir consultas sobre información pública
2. Buscar documentos relevantes en la base de datos pública
3. Usar memoria del usuario para personalizar respuestas
4. Generar respuestas basadas en el contexto recuperado
5. Guardar información memorable del usuario
"""

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from src.config.llm_config import get_public_agent_llm
from src.agents.state import RAGState, Source
from src.agents.input_normalization import extract_message
from src.agents.memory import (
    get_user_id_from_config,
    save_user_memory,
    should_remember,
    extract_memorable_info,
    MEMORY_TYPE_FACTS,
)
from src.agents.public_agent.prompt import (
    PUBLIC_AGENT_SYSTEM_PROMPT,
    AUGMENTED_PROMPT_TEMPLATE,
    NO_DOCUMENTS_RESPONSE,
)
from src.agents.public_agent.tools import search_public_documents, rewrite_search_query


def _format_context(documents: list[dict]) -> str:
    """Formatea los documentos recuperados como contexto para el LLM.
    
    Args:
        documents: Lista de documentos recuperados.
        
    Returns:
        String formateado con el contexto de todos los documentos.
    """
    if not documents:
        return "No se encontró información pública relevante."
    
    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(
            f"[Documento {i}] {doc['title']}\n"
            f"{doc['content']}"
        )
    
    return "\n\n---\n\n".join(context_parts)


def _extract_sources(documents: list[dict]) -> list[Source]:
    """Extrae la información de fuentes de los documentos recuperados.
    
    Args:
        documents: Lista de documentos recuperados.
        
    Returns:
        Lista de objetos Source con la información de cada fuente.
    """
    sources = []
    for doc in documents:
        sources.append({
            "document_id": doc["document_id"],
            "chunk_id": doc["chunk_id"],
            "title": doc["title"],
            "relevance_score": doc["relevance_score"],
            "snippet": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
        })
    return sources


async def public_agent_node(
    state: RAGState,
    config: RunnableConfig,
    *,
    store: BaseStore,
) -> dict:
    """Nodo del agente público que procesa consultas sobre información pública.
    
    Este nodo implementa el flujo RAG completo con soporte de memoria:
    1. Query Rewriting - Optimiza la consulta para búsqueda
    2. Retrieval - Busca documentos públicos relevantes
    3. Memory Integration - Incluye contexto de memoria del usuario
    4. Augmentation - Construye el contexto aumentado
    5. Generation - Genera la respuesta con el LLM
    6. Memory Storage - Guarda información memorable del usuario
    
    Args:
        state: Estado actual del grafo RAG con la consulta del usuario.
        config: Configuración del runnable con user_id, tenant_id, etc.
        store: Store de LangGraph para memoria a largo plazo.
        
    Returns:
        Diccionario con la respuesta, fuentes y estado actualizado.
    """
    message = extract_message(state)
    if not message:
        return {
            "retrieved_context": [],
            "response": "No recibí un mensaje válido para procesar.",
            "sources": [],
            "current_agent": "public_agent",
            "messages": [],
        }
    memory_context = state.get("memory_context", "")
    existing_messages = state.get("messages", [])
    
    # Obtener user_id para guardar memorias
    user_id = get_user_id_from_config(config)
    
    # Extraer historial de chat para contextualización de la query
    chat_history: list[tuple[str, str]] = []
    for msg in existing_messages:
        if hasattr(msg, "type") and hasattr(msg, "content"):
            role = "user" if msg.type == "human" else "assistant"
            chat_history.append((role, msg.content))
    
    # 1. QUERY REWRITING: Contextualizar + extraer keywords
    search_query = await rewrite_search_query(
        message, chat_history=chat_history, memory_context=memory_context
    )
    
    # 2. RETRIEVAL: Buscar documentos públicos usando la query optimizada
    retrieved_docs = await search_public_documents(
        query=search_query,
        k=8,
        score_threshold=0.5,
    )
    
    # 3. VERIFICAR SI HAY DOCUMENTOS RECUPERADOS
    
    # Construir system prompt con memoria del usuario
    system_prompt = PUBLIC_AGENT_SYSTEM_PROMPT
    if memory_context:
        system_prompt = f"{PUBLIC_AGENT_SYSTEM_PROMPT}\n\n{memory_context}"
    
    if not retrieved_docs:
        # Si hay historial de conversación, intentar responder basándose en él
        if existing_messages or memory_context:
            llm = get_public_agent_llm()
            conversational_prompt = f"""El usuario pregunta: "{message}"

No encontré documentos relevantes en la base de datos para esta consulta.

REGLAS ESTRICTAS:
- Si la pregunta se refiere a algo que YA discutimos en esta conversación (visible en el historial de mensajes), respondé basándote ÚNICAMENTE en esa información del historial.
- Si la pregunta requiere información que NO está en el historial de la conversación, indicá claramente: "No dispongo de esa información en mi base de datos actual."
- NUNCA inventes, supongas ni proporciones información general que no esté en el historial. No importa si "sabés" la respuesta; si no está en los documentos ni en el historial, NO la des."""
            
            conv_messages = [
                SystemMessage(content=system_prompt),
            ]
            for msg in existing_messages:
                conv_messages.append(msg)
            conv_messages.append(HumanMessage(content=conversational_prompt))
            
            response_chunks = []
            async for chunk in llm.astream(conv_messages):
                response_chunks.append(chunk.content)
            response_text = "".join(response_chunks)
            
            # Guardar memoria si el mensaje contiene información memorable
            await _maybe_save_memory(store, user_id, message)
            
            return {
                "retrieved_context": [],
                "response": response_text,
                "sources": [],
                "current_agent": "public_agent",
                "messages": [
                    HumanMessage(content=message),
                    AIMessage(content=response_text),
                ],
            }
        
        # Sin historial ni documentos
        return {
            "retrieved_context": [],
            "response": NO_DOCUMENTS_RESPONSE,
            "sources": [],
            "current_agent": "public_agent",
            "messages": [
                HumanMessage(content=message),
                AIMessage(content=NO_DOCUMENTS_RESPONSE),
            ],
        }
    
    # 4. AUGMENTATION: Construir el contexto
    context = _format_context(retrieved_docs)
    
    # 5. GENERATION: Generar respuesta con LLM
    llm = get_public_agent_llm()
    
    augmented_prompt = AUGMENTED_PROMPT_TEMPLATE.format(
        context=context,
        message=message,
    )
    
    # Construir mensajes incluyendo el historial existente
    messages = [
        SystemMessage(content=system_prompt),
    ]
    
    # Agregar historial de conversación anterior (si existe)
    for msg in existing_messages:
        messages.append(msg)
    
    # Agregar el mensaje actual con el contexto aumentado
    messages.append(HumanMessage(content=augmented_prompt))
    
    # Usar astream para emitir eventos on_chat_model_stream
    response_chunks = []
    async for chunk in llm.astream(messages):
        response_chunks.append(chunk.content)
    response_text = "".join(response_chunks)
    
    # 6. Guardar memoria si el mensaje contiene información memorable
    await _maybe_save_memory(store, user_id, message)
    
    # 7. Extraer sources y retornar resultado
    sources = _extract_sources(retrieved_docs)
    
    return {
        "retrieved_context": retrieved_docs,
        "response": response_text,
        "sources": sources,
        "current_agent": "public_agent",
        "messages": [
            HumanMessage(content=message),
            AIMessage(content=response_text),
        ],
    }


async def _maybe_save_memory(store: BaseStore, user_id: str, message: str) -> None:
    """Guarda información memorable del mensaje si corresponde.
    
    Args:
        store: Store de LangGraph.
        user_id: ID del usuario.
        message: Mensaje del usuario.
    """
    if not store or user_id == "anonymous":
        return
    
    if should_remember(message):
        memorable_info = extract_memorable_info(message)
        if memorable_info:
            await save_user_memory(
                store=store,
                user_id=user_id,
                data=memorable_info,
                memory_type=MEMORY_TYPE_FACTS,
            )

"""RAG graph builder — orquesta el pipeline RAG con LangGraph.

Pipeline retrieve-first:
  classify_intent → guardrail_input → [routing] →
    saludo → respond_greeting
    blocked → respond_blocked
    consulta → retrieve → rerank → ambiguity_detector → [routing] →
      needs_clarification → generate_clarification
      clear → score_gate → [routing] →
        suficiente → assemble_context
        insuficiente → respond_blocked
        ambiguo → topic_classifier → [routing] → assemble_context | respond_blocked
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from src.application.graphs.nodes.ambiguity_detector import ambiguity_detector_node
from src.application.graphs.nodes.assemble_context import assemble_context_node
from src.application.graphs.nodes.classify_intent import classify_intent_node
from src.application.graphs.nodes.generate_clarification import generate_clarification_node
from src.application.graphs.nodes.rerank import rerank_node
from src.application.graphs.nodes.respond_blocked import respond_blocked_node
from src.application.graphs.nodes.respond_greeting import respond_greeting_node
from src.application.graphs.nodes.retrieve import retrieve_node
from src.application.graphs.nodes.score_gate import score_gate_node
from src.application.graphs.nodes.topic_classifier import topic_classifier_node
from src.application.graphs.nodes.validate_input import validate_input_node
from src.application.graphs.state import RAGState

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


def _route_after_guardrail(state: RAGState) -> str:
    """Routing después del guardrail de entrada.

    - "saludo" → respond_greeting (respuesta LLM conversacional)
    - "blocked" → respond_blocked (respuesta de bloqueo)
    - "consulta" (y cualquier otro) → retrieve pipeline
    """
    query_type = state.get("query_type", "consulta")

    if query_type == "saludo":
        return "respond_greeting"

    if query_type == "blocked":
        return "respond_blocked"

    return "retrieve"


def _route_after_ambiguity_detector(state: RAGState) -> str:
    """Routing post-ambiguity_detector (runs BEFORE score_gate).

    - needs_clarification=True → generate_clarification
    - needs_clarification=False → score_gate (continue normal pipeline)
    """
    if state.get("needs_clarification", False):
        return "generate_clarification"
    return "score_gate"


def _route_after_score_gate(state: RAGState) -> str:
    """Routing post-score_gate basado en la confianza del retrieval.

    - "suficiente" → assemble_context (direct, ambiguity already checked)
    - "insuficiente" → respond_blocked (fallback)
    - "ambiguo" → topic_classifier (LLM decide si está en dominio)
    """
    confidence = state.get("retrieval_confidence", "insuficiente")

    if confidence == "suficiente":
        return "assemble_context"
    if confidence == "ambiguo":
        return "topic_classifier"

    return "respond_blocked"


def _route_after_topic_classifier(state: RAGState) -> str:
    """Routing después del topic_classifier (red de seguridad).

    Solo se invoca para casos ambiguos del score_gate.
    - ON_TOPIC (query_type="consulta") → assemble_context
    - OFF_TOPIC (query_type="fuera_dominio") / blocked → respond_blocked
    """
    query_type = state.get("query_type", "consulta")

    if query_type in ("blocked", "fuera_dominio"):
        return "respond_blocked"

    return "assemble_context"


def build_rag_graph(checkpointer=None):
    """Construye y compila el grafo RAG con patron retrieve-first.

    Este grafo ejecuta todo el pipeline EXCEPTO la generación LLM:
    classify → guardrail → retrieve → rerank → ambiguity_detector → score_gate → assemble_context

    La generación LLM se hace por fuera del grafo para permitir
    streaming token-por-token real.

    Args:
        checkpointer: Instancia de PostgresSaver para persistencia.

    Returns:
        CompiledGraph listo para ainvoke.
    """
    # LangGraph Studio CLI puede pasar un dict de config si no se especifica.
    # Solo usamos el checkpointer si es un objeto Saver real.
    if isinstance(checkpointer, dict):
        checkpointer = None
    graph = StateGraph(RAGState)

    # --- Nodos ---
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("guardrail_input", validate_input_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("score_gate", score_gate_node)
    graph.add_node("ambiguity_detector", ambiguity_detector_node)
    graph.add_node("generate_clarification", generate_clarification_node)
    graph.add_node("topic_classifier", topic_classifier_node)
    graph.add_node("assemble_context", assemble_context_node)
    graph.add_node("respond_blocked", respond_blocked_node)
    graph.add_node("respond_greeting", respond_greeting_node)

    # --- Edges ---
    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "guardrail_input")

    # Post-guardrail: saludo → respond_greeting, blocked → respond_blocked, consulta → retrieve
    graph.add_conditional_edges(
        "guardrail_input",
        _route_after_guardrail,
        {
            "respond_greeting": "respond_greeting",
            "respond_blocked": "respond_blocked",
            "retrieve": "retrieve",
        },
    )

    # Retrieve-first pipeline: retrieve → rerank → ambiguity_detector
    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "ambiguity_detector")

    # Post-ambiguity_detector: ambigua → clarificación, clara → score_gate
    graph.add_conditional_edges(
        "ambiguity_detector",
        _route_after_ambiguity_detector,
        {
            "generate_clarification": "generate_clarification",
            "score_gate": "score_gate",
        },
    )

    # Post-score_gate: suficiente → assemble, insuficiente → blocked, ambiguo → topic
    graph.add_conditional_edges(
        "score_gate",
        _route_after_score_gate,
        {
            "assemble_context": "assemble_context",
            "respond_blocked": "respond_blocked",
            "topic_classifier": "topic_classifier",
        },
    )

    # Post-topic_classifier: consulta → assemble, fuera_dominio → blocked
    graph.add_conditional_edges(
        "topic_classifier",
        _route_after_topic_classifier,
        {
            "assemble_context": "assemble_context",
            "respond_blocked": "respond_blocked",
        },
    )

    graph.add_edge("assemble_context", END)
    graph.add_edge("generate_clarification", END)
    graph.add_edge("respond_blocked", END)
    graph.add_edge("respond_greeting", END)

    return graph.compile(checkpointer=checkpointer)


@asynccontextmanager
async def create_checkpointer(db_url: str) -> AsyncIterator[AsyncPostgresSaver]:
    """Create an AsyncPostgresSaver backed by a connection pool.

    Uses ``AsyncConnectionPool`` instead of a single connection so the
    checkpointer can survive idle-timeout disconnects and Docker
    networking hiccups.  The pool validates connections transparently
    and replaces dead ones automatically.

    Normalises ``postgresql+asyncpg://`` to ``postgresql://`` which is
    the format expected by ``psycopg`` (used internally by the saver).
    Calls ``setup()`` to create checkpoint tables idempotently.
    """
    conn_string = db_url.replace("+asyncpg", "")
    async with AsyncConnectionPool(
        conninfo=conn_string,
        min_size=2,
        max_size=5,
        open=False,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    ) as pool:
        await pool.open()
        saver = AsyncPostgresSaver(conn=pool)  # type: ignore[arg-type]  # pool uses dict_row but generic isn't narrowed
        await saver.setup()
        logger.info("PostgresSaver checkpoint tables ready (pooled)")
        yield saver

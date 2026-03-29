"""Nodo classify_intent: determina el tipo de query del usuario.

Clasifica queries en dos categorias:
- "saludo": saludos simples, respuesta directa sin retrieval.
- "consulta": toda query no-saludo avanza al retrieval (patron retrieve-first).

La determinacion de dominio se delega al score_gate post-retrieval,
que evalua la relevancia de los documentos recuperados en lugar de
depender de keywords estaticas.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from src.infrastructure.observability.langfuse_client import observe

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# Patrones para declaraciones de contexto del usuario (rol, ubicación, preferencias).
# Solo aplica cuando la query NO contiene "?" (no es una pregunta).
# Conservador: solo prefijos inequívocos de declaración personal.
_CONTEXT_STATEMENT_RE = re.compile(
    r"^(?:"
    r"soy\s"
    r"|trabajo\s+en\s"
    r"|estoy\s+en\s"
    r"|me\s+llamo\s"
    r"|prefiero\s"
    r"|siempre\s+respond"  # "siempre respondeme", "siempre responde"
    r"|siempre\s+us"  # "siempre usa", "siempre usame"
    # Posesivos: "Mi DNI es...", "Mi área es...", "Mis datos son..."
    # Whitelist restrictiva: solo sustantivos de contexto personal/laboral,
    # excluye "tarjeta", "cuenta", "préstamo" para no capturar consultas bancarias.
    r"|mi\s+(?:dni|area|área|puesto|rol|equipo|sucursal|legajo|nombre)\s"
    r"|mis\s+(?:datos|preferencias)\s"
    r")",
    re.IGNORECASE,
)

_GREETING_KEYWORDS = frozenset(
    {
        "hola",
        "buenos",
        "dias",
        "buenas",
        "tardes",
        "noches",
        "hey",
        "saludos",
        "buen",
        "dia",
        "hi",
        "hello",
        # conversational greetings
        "como",
        "estas",
        "tal",
        "bien",
        "que",
        "todo",
        "genial",
        "excelente",
    }
)

# Patrones para saludos conversacionales que no pueden resolverse solo con keywords
# (palabras como "te", "va", "andas" son demasiado genericas para el set de keywords)
_GREETING_PATTERN_RE = re.compile(
    r"^(?:como\s+te\s+va|como\s+andas?)$",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    """Normaliza texto: minusculas, sin tildes comunes del espanol."""
    result = text.lower()
    for src, dst in (
        ("\u00e1", "a"),
        ("\u00e9", "e"),
        ("\u00ed", "i"),
        ("\u00f3", "o"),
        ("\u00fa", "u"),
        ("\u00fc", "u"),
        ("\u00f1", "n"),
    ):
        result = result.replace(src, dst)
    return result


@observe(name="rag_classify_intent")
def classify_intent_node(state: RAGState) -> dict:
    """Clasifica el intent de la query del usuario.

    Valores posibles de query_type:
    - "saludo": saludos simples, se responde directo sin retrieval.
    - "consulta": toda query no-saludo avanza al retrieval (retrieve-first).

    La determinacion de dominio se delega al score_gate post-retrieval.
    """
    messages = state.get("messages", [])
    query = state["query"].strip()
    normalized = _normalize(query)
    clean_query = normalized.strip("¿¡!.?,;:").strip()

    # --- Nivel 0: Short-term Feedback Loop (Respuesta a Clarificación) ---
    # Si el ultimo mensaje del AI fue una clarificación (needs_clarification=True),
    # intentamos reconstruir la consulta usando la respuesta actual del usuario
    # (ej: "La 1" o "Esa misma") y la consulta original guardada.
    if messages and len(messages) >= 1:
        last_msg = messages[-1]
        # Si el ultimo mensaje indica que se pidio clarificación
        if hasattr(last_msg, "content") and any(
            x in last_msg.content for x in ["¿Cuál de estas opciones te interesa?", "especificar qué necesitás"]
        ):
            # Verificamos si tenemos una 'context_query' (guardada en el nodo de clarificación)
            # o usamos la query del estado que aun no ha sido sobreescrita.
            context_query = state.get("query", "")
            if context_query and clean_query not in context_query:
                # Re-escribimos la query: [Original] + [Clarificación del usuario]
                # Esto permite que el siguiente retrieval sea mucho mas preciso.
                new_query = f"{context_query} (Clarificación: {query})"
                logger.info("Feedback loop detected: Re-writing query to '%s'", new_query)
                return {"query": new_query, "query_type": "consulta"}

    words = [w for w in clean_query.replace(",", " ").split() if w.strip()]
    if not words:
        return {"query_type": "consulta"}

    # --- Nivel 1: Declaración de contexto del usuario (sin "?") ---
    # Mensajes como "Soy oficial en Rosario", "Trabajo en RRHH", "Prefiero viñetas"
    # no son consultas: deben recibir un acuse de recibo y alimentar la memoria episódica.
    if "?" not in query and _CONTEXT_STATEMENT_RE.match(normalized):
        return {"query_type": "contexto_usuario"}

    # --- Nivel 2: Saludo por keywords ---
    if all(w in _GREETING_KEYWORDS for w in words):
        return {"query_type": "saludo"}

    # --- Nivel 3: Saludos conversacionales por patron regex ---
    if _GREETING_PATTERN_RE.match(clean_query):
        return {"query_type": "saludo"}

    # Toda query no-saludo se clasifica como consulta y avanza al retrieval.
    return {"query_type": "consulta"}

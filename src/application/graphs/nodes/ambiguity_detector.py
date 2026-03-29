"""Nodo ambiguity_detector: clasifica si una query requiere clarificación.

Se ejecuta DESPUÉS de rerank y ANTES de score_gate. TODAS las queries
que pasan retrieval llegan a este nodo, independientemente de sus scores
de reranking. La decisión se toma en base a señales de la query, metadata
de los documentos recuperados y scores de retrieval.

Arquitectura de decisión:
1. Heurísticas deterministas (sin costo LLM):
   - Query muy corta sin entidad de dominio específica.
   - Patrones genéricos sin complemento específico.
   - Frase genérica + sustantivo genérico sin calificador de dominio.
   - Pronombres sin referente en ausencia de historial.
   - Documentos de ≥ 2 áreas funcionales distintas con scores similares.
   - Score de retrieval bajo + query corta/genérica.
   - Entidad de dominio específica → CLEAR.
2. LLM (Gemini Flash Lite) solo para casos borderline:
   - Si las heurísticas clasifican con certeza → no se llama al LLM.
   - Si las heurísticas son inconclusas → LLM clasifica CLEAR vs AMBIGUOUS.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.observability.langfuse_client import observe

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# ── Heurísticas: patrones genéricos sin complemento ──────────────────

# Frases que son ambiguas cuando NO van seguidas de un complemento específico.
# Ejemplos: "¿cómo hago?" sí; "¿cómo hago para pedir mi préstamo hipotecario?" no.
_GENERIC_PATTERN_RE = re.compile(
    r"^\s*[¿]?\s*"
    r"(?:"
    r"(?:como|cómo)\s+(?:hago|puedo|se\s+hace|solicito|pido)"  # "¿cómo hago?"
    r"|necesito\s+(?:informaci[oó]n|ayuda|saber|un\s+certificado|certificado)"  # "necesito información"
    r"|(?:cu[aá]nto\s+(?:me\s+)?(?:sale|cuesta|cobra|tarda))"  # "¿cuánto me sale?"
    r"|(?:cu[aá]l\s+es\s+(?:el|la)\s+l[ií]mite)"  # "¿cuál es el límite?"
    r"|(?:qu[eé]\s+necesito\s+(?:para|hacer))"  # "¿qué necesito para?"
    r")"
    r"(?:[^a-zA-Z0-9]*)$",
    re.IGNORECASE,
)

# Pronombres sin referente — ambiguos solo si no hay historial de conversación
_PRONOUN_RE = re.compile(
    r"\b(eso|esto|lo\s+anterior|ese\s+tr[aá]mite|ese\s+proceso)\b",
    re.IGNORECASE,
)

# Palabras de dominio específico que indican que la query NO es ambigua
# aunque sea corta (ej: "vacaciones" SÍ es ambigua; "licencia médica" no tanto)
_DOMAIN_SPECIFIC_RE = re.compile(
    r"\b("
    r"hipotecario|hipoteca|cr[eé]dito\s+personal|pr[eé]stamo\s+personal"
    r"|tarjeta\s+de\s+cr[eé]dito|tarjeta\s+de\s+d[eé]bito"
    r"|licencia\s+m[eé]dica|licencia\s+por\s+maternidad|licencia\s+por\s+paternidad"
    r"|adelanto\s+de\s+sueldo|adelanto\s+de\s+haberes"
    r"|certificado\s+de\s+trabajo|certificado\s+de\s+ingresos|recibo\s+de\s+sueldo"
    r"|d[ií]as\s+de\s+vacaciones|d[ií]as\s+h[aá]biles"
    r")\b",
    re.IGNORECASE,
)

# Sustantivos genéricos del dominio bancario — ambiguos sin calificador.
# "adelanto" es ambiguo; "adelanto de sueldo" es específico (capturado por _DOMAIN_SPECIFIC_RE).
_GENERIC_NOUNS = frozenset(
    {
        "adelanto",
        "certificado",
        "limite",
        "límite",
        "tarjeta",
        "tramite",
        "trámite",
        "servicio",
        "producto",
        "paquete",
        "seguro",
        "cuenta",
        "credito",
        "crédito",
        "debito",
        "débito",
        "prestamo",
        "préstamo",
        "licencia",
        "baja",
        "alta",
    }
)

# Pattern: generic verb phrase + generic noun (e.g. "¿Cómo hago para pedir un adelanto?")
_GENERIC_VERB_NOUN_RE = re.compile(
    r"(?:como|cómo)\s+(?:hago|puedo|se\s+hace|solicito|pido)"
    r".*\b(" + "|".join(re.escape(n) for n in sorted(_GENERIC_NOUNS)) + r")\b"
    r"|(?:necesito|quiero)\s+(?:(?:sacar|pedir|solicitar|hacer|obtener|tramitar|consultar|ver|saber)\s+)?(?:un(?:a)?|el|la|mi|los|las)?\s*"
    r"\b(" + "|".join(re.escape(n) for n in sorted(_GENERIC_NOUNS)) + r")\b"
    r"|(?:cu[aá]l\s+es\s+(?:el|la|mi)\s+)"
    r"\b(" + "|".join(re.escape(n) for n in sorted(_GENERIC_NOUNS)) + r")\b",
    re.IGNORECASE,
)

# ── Prompt LLM para casos borderline ─────────────────────────────────

_AMBIGUITY_LLM_PROMPT = """\
You are a query classifier for an enterprise banking assistant.

Classify the user query as CLEAR or AMBIGUOUS.

A query is AMBIGUOUS if it is a banking-related query that is too vague to answer \
without knowing which specific topic the user means. Examples: "vacaciones", \
"necesito información de eso", "¿cómo hago el trámite?", "¿cuánto me sale?", \
"¿cuál es el límite?".

A query is CLEAR if it refers to a specific topic even if phrased informally. \
Examples: "¿cuántos días de vacaciones tengo?", "quiero dar de baja mi tarjeta", \
"¿cómo pido un préstamo hipotecario?".

IMPORTANT: If the query is clearly outside the banking domain (sports, recipes, \
politics, entertainment, etc.), classify it as CLEAR. The system has separate \
mechanisms to handle out-of-domain queries — do NOT classify them as AMBIGUOUS.

{history_context}
Given the conversation history (if any), evaluate whether the query is a follow-up \
question about the topic already discussed. If the user is clearly continuing a \
previous topic, classify as CLEAR — it is not ambiguous, just short or implicit.

Available document topics (for context only):
{topics}

Query: "{query}"

Respond with exactly one word: CLEAR or AMBIGUOUS
"""

# ── Module-level LLM client (lazy init) ──────────────────────────────

_llm_client: GeminiClient | None = None


def _get_llm_client() -> GeminiClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = GeminiClient(model=GeminiModel.FLASH_LITE, temperature=0.0)
    return _llm_client


def set_ambiguity_llm_client(client: GeminiClient | None) -> None:
    """Inyecta un GeminiClient custom (para tests)."""
    global _llm_client
    _llm_client = client


# ── Helpers ──────────────────────────────────────────────────────────


def _extract_topics(reranked_chunks: list[dict]) -> list[str]:
    """Extrae títulos y áreas funcionales de los chunks (sin contenido)."""
    seen: set[str] = set()
    topics: list[str] = []
    for chunk in reranked_chunks:
        area = chunk.get("area_funcional") or chunk.get("metadata", {}).get("area_funcional", "")
        title = chunk.get("title") or chunk.get("metadata", {}).get("title", "")
        label = " — ".join(filter(None, [area, title]))
        if label and label not in seen:
            seen.add(label)
            topics.append(label)
    return topics


def _count_distinct_areas(reranked_chunks: list[dict]) -> int:
    """Cuenta áreas funcionales distintas en los chunks recuperados."""
    areas: set[str] = set()
    for chunk in reranked_chunks:
        area = chunk.get("area_funcional") or chunk.get("metadata", {}).get("area_funcional", "")
        if area:
            areas.add(area.lower())
    return len(areas)


def _has_conversation_context(messages: list) -> bool:
    """Verifica si hay historial de conversación previo (mensajes del asistente)."""
    from langchain_core.messages import AIMessage

    return any(isinstance(m, AIMessage) for m in messages)


def _build_history_summary(messages: list, max_turns: int = 2) -> str:
    """Extrae las últimas N preguntas del usuario del historial.

    Devuelve cadena vacía si no hay mensajes humanos previos.
    El resumen no excede ~200 caracteres (32 prefijo + 2 * 80 + separadores).
    """
    from langchain_core.messages import HumanMessage

    if not messages:
        return ""
    human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
    recent = human_msgs[-max_turns:]
    if not recent:
        return ""
    summary = "; ".join(m.content[:80] for m in recent if isinstance(m.content, str))
    return f"Historial reciente del usuario: {summary}"


def _heuristic_classify(
    query: str,
    reranked_chunks: list[dict],
    has_history: bool,
) -> str | None:
    """Clasifica la query con heurísticas deterministas.

    Returns
    -------
    "AMBIGUOUS" | "CLEAR" | None
        None significa que las heurísticas son inconclusas → usar LLM.
    """
    query_stripped = query.strip()
    token_count = len(query_stripped.split())

    # 1. Pronombres sin referente — ambiguos solo sin historial
    if _PRONOUN_RE.search(query_stripped) and not has_history:
        logger.debug("ambiguity_detector: heuristic=pronoun_no_history → AMBIGUOUS")
        return "AMBIGUOUS"

    # 2. Query monopalabra sin entidad específica de dominio
    if token_count <= 2 and not _DOMAIN_SPECIFIC_RE.search(query_stripped):
        logger.debug("ambiguity_detector: heuristic=short_no_domain → AMBIGUOUS")
        return "AMBIGUOUS"

    # 3. Patrón genérico sin complemento (strict: query ends after pattern)
    #    Con historial, la query puede ser una pregunta de seguimiento legítima
    #    (ej: "¿cuánto tarda?" después de discutir un trámite específico).
    if _GENERIC_PATTERN_RE.search(query_stripped) and not has_history:
        logger.debug("ambiguity_detector: heuristic=generic_pattern → AMBIGUOUS")
        return "AMBIGUOUS"

    # 4. Generic verb phrase + generic noun without domain-specific qualifier
    #    e.g. "¿Cómo hago para pedir un adelanto?" — ambiguous
    #    but NOT "¿Cómo hago para pedir un adelanto de sueldo?" — specific
    if _GENERIC_VERB_NOUN_RE.search(query_stripped) and not _DOMAIN_SPECIFIC_RE.search(query_stripped):
        logger.debug("ambiguity_detector: heuristic=generic_verb_noun → AMBIGUOUS")
        return "AMBIGUOUS"

    # 5. Documentos de ≥ 2 áreas distintas con scores similares
    if len(reranked_chunks) >= 2:
        distinct_areas = _count_distinct_areas(reranked_chunks)
        if distinct_areas >= 2:
            scores = [chunk.get("score", 0.0) for chunk in reranked_chunks[:3]]
            if len(scores) >= 2 and (max(scores) - min(scores)) < 0.15:
                logger.debug(
                    "ambiguity_detector: heuristic=multi_area_similar_scores → AMBIGUOUS (areas=%d, score_spread=%.3f)",
                    distinct_areas,
                    max(scores) - min(scores),
                )
                return "AMBIGUOUS"

    # 6. Low retrieval score + short/generic query reinforces ambiguity.
    #    Con historial, el score bajo puede deberse a que la query es una
    #    referencia implícita al contexto previo, no una pregunta genuinamente vaga.
    if reranked_chunks and not has_history:
        max_score = max(chunk.get("score", 0.0) for chunk in reranked_chunks)
        if max_score < 0.78 and (token_count <= 3 or _GENERIC_VERB_NOUN_RE.search(query_stripped)):
            logger.debug(
                "ambiguity_detector: heuristic=low_score_generic → AMBIGUOUS (max_score=%.3f)",
                max_score,
            )
            return "AMBIGUOUS"

    # 7. Domain-specific term present → clearly not ambiguous
    if _DOMAIN_SPECIFIC_RE.search(query_stripped):
        logger.debug("ambiguity_detector: heuristic=domain_specific → CLEAR")
        return "CLEAR"

    # Inconclusive → needs LLM
    return None


# ── LLM borderline ────────────────────────────────────────────────────


async def _classify_with_llm(
    query: str,
    reranked_chunks: list[dict],
    messages: list,
) -> bool:
    """Clasifica query borderline con LLM, inyectando contexto conversacional.

    Returns
    -------
    bool
        True si la query es AMBIGUOUS, False si es CLEAR.
    """
    topics = _extract_topics(reranked_chunks)
    topics_text = "\n".join(f"- {t}" for t in topics) if topics else "- (sin temas disponibles)"
    history_context = _build_history_summary(messages)

    prompt = _AMBIGUITY_LLM_PROMPT.format(
        query=query,
        topics=topics_text,
        history_context=history_context,
    )

    try:
        client = _get_llm_client()
        response = await client.generate(prompt)
        classification = response.strip().upper()
        needs_clarification = "AMBIGUOUS" in classification
        logger.info(
            "ambiguity_detector: %s (llm), query=%.80s",
            "AMBIGUOUS" if needs_clarification else "CLEAR",
            query,
        )
    except Exception:
        # Fail-open: si el LLM falla, no interrumpir el pipeline
        logger.exception("ambiguity_detector: LLM failed, defaulting to CLEAR")
        needs_clarification = False

    return needs_clarification


# ── Nodo principal ────────────────────────────────────────────────────


@observe(name="rag_ambiguity_detector")
async def ambiguity_detector_node(state: RAGState) -> dict:
    """Clasifica si la query requiere clarificación antes de la generación.

    Actualiza ``needs_clarification`` en el estado.
    """
    query: str = state.get("query", "")
    reranked_chunks: list[dict] = state.get("reranked_chunks", [])
    messages: list = state.get("messages", [])

    has_history = _has_conversation_context(messages)

    # ── Paso 1: heurísticas ───────────────────────────────────────────
    heuristic_result = _heuristic_classify(query, reranked_chunks, has_history)

    if heuristic_result == "AMBIGUOUS":
        logger.info("ambiguity_detector: AMBIGUOUS (heuristic), query=%.80s", query)
        return {"needs_clarification": True}

    if heuristic_result == "CLEAR":
        logger.info("ambiguity_detector: CLEAR (heuristic), query=%.80s", query)
        return {"needs_clarification": False}

    # ── Paso 2: LLM para casos borderline (con contexto conversacional) ──
    needs_clarification = await _classify_with_llm(query, reranked_chunks, messages)
    return {"needs_clarification": needs_clarification}

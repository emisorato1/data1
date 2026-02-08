"""Query Rewriter - Extrae keywords de búsqueda de consultas conversacionales.

Este módulo mejora el retrieval de RAG al convertir consultas complejas
o conversacionales en keywords optimizadas para búsqueda vectorial.

Ejemplo:
    Input:  "podrias darme un paso a paso para hacer un taco?"
    Output: "tacos preparación receta ingredientes pasos"
"""

import os
import unicodedata
from openai import OpenAI


# Prompt para extracción de keywords
QUERY_REWRITE_PROMPT = """Eres un experto en búsqueda semántica. Tu tarea es extraer las palabras clave más relevantes de una consulta del usuario para buscar en una base de datos de documentos.

INSTRUCCIONES:
1. Extrae SOLO los conceptos y temas principales de la consulta
2. Ignora palabras conversacionales como "podrías", "dame", "quiero", "necesito", "por favor", "como", "que", "donde", etc.
3. Incluye sinónimos relevantes y términos en inglés si el tema es técnico
4. Responde ÚNICAMENTE con las keywords separadas por espacios
5. Máximo 10 palabras
6. Si la consulta es muy corta (1-3 palabras), SIEMPRE expande con términos relacionados y sinónimos
7. Mantené siempre el término original del tema principal en las keywords

EJEMPLOS:
- "podrias darme un paso a paso para hacer un taco?" → "tacos preparación receta ingredientes pasos cocina"
- "cuéntame sobre la historia de los tacos" → "tacos historia origen tradición méxico"
- "qué ingredientes necesito para hacer salsa verde?" → "salsa verde ingredientes receta preparación"
- "tacos" → "tacos comida mexicana recetas"
- "rag" → "rag retrieval augmented generation técnica búsqueda"
- "como hago un rag?" → "rag retrieval augmented generation implementación construcción"
- "que es un rag?" → "rag retrieval augmented generation definición concepto"
- "recetas mexicanas tradicionales" → "recetas mexicanas tradicionales cocina típica"

CONSULTA DEL USUARIO:
{query}

KEYWORDS DE BÚSQUEDA:"""


CONTEXTUALIZE_PROMPT = """Dado el historial de conversación y las últimas consultas del usuario, reescribí la consulta para que sea AUTOCONTENIDA (que se entienda sin necesidad del historial).

REGLAS:
1. Si la consulta hace referencia a algo mencionado antes ("la receta", "eso", "lo anterior", "el tema", etc.), reemplazá la referencia por el término concreto del historial.
2. Si la consulta ya es autocontenida, devolvela sin cambios.
3. Respondé ÚNICAMENTE con la consulta reformulada, nada más.

EJEMPLOS:
- Historial: ["quiero hacer tacos"] → Consulta: "dime la receta" → "dime la receta de tacos"
- Historial: ["que es un rag?", "RAG es..."] → Consulta: "como lo implemento?" → "como implemento un rag?"
- Historial: ["me gusta el chocolate"] → Consulta: "que postres hay?" → "que postres hay?" (ya es autocontenida)

HISTORIAL RECIENTE:
{history}

CONSULTA DEL USUARIO:
{query}

CONSULTA REFORMULADA:"""


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Obtiene el cliente de OpenAI (singleton)."""
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY no está configurada")
        _client = OpenAI(api_key=api_key)
    return _client


def contextualize_query(
    query: str,
    chat_history: list[tuple[str, str]] | None = None,
    memory_context: str = "",
) -> str:
    """Resuelve referencias anafóricas usando el historial y/o memoria.

    Convierte consultas dependientes del contexto en consultas autocontenidas.
    Ejemplo: "dime la receta" + historial sobre tacos → "dime la receta de tacos"

    Args:
        query: Consulta actual del usuario.
        chat_history: Lista de tuplas (role, content) con mensajes recientes.
            Ejemplo: [("user", "quiero hacer tacos"), ("assistant", "¿Querés la receta?")]
        memory_context: Contexto de memoria long-term del usuario (ej: "Le gusta cocinar tacos").

    Returns:
        Consulta autocontenida (reformulada si era necesario).
    """
    if not chat_history and not memory_context:
        return query

    # Formatear historial (últimos 6 mensajes para mantener bajo el costo)
    history_parts = []
    if chat_history:
        recent = chat_history[-6:]
        history_parts.append("\n".join(f"- {role}: {content[:200]}" for role, content in recent))
    if memory_context:
        history_parts.append(f"[Memoria del usuario]: {memory_context[:300]}")
    history_str = "\n".join(history_parts)

    try:
        client = _get_client()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": CONTEXTUALIZE_PROMPT.format(
                    history=history_str, query=query
                )}
            ],
            max_tokens=100,
            temperature=0.0,
            timeout=5,
        )

        contextualized = response.choices[0].message.content.strip()

        if contextualized and contextualized != query:
            print(f"[Contextualizer] '{query}' → '{contextualized}'")
            return contextualized

        return query

    except Exception as e:
        print(f"[Contextualizer] Error: {e}, usando query original")
        return query


def _remove_accents(text: str) -> str:
    """Elimina acentos/diacríticos de un texto para comparación flexible."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _is_conversational(query: str) -> bool:
    """Detecta si una consulta es conversacional (no son keywords puras).

    Busca palabras interrogativas, verbos modales y frases corteses,
    con y sin acentos.
    """
    query_normalized = _remove_accents(query.lower())

    # Palabras que indican pregunta o frase conversacional
    conversational_markers = [
        # Interrogativas (sin acentos para matchear ambas formas)
        "como ", "que ", "cual ", "donde ", "cuando ", "porque ", "quien ",
        "cuales ", "cuantos ", "cuantas ",
        # Verbos modales / cortesía
        "podrias", "podria", "puedes", "puede",
        "dame", "dime", "explicame", "cuentame", "muestrame",
        "quiero", "necesito", "quisiera", "gustaria",
        "por favor", "porfavor",
        # Patrones de pregunta
        "que es ", "que son ", "como se ", "como hago", "como hacer",
        "para que ", "en que ",
    ]

    return any(marker in query_normalized for marker in conversational_markers)


def rewrite_query(query: str) -> str:
    """Reescribe una consulta conversacional a keywords de búsqueda.

    SIEMPRE pasa por el LLM rewriter excepto si la consulta tiene 5+
    palabras y NO parece conversacional (i.e. ya son keywords puras).

    Args:
        query: La consulta original del usuario

    Returns:
        Keywords optimizadas para búsqueda vectorial
    """
    # Limpiar la consulta (quitar signos de interrogación, espacios extra, etc.)
    cleaned_query = query.strip().rstrip("?!¿¡").strip()

    word_count = len(cleaned_query.split())

    # Consultas cortas (1-4 palabras) → SIEMPRE reescribir
    # Consultas largas (5+ palabras) → solo si parecen conversacionales
    if word_count >= 5 and not _is_conversational(cleaned_query):
        print(f"[QueryRewriter] Bypass (keywords detected): '{query}'")
        return cleaned_query

    try:
        client = _get_client()

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo rápido y económico
            messages=[
                {"role": "user", "content": QUERY_REWRITE_PROMPT.format(query=cleaned_query)}
            ],
            max_tokens=50,
            temperature=0.0,  # Determinístico
            timeout=5,  # Timeout bajo para no aumentar mucho la latencia
        )

        rewritten = response.choices[0].message.content.strip()

        # Log para debugging (se verá en docker logs)
        print(f"[QueryRewriter] Original: '{query}' → Rewritten: '{rewritten}'")

        return rewritten if rewritten else cleaned_query

    except Exception as e:
        # En caso de error, usar la consulta original
        print(f"[QueryRewriter] Error: {e}, usando query original")
        return cleaned_query
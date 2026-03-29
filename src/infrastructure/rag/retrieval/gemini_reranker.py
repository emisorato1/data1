import json
import logging

from google import genai
from google.genai import types

from src.config.settings import settings
from src.infrastructure.rag.retrieval.models import StoredChunk

logger = logging.getLogger(__name__)


class GeminiReranker:
    """Reranker alternativo usando Gemini Pro.

    Toma los resultados de hybrid search y usa un prompt de razonamiento
    para re-ordenarlos según su utilidad real para responder la pregunta.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        if settings.use_vertex_ai:
            import google.auth

            effective_quota = settings.gcp_quota_project_id or settings.gcp_project_id
            credentials, _ = google.auth.default(quota_project_id=effective_quota)
            self._client = genai.Client(
                vertexai=True,
                project=settings.gcp_project_id,
                location=settings.gcp_location,
                credentials=credentials,
            )
        else:
            resolved_key = api_key or settings.gemini_api_key.get_secret_value()
            self._client = genai.Client(api_key=resolved_key)
        self._model = model or settings.gemini_model_flash

    async def rerank(self, query: str, chunks: list[StoredChunk], top_k: int = 5) -> list[StoredChunk]:
        """Re-ordena los chunks usando Gemini."""
        if not chunks:
            return []

        # Construir el prompt para el reranking
        chunks_text = ""
        for i, chunk in enumerate(chunks):
            chunks_text += f"--- CHUNK ID: {i} ---\n{chunk.content}\n\n"

        prompt = f"""
Eres un experto en análisis de documentos bancarios y seguridad.
Analiza la siguiente pregunta del usuario y los fragmentos de documentos proporcionados.

PREGUNTA DEL USUARIO: "{query}"

FRAGMENTOS DISPONIBLES:
{chunks_text}

TAREA:
1. Evalúa qué tan bien cada fragmento responde a la pregunta.
2. Ordena los CHUNK IDs del más útil al menos útil.
3. Devuelve los resultados estrictamente en formato JSON con la siguiente estructura:
{{
  "ranking": [ID1, ID2, ID3, ...],
  "reasoning": "Breve explicación de por qué el primero es el mejor"
}}

Solo devuelve el JSON, nada de texto extra.
"""

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,  # Baja temperatura para consistencia
                ),
            )

            response_text = response.text or "{}"
            result_json = json.loads(response_text)
            ordered_indices = result_json.get("ranking", [])

            # Re-ordenar la lista original de chunks basada en los índices devueltos
            reranked_chunks: list[StoredChunk] = []
            seen_indices: set[int] = set()

            for raw_idx in ordered_indices:
                idx = int(raw_idx)
                if 0 <= idx < len(chunks) and idx not in seen_indices:
                    chunk = chunks[idx]
                    # Asignamos un score artificial descendente para el ranking
                    chunk.score = 1.0 - (len(reranked_chunks) * 0.1)
                    reranked_chunks.append(chunk)
                    seen_indices.add(idx)

            # Si Gemini omitió algún chunk, los agregamos al final (opcional)
            for i, chunk in enumerate(chunks):
                if i not in seen_indices:
                    chunk.score = 0.0
                    reranked_chunks.append(chunk)

            logger.info(f"Gemini reranking exitoso. Razón: {result_json.get('reasoning')}")
            return reranked_chunks[:top_k]

        except Exception as e:
            logger.error(f"Error en Gemini Reranker: {e}")
            # Fallback al orden original si falla la IA
            return chunks[:top_k]

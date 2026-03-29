import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from google.genai import types
from src.config.settings import settings
from src.infrastructure.database.session import async_session_maker
from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService
from src.infrastructure.rag.retrieval.gemini_reranker import GeminiReranker
from src.infrastructure.rag.retrieval.models import StoredChunk
from src.infrastructure.rag.vector_store.pgvector_store import PgVectorStore


async def test_full_retrieval(query: str):
    print(f"\n🔍 Buscando con Reranking (Gemini): '{query}'")
    print("-" * 60)

    # 1. Embeddings
    embedding_service = GeminiEmbeddingService()
    query_vector = await embedding_service.embed_query(query)

    async with async_session_maker() as session:
        # 2. Búsqueda Híbrida (Aumentamos a 30 para preguntas complejas)
        vector_store = PgVectorStore(session)
        print("🚀 Fase 1: Búsqueda Híbrida (Postgres)...")
        hybrid_results = await vector_store.hybrid_search(
            query_embedding=query_vector, query_text=query, match_count=30
        )

        # Convertir a StoredChunk
        chunks_to_rerank = [
            StoredChunk(
                id=res["id"],
                content=res["content"],
                score=res["score"],
                document_id=res["document_id"],
                chunk_index=res["chunk_index"],
                area=res["area"],
                metadata=res["metadata"],
            )
            for res in hybrid_results
        ]

        # 3. Reranking (Usando Gemini con tu API KEY actual)
        print("🧠 Fase 2: Reranking con Gemini Flash...")
        reranker = GeminiReranker()
        final_results = await reranker.rerank(
            query=query,
            chunks=chunks_to_rerank,
            top_k=5,  # Le pasamos los mejores 5 a la generación
        )

        # DEBUG: Mostrar qué chunks ganaron el reranking
        print("\n📄 Fragmentos seleccionados por la IA:")
        for i, res in enumerate(final_results, 1):
            print(f"   - [{i}] Chunk {res.chunk_index} (Score: {res.score:.2f})")

        # 4. Generación (La respuesta final del RAG)
        print("\n✍️ Fase 3: Generando respuesta final con Gemini...")

        # Unir el contenido de los mejores chunks para el contexto
        context = "\n\n".join([f"Fragmento {i + 1}:\n{res.content}" for i, res in enumerate(final_results)])

        system_prompt = """
Eres un asistente experto de Seguridad e Higiene Industrial.
Tu tarea es responder la pregunta del usuario utilizando UNICAMENTE
la información proporcionada en los fragmentos de documentos adjuntos.

REGLAS:
1. Si la respuesta no está en el contexto, di:
"Lo siento, no encontré información específica en los manuales de seguridad".
2. Mantén un tono profesional y directo.
3. Menciona qué fragmentos usaste para la respuesta.
"""

        user_prompt = f"""
CONTEXTO:
{context}

PREGUNTA: "{query}"

RESPUESTA:
"""

        try:
            # Reutilizamos el cliente de Gemini del reranker o creamos uno rápido
            generation_model = settings.gemini_model_flash
            response = await reranker._client.aio.models.generate_content(
                model=generation_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.2),
            )

            print("\n" + "=" * 60)
            print("🤖 RESPUESTA FINAL DE LA IA:")
            print("=" * 60)
            print(response.text)
            print("=" * 60)

        except Exception as e:
            print(f"❌ Error en la generación: {e}")


if __name__ == "__main__":
    input_query = sys.argv[1] if len(sys.argv) > 1 else "que hacer en caso de derrames quimicos?"
    asyncio.run(test_full_retrieval(input_query))

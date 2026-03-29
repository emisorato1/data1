"""Servicio de memoria episodica para extraer y gestionar recuerdos del usuario."""

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.infrastructure.database.models.episodic_memory import EpisodicMemory
from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService
from src.infrastructure.security.dlp_client import DlpClient

MEMORY_EXTRACTION_PROMPT = """\
Analiza la siguiente conversación entre un humano (User) y un asistente de IA (Assistant).
Tu objetivo es extraer hechos clave, preferencias, contexto laboral o instrucciones
explícitas sobre el usuario para recordarlas a largo plazo.

Tipos de recuerdos válidos:
- preferencia_usuario: Gustos, disgustos, formatos preferidos.
- hecho_mencionado: Información personal o profesional.
- contexto_laboral: Detalles del trabajo, roles, proyectos actuales.
- instruccion_explicita: Reglas que el usuario pidió seguir.

Instrucciones:
1. Extrae únicamente los recuerdos que encajen en las categorías mencionadas.
2. Resume el contenido del recuerdo de forma concisa y en tercera persona.
3. Asigna un score de confianza (0.0 a 1.0) indicando qué tan seguro estás de que
   esto es un recuerdo permanente útil.
4. Si no hay nada relevante para recordar, retorna una lista vacía.
5. NUNCA incluyas datos personales sensibles (PII) en los recuerdos:
   - No incluyas números de DNI, CUIT, CUIL, CBU, tarjetas de crédito ni cuentas bancarias.
   - No incluyas direcciones de email, números de teléfono ni direcciones postales.
   - Si el usuario menciona PII, omítelo del recuerdo o reemplázalo con una referencia
     genérica (ej. "El usuario mencionó su número de documento" en vez del número real).

Conversación:
{conversation}
"""


class ExtractedMemory(BaseModel):
    """Estructura de un recuerdo extraído."""

    memory_type: str = Field(
        description="Tipo de recuerdo: preferencia_usuario, hecho_mencionado, contexto_laboral, o instruccion_explicita"
    )
    content: str = Field(description="Resumen claro y conciso del recuerdo")
    confidence: float = Field(description="Confianza en la relevancia y precisión del recuerdo (0.0 a 1.0)")


class MemoryExtractionResult(BaseModel):
    """Resultado de la extracción de memoria."""

    memories: list[ExtractedMemory]


class MemoryService:
    """Servicio para la extracción y gestión de memorias episódicas."""

    def __init__(self, session: AsyncSession, embedding_service: GeminiEmbeddingService) -> None:
        """Inicializa el servicio."""
        self._session = session
        self._embedding_service = embedding_service
        self._llm = GeminiClient(model=GeminiModel.FLASH)
        self._dlp = DlpClient(
            project_id=settings.gcp_project_id,
            dlp_enabled=settings.dlp_enabled,
            min_likelihood=settings.dlp_min_likelihood,
        )

    async def extract_and_store_memories(self, user_id: int, conversation_history: list[dict[str, Any]]) -> None:
        """Extrae recuerdos de la conversación y los almacena en la base de datos."""
        formatted_history = "\n".join(
            f"{msg.get('role', 'unknown').capitalize()}: {msg.get('content', '')}" for msg in conversation_history
        )

        prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=formatted_history)

        result: MemoryExtractionResult = await self._llm.generate_structured(
            prompt=prompt, schema=MemoryExtractionResult
        )

        valid_memories = [m for m in result.memories if m.confidence > 0.7]

        for mem in valid_memories:
            sanitized = await self._dlp.sanitize(mem.content)
            mem.content = sanitized.sanitized_text
            await self._store_memory(user_id, mem)

    async def _store_memory(self, user_id: int, extracted_memory: ExtractedMemory) -> None:
        """Verifica duplicados usando embeddings y almacena si es nuevo."""
        valid_types = {"preferencia_usuario", "hecho_mencionado", "contexto_laboral", "instruccion_explicita"}
        if extracted_memory.memory_type not in valid_types:
            return

        content = extracted_memory.content
        embedding = await self._embedding_service.embed_query(content)

        # Búsqueda de similitud para deduplicación (> 0.9 cosine)
        # max_inner_product corresponde a cosine distance inverso en vectores normalizados,
        # pero cosine_distance es < 0.1
        # Usamos cosine distance en pgvector -> 1 - cosine_similarity
        distance_threshold = 1.0 - settings.memory_dedup_threshold

        stmt = (
            select(EpisodicMemory)
            .where(EpisodicMemory.user_id == user_id)
            .where(EpisodicMemory.embedding.cosine_distance(embedding) < distance_threshold)
            .limit(1)
        )

        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Podríamos actualizar el last_accessed o algo, pero para la spec evitamos duplicar.
            return

        new_memory = EpisodicMemory(
            user_id=user_id,
            memory_type=extracted_memory.memory_type,
            content=content,
            embedding=embedding,
            confidence=extracted_memory.confidence,
        )
        self._session.add(new_memory)

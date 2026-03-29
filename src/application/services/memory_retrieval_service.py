"""Servicio para buscar recuerdos episódicos del usuario."""

import logging
from typing import Any

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.infrastructure.database.models.episodic_memory import EpisodicMemory

logger = logging.getLogger(__name__)


class MemoryRetrievalService:
    """Servicio para buscar recuerdos del usuario."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_memories(
        self,
        user_id: int,
        query_embedding: list[float],
        top_k: int = settings.memory_top_k,
        threshold: float = settings.memory_retrieval_threshold,
    ) -> list[dict[str, Any]]:
        """Busca los recuerdos más relevantes y actualiza last_accessed.

        Filtra aquellos cuya similitud coseno es menor al umbral.
        """
        # Calcular similitud coseno (pgvector: 1 - cosine_distance)
        similarity_expr = 1 - EpisodicMemory.embedding.cosine_distance(query_embedding)

        stmt = (
            select(EpisodicMemory, similarity_expr.label("similarity"))
            .where(EpisodicMemory.user_id == user_id)
            .where(similarity_expr >= threshold)
            .order_by(EpisodicMemory.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        if not rows:
            logger.info("memory_retrieval: No se encontraron recuerdos relevantes para user_id=%s", user_id)
            return []

        memories = []
        memory_ids = []

        for row in rows:
            memory: EpisodicMemory = row[0]
            similarity: float = row[1]
            memories.append(
                {
                    "id": str(memory.id),
                    "content": memory.content,
                    "memory_type": memory.memory_type,
                    "similarity": similarity,
                }
            )
            memory_ids.append(memory.id)

        # Actualizar last_accessed
        if memory_ids:
            update_stmt = (
                update(EpisodicMemory).where(EpisodicMemory.id.in_(memory_ids)).values(last_accessed=text("now()"))
            )
            await self.session.execute(update_stmt)
            await self.session.commit()

        logger.info(
            "memory_retrieval: Encontrados %d recuerdos para user_id=%s (threshold=%f)",
            len(memories),
            user_id,
            threshold,
        )

        return memories

"""Servicio para resolver membresías de grupos recursivamente con CTE."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class GroupResolver:
    """Resuelve la membresía transitiva de grupos de OpenText.

    Utiliza Common Table Expressions (CTE) recursivas en PostgreSQL
    para explorar el árbol de grupos desde la base hacia arriba.
    Incluye protección contra ciclos en la jerarquía (max_depth).
    """

    def __init__(self, db_session: AsyncSession) -> None:
        """Inicializa el resolver con una sesión de base de datos."""
        self.db = db_session

    async def resolve_all_groups(self, user_id: int, max_depth: int = 10) -> set[int]:
        """Obtiene todos los IDs de grupos a los que pertenece el usuario.

        Incluye grupos directos y grupos heredados por membresía anidada.

        Args:
            user_id: ID del usuario (KUAF.ID).
            max_depth: Profundidad máxima para prevenir ciclos infinitos.

        Returns:
            Un conjunto (set) de group_ids.
        """
        # CTE Recursiva en PostgreSQL
        # Parte base: grupos a los que el usuario pertenece directamente (child_id = user_id)
        # Parte recursiva: grupos que contienen a los grupos encontrados en el nivel anterior
        query = text(
            """
            WITH RECURSIVE group_hierarchy AS (
                -- Caso base: Membresías directas del usuario
                SELECT group_id, child_id, 1 as depth
                FROM kuafchildren
                WHERE child_id = :user_id

                UNION ALL

                -- Paso recursivo: Grupos que son padres de los grupos actuales
                SELECT kc.group_id, kc.child_id, gh.depth + 1
                FROM kuafchildren kc
                JOIN group_hierarchy gh ON kc.child_id = gh.group_id
                WHERE gh.depth < :max_depth
            )
            SELECT DISTINCT group_id
            FROM group_hierarchy;
            """
        )

        try:
            result = await self.db.execute(query, {"user_id": user_id, "max_depth": max_depth})
        except Exception:
            logger.exception("Error resolving groups for user_id=%s", user_id)
            return set()

        group_ids = {row[0] for row in result.all()}
        logger.debug("Resolved %d groups for user_id=%s", len(group_ids), user_id)
        return group_ids

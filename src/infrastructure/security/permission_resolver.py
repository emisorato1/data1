"""Servicio de resolución de permisos basado en el Security Mirror."""

import logging
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.security.group_resolver import GroupResolver
from src.infrastructure.security.permission_cache import PermissionCache

logger = logging.getLogger(__name__)


class PermissionResolver:
    """Validador de permisos de usuario contra el Espejo de Seguridad.

    Usa la vista materializada kuaf_membership_flat o GroupResolver CTE
    para resolver membresía y Redis para cachear consultas frecuentes y reducir latencia.
    """

    def __init__(self, db_session: AsyncSession, cache: PermissionCache) -> None:
        """Inicializa el resolver con sesión de BD y cliente de caché."""
        self.db = db_session
        self.cache = cache
        self.group_resolver = GroupResolver(db_session)

    async def can_access(self, user_id: int, document_id: int, use_cte: bool = False) -> bool:
        """Verifica si el usuario tiene permiso (See Contents) al documento."""
        try:
            cached = await self.cache.get_can_access(user_id, document_id)
            if cached is not None:
                return cached
        except Exception as e:
            logger.warning(f"Error accediendo a caché Redis para can_access: {e}")

        if use_cte:
            groups = await self.group_resolver.resolve_all_groups(user_id)
            all_rights = [*list(groups), user_id]
            query = text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM dtreeacl acl
                    WHERE acl.data_id = :document_id
                      AND acl.right_id = ANY(:rights)
                      AND (acl.permissions & 2) = 2
                )
                """
            )
            result = await self.db.execute(query, {"document_id": document_id, "rights": all_rights})
            has_access = bool(result.scalar())
        else:
            query = text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM dtreeacl acl
                    JOIN kuaf_membership_flat f ON acl.right_id = f.group_id
                    WHERE f.member_id = :user_id
                      AND acl.data_id = :document_id
                      AND (acl.permissions & 2) = 2
                )
                """
            )
            result = await self.db.execute(query, {"user_id": user_id, "document_id": document_id})
            has_access = bool(result.scalar())

        try:
            await self.cache.set_can_access(user_id, document_id, has_access)
        except Exception as e:
            logger.warning(f"Error seteando caché Redis para can_access: {e}")

        return has_access

    async def get_accessible_document_ids(self, user_id: int, use_cte: bool = False) -> Sequence[int]:
        """Obtiene la lista de documentos accesibles para un usuario."""
        try:
            cached_docs = await self.cache.get_accessible_document_ids(user_id)
            if cached_docs is not None:
                return cached_docs
        except Exception as e:
            logger.warning(f"Error accediendo a caché Redis para documentos: {e}")

        if use_cte:
            groups = await self.group_resolver.resolve_all_groups(user_id)
            all_rights = [*list(groups), user_id]
            query = text(
                """
                SELECT DISTINCT acl.data_id
                FROM dtreeacl acl
                WHERE acl.right_id = ANY(:rights)
                  AND (acl.permissions & 2) = 2
                """
            )
            result = await self.db.execute(query, {"rights": all_rights})
            doc_ids = [row[0] for row in result.all()]
        else:
            query = text(
                """
                SELECT DISTINCT acl.data_id
                FROM dtreeacl acl
                JOIN kuaf_membership_flat f ON acl.right_id = f.group_id
                WHERE f.member_id = :user_id
                  AND (acl.permissions & 2) = 2
                """
            )
            result = await self.db.execute(query, {"user_id": user_id})
            doc_ids = [row[0] for row in result.all()]

        try:
            await self.cache.set_accessible_document_ids(user_id, doc_ids)
        except Exception as e:
            logger.warning(f"Error seteando caché Redis para documentos: {e}")

        return doc_ids

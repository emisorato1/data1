import json
from datetime import timedelta

from redis.asyncio import Redis

from src.config.settings import settings


class PermissionCache:
    """Caché de permisos basada en Redis."""

    def __init__(self, redis_client: Redis | None = None) -> None:
        """Inicializa la caché. Si no se provee cliente, usa la URL de settings."""
        self.redis = redis_client or Redis.from_url(settings.redis_url.get_secret_value(), decode_responses=True)
        self.default_ttl = timedelta(minutes=5)

    def _get_user_docs_key(self, user_id: int) -> str:
        return f"perm:user:{user_id}:docs"

    def _get_user_doc_access_key(self, user_id: int, document_id: int | str) -> str:
        return f"perm:user:{user_id}:doc:{document_id}"

    async def get_accessible_document_ids(self, user_id: int) -> list[int] | None:
        """Obtiene la lista de IDs accesibles para un usuario desde la caché."""
        key = self._get_user_docs_key(user_id)
        data = await self.redis.get(key)
        if data is not None:
            return [int(doc_id) for doc_id in json.loads(data)]
        return None

    async def set_accessible_document_ids(
        self, user_id: int, document_ids: list[int], ttl: timedelta | None = None
    ) -> None:
        """Guarda la lista de IDs accesibles para un usuario en la caché."""
        key = self._get_user_docs_key(user_id)
        expiry = ttl or self.default_ttl
        await self.redis.set(key, json.dumps(document_ids), ex=expiry)

    async def get_can_access(self, user_id: int, document_id: int) -> bool | None:
        """Verifica si el acceso a un documento está cacheado."""
        key = self._get_user_doc_access_key(user_id, document_id)
        val = await self.redis.get(key)
        if val is not None:
            return str(val) == "1"
        return None

    async def set_can_access(
        self, user_id: int, document_id: int, has_access: bool, ttl: timedelta | None = None
    ) -> None:
        """Cachea el resultado de acceso a un documento específico."""
        key = self._get_user_doc_access_key(user_id, document_id)
        expiry = ttl or self.default_ttl
        val = "1" if has_access else "0"
        await self.redis.set(key, val, ex=expiry)

    async def invalidate_user(self, user_id: int) -> None:
        """Invalida toda la caché de permisos de un usuario."""
        # Borra lista de documentos
        await self.redis.delete(self._get_user_docs_key(user_id))

        # Borra accesos específicos
        pattern = self._get_user_doc_access_key(user_id, "*")
        cursor = 0
        while True:
            cursor_res, keys = await self.redis.scan(cursor=cursor, match=pattern)
            if keys:
                await self.redis.delete(*keys)
            cursor = int(cursor_res)
            if cursor == 0:
                break

    async def close(self) -> None:
        """Cierra la conexión con Redis."""
        await self.redis.close()

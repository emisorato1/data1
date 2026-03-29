import hashlib
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.audit_log import AuditLogEntry
from src.infrastructure.database.models.audit import AuditLog


class AuditService:
    """Servicio de auditoria forense con hash chain SHA-256."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_latest_hash(self) -> str:
        """Obtiene el hash_chain del ultimo registro o el genesis si no hay."""
        stmt = select(AuditLog.hash_chain).order_by(AuditLog.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        latest_hash = result.scalar()
        if not latest_hash:
            return hashlib.sha256(b"genesis_hash_enterprise_ai_platform").hexdigest()
        return latest_hash

    def _calculate_hash(self, entry: AuditLogEntry, previous_hash: str) -> str:
        """Calcula SHA-256 de (entry_data + previous_hash)."""
        data_to_hash = {
            "actor_id": entry.actor_id,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "details_json": entry.details_json,
            "status": entry.status,
            "timestamp": entry.timestamp.isoformat(),
        }
        # Serialize dict with sorted keys to ensure deterministic representation
        entry_data_str = json.dumps(data_to_hash, sort_keys=True, default=str)
        hash_input = f"{entry_data_str}{previous_hash}"
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    async def log(self, entry: AuditLogEntry) -> AuditLog:
        """Registra un evento de auditoria y calcula la cadena de hash de forma inmutable."""
        previous_hash = await self._get_latest_hash()
        new_hash = self._calculate_hash(entry, previous_hash)

        audit_log = AuditLog(
            user_id=entry.actor_id,
            session_id=entry.session_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            old_value=entry.old_value,
            new_value=entry.new_value,
            details=entry.details_json,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            request_id=entry.request_id,
            status=entry.status,
            error_message=entry.error_message,
            hash_chain=new_hash,
            created_at=entry.timestamp,
        )

        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        return audit_log

    async def verify_chain(self) -> bool:
        """Valida criptograficamente la hash chain de todos los logs."""
        stmt = select(AuditLog).order_by(AuditLog.created_at.asc())
        result = await self.session.execute(stmt)
        logs = result.scalars().all()

        current_hash = hashlib.sha256(b"genesis_hash_enterprise_ai_platform").hexdigest()

        for log in logs:
            entry_model = AuditLogEntry(
                id=log.id,
                actor_id=log.user_id,
                session_id=log.session_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                old_value=log.old_value,
                new_value=log.new_value,
                details_json=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                request_id=log.request_id,
                status=log.status,
                error_message=log.error_message,
                hash_chain=log.hash_chain,
                timestamp=log.created_at,
            )
            expected_hash = self._calculate_hash(entry_model, current_hash)
            if expected_hash != log.hash_chain:
                return False
            current_hash = expected_hash

        return True

    async def get_logs(self, limit: int = 50, offset: int = 0) -> list[AuditLog]:
        """Obtiene logs para admin paginado."""
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

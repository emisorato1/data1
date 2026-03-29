import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

from src.application.services.audit_service import AuditService
from src.domain.entities.audit_log import AuditLogEntry
from src.infrastructure.database.models.audit import AuditLog


async def run():
    mock_session = AsyncMock()
    audit_service = AuditService(mock_session)
    genesis = "087c9f6d33f20d20ef37d159e4b95f190e21ea5c1fc182b8a3e74288075f7823"
    log1 = AuditLog(
        id="00000000-0000-0000-0000-000000000001",
        user_id=1,
        action="login",
        status="success",
        created_at=datetime(2026, 3, 6, 12, 0, 0),
        details={},
    )
    entry1 = AuditLogEntry(
        id=log1.id,
        actor_id=log1.user_id,
        action=log1.action,
        status=log1.status,
        timestamp=log1.created_at,
        details_json=log1.details,
    )
    hash1 = audit_service._calculate_hash(entry1, genesis)
    log1.hash_chain = hash1

    entry_model = AuditLogEntry(
        id=log1.id,
        actor_id=log1.user_id,
        session_id=log1.session_id,
        action=log1.action,
        resource_type=log1.resource_type,
        resource_id=log1.resource_id,
        old_value=log1.old_value,
        new_value=log1.new_value,
        details_json=log1.details,
        ip_address=log1.ip_address,
        user_agent=log1.user_agent,
        request_id=log1.request_id,
        status=log1.status,
        error_message=log1.error_message,
        hash_chain=log1.hash_chain,
        timestamp=log1.created_at,
    )
    expected_hash = audit_service._calculate_hash(entry_model, genesis)
    print("Hash1:", hash1)
    print("Expected:", expected_hash)


asyncio.run(run())

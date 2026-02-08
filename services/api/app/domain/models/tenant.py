from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums.tenant_status import TenantStatus


@dataclass(frozen=True)
class Tenant:
    id: UUID
    name: str
    status: TenantStatus
    created_at: datetime

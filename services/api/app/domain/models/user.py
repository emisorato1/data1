from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    tenant_id: UUID
    role_id: UUID
    is_active: bool
    created_at: datetime
    auth_provider: str = "local"
    google_id: str | None = None
    avatar_url: str | None = None
    full_name: str | None = None
    updated_at: datetime | None = None

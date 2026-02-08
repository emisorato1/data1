from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.infrastructure.db.orm.tenant import TenantORM
from app.domain.enums.role_name import RoleName
from app.infrastructure.db.orm.role import RoleORM


async def seed_defaults(db: AsyncSession) -> None:
    for role_name in (RoleName.PUBLIC.value, RoleName.PRIVATE.value, RoleName.ADMIN.value):
        stmt = select(RoleORM).where(RoleORM.name == role_name)
        exists = (await db.execute(stmt)).scalar_one_or_none()
        if not exists:
            db.add(RoleORM(name=role_name, scopes=[]))
    await db.commit()



DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

async def seed_default_tenant(db: AsyncSession) -> None:
    stmt = select(TenantORM).where(TenantORM.id == DEFAULT_TENANT_ID)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return

    db.add(
        TenantORM(
            id=DEFAULT_TENANT_ID,
            name="default",
            status="active",  # ajustá a tu enum/valores reales
        )
    )
    await db.commit()

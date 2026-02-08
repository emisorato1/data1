from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.orm.role import RoleORM


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> RoleORM | None:
        stmt = select(RoleORM).where(RoleORM.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_if_not_exists(self, *, name: str, scopes: list[str] | None = None) -> RoleORM:
        existing = await self.get_by_name(name)
        if existing:
            return existing

        role = RoleORM(name=name, scopes=scopes or [])
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
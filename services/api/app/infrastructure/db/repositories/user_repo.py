from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.orm.user import UserORM


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> UserORM | None:
        stmt = (
            select(UserORM)
            .options(selectinload(UserORM.role))
            .where(UserORM.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> UserORM | None:
        stmt = (
            select(UserORM)
            .options(selectinload(UserORM.role))
            .where(UserORM.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> UserORM | None:
        """Get user by Google OAuth ID."""
        stmt = (
            select(UserORM)
            .options(selectinload(UserORM.role))
            .where(UserORM.google_id == google_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        password_hash: str | None,
        tenant_id: UUID,
        role_id: UUID,
        auth_provider: str = "local",
        google_id: str | None = None,
        avatar_url: str | None = None,
        full_name: str | None = None,
    ) -> UserORM:
        user = UserORM(
            email=email,
            password_hash=password_hash,
            tenant_id=tenant_id,
            role_id=role_id,
            is_active=True,
            auth_provider=auth_provider,
            google_id=google_id,
            avatar_url=avatar_url,
            full_name=full_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        loaded = await self.get_by_id(user.id)
        assert loaded is not None
        return loaded

    async def update_google_info(
        self,
        user_id: UUID,
        *,
        google_id: str,
        avatar_url: str | None = None,
        full_name: str | None = None,
    ) -> UserORM | None:
        """Link Google account to existing user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        user.google_id = google_id
        user.auth_provider = "google" if user.password_hash is None else user.auth_provider
        if avatar_url:
            user.avatar_url = avatar_url
        if full_name:
            user.full_name = full_name

        await self.db.commit()
        await self.db.refresh(user)
        return user
import asyncio

from app.infrastructure.db.session import AsyncSessionLocal
from app.infrastructure.db.repositories.role_repo import RoleRepository
from app.domain.enums.role_name import RoleName


async def main():
    async with AsyncSessionLocal() as db:
        repo = RoleRepository(db)
        await repo.create_if_not_exists(name=RoleName.PUBLIC.value, scopes=["chat:read"])
        await repo.create_if_not_exists(name=RoleName.PRIVATE.value, scopes=["chat:read", "chat:write"])
        await repo.create_if_not_exists(name=RoleName.ADMIN.value, scopes=["*"])
    print("roles seeded")


if __name__ == "__main__":
    asyncio.run(main())
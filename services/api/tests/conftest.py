"""
Pytest configuration and fixtures for API tests.
"""
import asyncio
from typing import AsyncGenerator, Generator
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import get_db
from app.infrastructure.db.orm.role import RoleORM
from app.infrastructure.db.orm.tenant import TenantORM


# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Test session factory
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # Seed test data
        await _seed_test_data(session)
        yield session

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _seed_test_data(session: AsyncSession) -> None:
    """Seed required test data."""
    # Create default tenant
    tenant = TenantORM(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Tenant",
        status="active",
    )
    session.add(tenant)

    # Create roles
    roles = [
        RoleORM(
            id=UUID("00000000-0000-0000-0000-000000000010"),
            name="public",
            scopes=["read:public"],
        ),
        RoleORM(
            id=UUID("00000000-0000-0000-0000-000000000011"),
            name="private",
            scopes=["read:public", "read:private"],
        ),
        RoleORM(
            id=UUID("00000000-0000-0000-0000-000000000012"),
            name="admin",
            scopes=["read:public", "read:private", "admin"],
        ),
    ]
    session.add_all(roles)
    await session.commit()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# Mock Google user data for testing
MOCK_GOOGLE_USER = {
    "id": "google-user-123456",
    "email": "testuser@example.com",
    "verified_email": True,
    "name": "Test User",
    "given_name": "Test",
    "family_name": "User",
    "picture": "https://example.com/photo.jpg",
}

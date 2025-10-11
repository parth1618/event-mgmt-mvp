"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator  # noqa: UP035

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.security import get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models.user import User

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database and session."""
    # Create engine
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def client(test_db: AsyncSession) -> TestClient:  # type: ignore
    """Create test client with database override."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Test User",
        role="attendee",
        is_active=True,
        is_verified=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_organizer(test_db: AsyncSession) -> User:
    """Create test organizer."""
    organizer = User(
        email="organizer@example.com",
        hashed_password=get_password_hash("OrganizerPass123!"),
        full_name="Test Organizer",
        role="organizer",
        is_active=True,
        is_verified=True,
    )
    test_db.add(organizer)
    await test_db.commit()
    await test_db.refresh(organizer)
    return organizer


@pytest.fixture
async def test_admin(test_db: AsyncSession) -> User:
    """Create test admin."""
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Test Admin",
        role="admin",
        is_active=True,
        is_verified=True,
    )
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "TestPass123!"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

"""Test configuration and fixtures.

This file contains shared test fixtures used across different test types:
- Database fixtures for integration tests
- FastAPI test client for API tests
"""

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.deps import get_session
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        # Clean up all tables before each test
        async with session.begin():
            for table in reversed(SQLModel.metadata.sorted_tables):
                await session.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

        yield session

        # Rollback any pending transactions
        await session.rollback()
        # Clean up all tables after each test
        async with session.begin():
            for table in reversed(SQLModel.metadata.sorted_tables):
                await session.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))


@pytest.fixture
def test_client(test_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create a test client with the test database session."""

    # Override the get_session dependency
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    # Create test client using context manager for proper cleanup
    with TestClient(app) as client:
        yield client

    # Clear dependency overrides
    app.dependency_overrides.clear()

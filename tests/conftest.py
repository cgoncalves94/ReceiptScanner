"""Test configuration and fixtures.

This file contains shared test fixtures used across different test types:
- Database fixtures for integration tests
- FastAPI test client for API tests
"""

import os
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

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

from app.core.deps import get_session
from app.main import app


def get_test_database_url() -> str:
    """Build test database URL from environment variables.

    This reads directly from env vars (set by pytest-dotenv from .env.test)
    instead of using the settings singleton which may have cached .env values.
    """
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db = os.getenv("POSTGRES_DB", "receipt_analyzer")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine]:
    """Create a test database engine."""
    engine = create_async_engine(
        get_test_database_url(),
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
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
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
def test_client(
    test_session: AsyncSession, test_engine: AsyncEngine
) -> Generator[TestClient]:
    """Create a test client with the test database session.

    Patches lifespan to use test engine and session instead of the app's
    default engine which connects to the Docker hostname.
    """

    # Override the get_session dependency
    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    # Patch lifespan deps to use test engine (avoids connecting to 'db' host)
    with (
        patch("app.main.init_db", AsyncMock()),
        patch("app.main.engine", test_engine),
    ):
        # Create test client using context manager for proper cleanup
        with TestClient(app) as client:
            yield client

    # Clear dependency overrides
    app.dependency_overrides.clear()

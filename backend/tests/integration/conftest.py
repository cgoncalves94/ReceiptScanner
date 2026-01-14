"""Integration test fixtures.

This conftest provides database fixtures for integration tests only.
Unit tests should NOT use these fixtures - they should mock dependencies instead.

Key design decisions:
1. Session-scoped engine: Tables created once per test run (fast)
2. Transaction rollback isolation: Each test runs in a transaction that gets
   rolled back, providing test isolation without TRUNCATE (faster)
3. Nested transactions: Using savepoints so tests can have their own transactions

References:
- https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
- https://fastapi.tiangolo.com/how-to/testing-database/
"""

import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    create_async_engine,
)
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.models import User
from app.auth.utils import create_access_token, hash_password
from app.category.models import Category
from app.core.config import settings
from app.core.deps import get_session
from app.main import app
from app.receipt.models import Receipt, ReceiptItem


def get_test_database_url() -> str:
    """Build test database URL from environment variables.

    Reads directly from env vars (set by pytest-dotenv from .env.test)
    instead of using the settings singleton which may have cached .env values.

    Requires .env.test to be present with all POSTGRES_* variables defined.
    """
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db = os.environ["POSTGRES_DB"]
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


# =============================================================================
# Filesystem Isolation Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def test_uploads_dir() -> Generator[Path]:
    """Create a temporary directory for file uploads during tests.

    This prevents test files from accumulating in the real uploads/ directory.
    The temp directory is automatically cleaned up after the test session.
    """
    with tempfile.TemporaryDirectory(prefix="receipt_test_uploads_") as tmp_dir:
        yield Path(tmp_dir)


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine]:
    """Create a test database engine (session-scoped).

    Creates all tables once at the start of the test session,
    drops them at the end. This is faster than per-test table creation.
    """
    engine = create_async_engine(
        get_test_database_url(),
        echo=False,
        future=True,
    )

    # Create all tables once
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop all tables at end of session
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_connection(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncConnection]:
    """Create a connection with an outer transaction for test isolation.

    This connection begins a transaction that will be rolled back after
    each test, providing fast isolation without TRUNCATE.
    """
    async with test_engine.connect() as connection:
        # Begin outer transaction (will be rolled back)
        transaction = await connection.begin()

        yield connection

        # Rollback the outer transaction - this undoes all test changes
        await transaction.rollback()


@pytest_asyncio.fixture
async def test_session(
    test_connection: AsyncConnection,
) -> AsyncGenerator[AsyncSession]:
    """Create a test session bound to the test connection.

    Uses nested transactions (savepoints) so the test code can use
    normal transaction semantics while still being rolled back.
    """
    # Create session bound to the connection with join_transaction_mode
    # This ensures the session joins the connection's transaction
    session = AsyncSession(
        bind=test_connection,
        expire_on_commit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )

    async with session:
        yield session
        # No explicit rollback needed - outer transaction handles it


@pytest.fixture
def test_client(
    test_session: AsyncSession,
    test_engine: AsyncEngine,
    test_uploads_dir: Path,
) -> Generator[TestClient]:
    """Create a test client with the test database session.

    Overrides FastAPI's session dependency to use our test session,
    ensuring all requests use the same transaction that will be rolled back.

    Also redirects file uploads to a temp directory to prevent test files
    from accumulating in the real uploads/ directory.
    """

    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    # Store original upload dir
    original_upload_dir = settings.UPLOAD_DIR

    # Patch lifespan and uploads directory
    with (
        patch("app.main.init_db", AsyncMock()),
        patch("app.main.engine", test_engine),
    ):
        # Redirect uploads to temp directory
        settings.UPLOAD_DIR = test_uploads_dir
        try:
            with TestClient(app) as client:
                yield client
        finally:
            # Restore original upload dir
            settings.UPLOAD_DIR = original_upload_dir

    app.dependency_overrides.clear()


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def test_image() -> BytesIO:
    """Create a minimal test image (100x100 white PNG).

    Returns a BytesIO buffer ready to be used in file uploads.
    """
    img = Image.new("RGB", (100, 100), color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


@pytest.fixture
def mock_receipt_analysis() -> dict:
    """Create mock receipt analysis data matching ReceiptAnalysis schema.

    This fixture provides realistic test data that matches what Gemini
    would return when analyzing a receipt image.
    """
    return {
        "store_name": "Test Grocery Store",
        "total_amount": 25.98,
        "currency": "€",
        "date": datetime(2025, 1, 9, 14, 30, 0).isoformat(),
        "items": [
            {
                "name": "Organic Milk",
                "price": 3.99,
                "quantity": 2.0,
                "currency": "€",
                "category": {
                    "name": "Dairy",
                    "description": "Milk, cheese, yogurt and other dairy products",
                },
            },
            {
                "name": "Whole Wheat Bread",
                "price": 2.50,
                "quantity": 1.0,
                "currency": "€",
                "category": {
                    "name": "Bakery",
                    "description": "Bread, pastries, and baked goods",
                },
            },
            {
                "name": "Bananas",
                "price": 1.99,
                "quantity": 1.0,
                "currency": "€",
                "category": {
                    "name": "Fruits",
                    "description": "Fresh fruits and produce",
                },
            },
        ],
    }


# =============================================================================
# Authentication Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession) -> AsyncGenerator[User]:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    yield user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create a JWT access token for the test user."""
    assert test_user.id is not None
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Create authorization headers with the test user's token."""
    return {"Authorization": f"Bearer {auth_token}"}


# =============================================================================
# Entity Fixtures (Database Records)
# =============================================================================


@pytest_asyncio.fixture
async def test_category(
    test_session: AsyncSession, test_user: User
) -> AsyncGenerator[Category]:
    """Create a test category in the database."""
    assert test_user.id is not None
    category = Category(
        name="Test Category",
        description="Test Description",
        user_id=test_user.id,
    )
    test_session.add(category)
    await test_session.commit()
    await test_session.refresh(category)
    yield category


@pytest_asyncio.fixture
async def test_receipt(
    test_session: AsyncSession, test_user: User
) -> AsyncGenerator[Receipt]:
    """Create a test receipt in the database."""
    assert test_user.id is not None
    receipt = Receipt(
        store_name="Test Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
        user_id=test_user.id,
    )
    test_session.add(receipt)
    await test_session.commit()
    await test_session.refresh(receipt)
    yield receipt


@pytest_asyncio.fixture
async def test_receipt_item(
    test_session: AsyncSession,
    test_receipt: Receipt,
    test_category: Category,
) -> AsyncGenerator[ReceiptItem]:
    """Create a test receipt item linked to a receipt and category."""
    assert test_receipt.id is not None
    assert test_category.id is not None
    item = ReceiptItem(
        name="Test Item",
        quantity=2,
        unit_price=Decimal("5.50"),
        total_price=Decimal("11.00"),
        currency="$",
        receipt_id=test_receipt.id,
        category_id=test_category.id,
    )
    test_session.add(item)
    await test_session.commit()
    await test_session.refresh(item)
    yield item


@pytest_asyncio.fixture
async def analytics_test_data(test_session: AsyncSession, test_user: User) -> dict:
    """Create test data for analytics tests.

    Creates a realistic scenario with multiple stores, categories,
    receipts, and items for testing analytics aggregations.
    """
    assert test_user.id is not None

    # Create categories
    groceries = Category(
        name="Groceries", description="Food items", user_id=test_user.id
    )
    electronics = Category(
        name="Electronics", description="Electronic items", user_id=test_user.id
    )
    test_session.add(groceries)
    test_session.add(electronics)
    await test_session.flush()

    # Create receipts for January 2025
    receipt1 = Receipt(
        store_name="Walmart",
        total_amount=Decimal("50.00"),
        currency="EUR",
        purchase_date=datetime(2025, 1, 5),
        image_path="/path/receipt1.jpg",
        user_id=test_user.id,
    )
    receipt2 = Receipt(
        store_name="Target",
        total_amount=Decimal("75.00"),
        currency="EUR",
        purchase_date=datetime(2025, 1, 15),
        image_path="/path/receipt2.jpg",
        user_id=test_user.id,
    )
    receipt3 = Receipt(
        store_name="Walmart",
        total_amount=Decimal("30.00"),
        currency="EUR",
        purchase_date=datetime(2025, 1, 20),
        image_path="/path/receipt3.jpg",
        user_id=test_user.id,
    )
    test_session.add_all([receipt1, receipt2, receipt3])
    await test_session.flush()

    # Assert IDs are set after flush (for type checker)
    assert receipt1.id is not None
    assert receipt2.id is not None
    assert groceries.id is not None
    assert electronics.id is not None

    # Create receipt items
    item1 = ReceiptItem(
        name="Milk",
        quantity=2,
        unit_price=Decimal("3.00"),
        total_price=Decimal("6.00"),
        currency="EUR",
        receipt_id=receipt1.id,
        category_id=groceries.id,
    )
    item2 = ReceiptItem(
        name="Bread",
        quantity=1,
        unit_price=Decimal("2.50"),
        total_price=Decimal("2.50"),
        currency="EUR",
        receipt_id=receipt1.id,
        category_id=groceries.id,
    )
    item3 = ReceiptItem(
        name="USB Cable",
        quantity=1,
        unit_price=Decimal("15.00"),
        total_price=Decimal("15.00"),
        currency="EUR",
        receipt_id=receipt2.id,
        category_id=electronics.id,
    )
    test_session.add_all([item1, item2, item3])
    await test_session.commit()

    return {
        "categories": [groceries, electronics],
        "receipts": [receipt1, receipt2, receipt3],
        "items": [item1, item2, item3],
    }

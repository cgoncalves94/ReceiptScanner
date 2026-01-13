"""Integration tests for analytics endpoints."""

from datetime import datetime
from decimal import Decimal

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.category.models import Category
from app.receipt.models import Receipt, ReceiptItem


@pytest_asyncio.fixture
async def analytics_test_data(test_session: AsyncSession):
    """Create test data for analytics tests."""
    # Create categories
    groceries = Category(name="Groceries", description="Food items")
    electronics = Category(name="Electronics", description="Electronic items")
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
    )
    receipt2 = Receipt(
        store_name="Target",
        total_amount=Decimal("75.00"),
        currency="EUR",
        purchase_date=datetime(2025, 1, 15),
        image_path="/path/receipt2.jpg",
    )
    receipt3 = Receipt(
        store_name="Walmart",
        total_amount=Decimal("30.00"),
        currency="EUR",
        purchase_date=datetime(2025, 1, 20),
        image_path="/path/receipt3.jpg",
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


class TestSummaryEndpoint:
    """Tests for GET /api/v1/analytics/summary."""

    def test_summary_empty_database(self, test_client: TestClient):
        """Test summary returns zeros when database is empty."""
        response = test_client.get("/api/v1/analytics/summary?year=2025&month=1")

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_spent"]) == Decimal("0")
        assert data["receipt_count"] == 0
        assert Decimal(data["avg_per_receipt"]) == Decimal("0")

    def test_summary_with_data(
        self, test_client: TestClient, analytics_test_data: dict
    ):
        """Test summary returns correct totals."""
        response = test_client.get("/api/v1/analytics/summary?year=2025&month=1")

        assert response.status_code == 200
        data = response.json()
        # Total: 50 + 75 + 30 = 155
        assert Decimal(data["total_spent"]) == Decimal("155.00")
        assert data["receipt_count"] == 3
        # Avg: 155 / 3 = 51.67
        assert Decimal(data["avg_per_receipt"]) == Decimal("51.67")

    def test_summary_yearly(self, test_client: TestClient, analytics_test_data: dict):
        """Test summary for entire year (no month filter)."""
        response = test_client.get("/api/v1/analytics/summary?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data["receipt_count"] == 3
        assert data["month"] is None

    def test_summary_invalid_month(self, test_client: TestClient):
        """Test summary rejects invalid month."""
        response = test_client.get("/api/v1/analytics/summary?year=2025&month=13")
        assert response.status_code == 422

    def test_summary_different_year(
        self, test_client: TestClient, analytics_test_data: dict
    ):
        """Test summary returns empty for year with no data."""
        response = test_client.get("/api/v1/analytics/summary?year=2020&month=1")

        assert response.status_code == 200
        data = response.json()
        assert data["receipt_count"] == 0


class TestTrendsEndpoint:
    """Tests for GET /api/v1/analytics/trends."""

    def test_trends_empty_database(self, test_client: TestClient):
        """Test trends returns empty list when no data."""
        response = test_client.get(
            "/api/v1/analytics/trends",
            params={
                "start": "2025-01-01T00:00:00",
                "end": "2025-01-31T23:59:59",
                "period": "daily",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["trends"] == []
        assert data["period"] == "daily"

    def test_trends_with_data(
        self, test_client: TestClient, analytics_test_data: dict
    ):
        """Test trends returns time-series data."""
        response = test_client.get(
            "/api/v1/analytics/trends",
            params={
                "start": "2025-01-01T00:00:00",
                "end": "2025-01-31T23:59:59",
                "period": "daily",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["trends"]) > 0
        # Each trend should have the required fields
        for trend in data["trends"]:
            assert "date" in trend
            assert "total" in trend
            assert "receipt_count" in trend

    def test_trends_monthly_period(
        self, test_client: TestClient, analytics_test_data: dict
    ):
        """Test trends with monthly grouping."""
        response = test_client.get(
            "/api/v1/analytics/trends",
            params={
                "start": "2025-01-01T00:00:00",
                "end": "2025-12-31T23:59:59",
                "period": "monthly",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "monthly"

    def test_trends_missing_required_params(self, test_client: TestClient):
        """Test trends requires start and end dates."""
        response = test_client.get("/api/v1/analytics/trends")
        assert response.status_code == 422


class TestTopStoresEndpoint:
    """Tests for GET /api/v1/analytics/top-stores."""

    def test_top_stores_empty_database(self, test_client: TestClient):
        """Test top-stores returns empty when no data."""
        response = test_client.get("/api/v1/analytics/top-stores?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data["stores"] == []

    def test_top_stores_with_data(
        self, test_client: TestClient, analytics_test_data: dict
    ):
        """Test top-stores returns ranked stores."""
        response = test_client.get("/api/v1/analytics/top-stores?year=2025&month=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["stores"]) == 2  # Walmart and Target

        # Walmart should be first (50 + 30 = 80, vs Target's 75)
        assert data["stores"][0]["store_name"] == "Walmart"
        assert Decimal(data["stores"][0]["total_spent"]) == Decimal("80.00")
        assert data["stores"][0]["visit_count"] == 2

    def test_top_stores_limit(
        self, test_client: TestClient, analytics_test_data: dict
    ):
        """Test top-stores respects limit parameter."""
        response = test_client.get(
            "/api/v1/analytics/top-stores?year=2025&month=1&limit=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["stores"]) == 1

    def test_top_stores_invalid_limit(self, test_client: TestClient):
        """Test top-stores rejects invalid limit."""
        response = test_client.get(
            "/api/v1/analytics/top-stores?year=2025&limit=100"
        )
        assert response.status_code == 422

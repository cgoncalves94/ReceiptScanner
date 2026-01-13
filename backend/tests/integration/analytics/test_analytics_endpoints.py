"""Integration tests for analytics endpoints.

Note: The service now returns data grouped by original currency.
Frontend handles conversion to display currency.
"""

from decimal import Decimal

from fastapi.testclient import TestClient


class TestSummaryEndpoint:
    """Tests for GET /api/v1/analytics/summary."""

    def test_summary_empty_database(self, test_client: TestClient):
        """Test summary returns zeros when database is empty."""
        response = test_client.get("/api/v1/analytics/summary?year=2025&month=1")

        assert response.status_code == 200
        data = response.json()
        assert data["totals_by_currency"] == []
        assert data["receipt_count"] == 0

    def test_summary_with_data(
        self, test_client: TestClient, analytics_test_data: dict
    ):
        """Test summary returns correct totals grouped by currency."""
        response = test_client.get("/api/v1/analytics/summary?year=2025&month=1")

        assert response.status_code == 200
        data = response.json()
        # Test data uses EUR currency
        assert len(data["totals_by_currency"]) == 1
        assert data["totals_by_currency"][0]["currency"] == "EUR"
        # Total: 50 + 75 + 30 = 155
        assert Decimal(data["totals_by_currency"][0]["amount"]) == Decimal("155.00")
        assert data["receipt_count"] == 3

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

    def test_trends_with_data(self, test_client: TestClient, analytics_test_data: dict):
        """Test trends returns time-series data grouped by currency."""
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
            assert "totals_by_currency" in trend
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
        """Test top-stores returns ranked stores with totals by currency."""
        response = test_client.get("/api/v1/analytics/top-stores?year=2025&month=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["stores"]) == 2  # Walmart and Target

        # Walmart should be first (50 + 30 = 80, vs Target's 75)
        assert data["stores"][0]["store_name"] == "Walmart"
        assert len(data["stores"][0]["totals_by_currency"]) == 1
        assert Decimal(data["stores"][0]["totals_by_currency"][0]["amount"]) == Decimal(
            "80.00"
        )
        assert data["stores"][0]["visit_count"] == 2

    def test_top_stores_limit(self, test_client: TestClient, analytics_test_data: dict):
        """Test top-stores respects limit parameter."""
        response = test_client.get(
            "/api/v1/analytics/top-stores?year=2025&month=1&limit=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["stores"]) == 1

    def test_top_stores_invalid_limit(self, test_client: TestClient):
        """Test top-stores rejects invalid limit."""
        response = test_client.get("/api/v1/analytics/top-stores?year=2025&limit=100")
        assert response.status_code == 422

"""Unit tests for the analytics service.

Note: The service now returns data grouped by original currency.
Frontend handles conversion to display currency.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.analytics.services import AnalyticsService


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def analytics_service(mock_session: AsyncMock) -> AnalyticsService:
    """Create an AnalyticsService with mock dependencies."""
    return AnalyticsService(session=mock_session)


@pytest.mark.asyncio
async def test_get_summary_empty_data(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_summary returns empty totals when no data exists."""
    # Arrange - first query returns empty currency groups
    mock_result = MagicMock()
    mock_result.all.return_value = []

    # Category query returns no top category
    mock_category_result = MagicMock()
    mock_category_result.first.return_value = None

    mock_session.exec.side_effect = [mock_result, mock_category_result]

    # Act
    summary = await analytics_service.get_summary(year=2025, month=1)

    # Assert
    assert summary.totals_by_currency == []
    assert summary.receipt_count == 0
    assert summary.top_category is None
    assert summary.top_category_amounts is None
    assert summary.year == 2025
    assert summary.month == 1


@pytest.mark.asyncio
async def test_get_summary_with_data(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_summary returns correct totals grouped by currency."""
    # Arrange - tuples: (currency, total_amount, receipt_count)
    mock_result = MagicMock()
    mock_result.all.return_value = [
        ("EUR", Decimal("100.00"), 4),
    ]

    # Category query returns no top category for simplicity
    mock_category_result = MagicMock()
    mock_category_result.first.return_value = None

    mock_session.exec.side_effect = [mock_result, mock_category_result]

    # Act
    summary = await analytics_service.get_summary(year=2025, month=1)

    # Assert
    assert len(summary.totals_by_currency) == 1
    assert summary.totals_by_currency[0].currency == "EUR"
    assert summary.totals_by_currency[0].amount == Decimal("100.00")
    assert summary.receipt_count == 4


@pytest.mark.asyncio
async def test_get_summary_yearly(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_summary works for yearly data (no month filter)."""
    # Arrange - multiple currencies
    mock_result = MagicMock()
    mock_result.all.return_value = [
        ("EUR", Decimal("1000.00"), 20),
        ("GBP", Decimal("200.00"), 4),
    ]

    mock_category_result = MagicMock()
    mock_category_result.first.return_value = None

    mock_session.exec.side_effect = [mock_result, mock_category_result]

    # Act
    summary = await analytics_service.get_summary(year=2025, month=None)

    # Assert
    assert len(summary.totals_by_currency) == 2
    assert summary.receipt_count == 24  # 20 + 4
    assert summary.month is None


@pytest.mark.asyncio
async def test_get_summary_with_top_category(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_summary returns top category with amounts by currency."""
    # Arrange - main query
    mock_result = MagicMock()
    mock_result.all.return_value = [
        ("EUR", Decimal("500.00"), 10),
    ]

    # Top category query returns category name
    mock_top_cat_result = MagicMock()
    mock_top_cat_result.first.return_value = ("Groceries", Decimal("200.00"))

    # Category currency breakdown query
    mock_cat_currency_result = MagicMock()
    mock_cat_currency_result.all.return_value = [
        ("EUR", Decimal("200.00")),
    ]

    mock_session.exec.side_effect = [
        mock_result,
        mock_top_cat_result,
        mock_cat_currency_result,
    ]

    # Act
    summary = await analytics_service.get_summary(year=2025, month=1)

    # Assert
    assert summary.top_category == "Groceries"
    assert summary.top_category_amounts is not None
    assert len(summary.top_category_amounts) == 1
    assert summary.top_category_amounts[0].currency == "EUR"
    assert summary.top_category_amounts[0].amount == Decimal("200.00")


@pytest.mark.asyncio
async def test_get_trends_empty_data(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_trends returns empty list when no data exists."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    # Act
    start = datetime(2025, 1, 1)
    end = datetime(2025, 1, 31)
    trends = await analytics_service.get_trends(start, end, period="daily")

    # Assert
    assert trends.trends == []
    assert trends.period == "daily"
    assert trends.start_date == start
    assert trends.end_date == end


@pytest.mark.asyncio
async def test_get_trends_with_data(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_trends returns correct trend data grouped by currency."""
    # Arrange - tuples: (period_date, currency, total_amount, receipt_count)
    mock_result = MagicMock()
    mock_result.all.return_value = [
        ("2025-01-01", "EUR", Decimal("50.00"), 2),
        ("2025-01-01", "GBP", Decimal("20.00"), 1),
        ("2025-01-02", "EUR", Decimal("75.00"), 3),
    ]
    mock_session.exec.return_value = mock_result

    # Act
    start = datetime(2025, 1, 1)
    end = datetime(2025, 1, 31)
    trends = await analytics_service.get_trends(start, end, period="daily")

    # Assert
    assert len(trends.trends) == 2  # Two dates

    # First date has EUR + GBP
    day1 = trends.trends[0]
    assert day1.date == "2025-01-01"
    assert len(day1.totals_by_currency) == 2
    assert day1.receipt_count == 3  # 2 + 1

    # Second date has only EUR
    day2 = trends.trends[1]
    assert day2.date == "2025-01-02"
    assert len(day2.totals_by_currency) == 1
    assert day2.totals_by_currency[0].currency == "EUR"
    assert day2.totals_by_currency[0].amount == Decimal("75.00")


@pytest.mark.asyncio
async def test_get_top_stores_empty(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_top_stores returns empty list when no data."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    # Act
    result = await analytics_service.get_top_stores(year=2025)

    # Assert
    assert result.stores == []
    assert result.year == 2025


@pytest.mark.asyncio
async def test_get_top_stores_with_data(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_top_stores returns stores with totals by currency."""
    # Arrange - first query returns top stores
    mock_top_stores_result = MagicMock()
    mock_top_stores_result.all.return_value = [
        ("Store A", Decimal("200.00")),
        ("Store B", Decimal("150.00")),
    ]

    # Detail queries for each store: (currency, visit_count, total_spent)
    mock_detail_a = MagicMock()
    mock_detail_a.all.return_value = [("EUR", 5, Decimal("200.00"))]

    mock_detail_b = MagicMock()
    mock_detail_b.all.return_value = [("EUR", 3, Decimal("150.00"))]

    mock_session.exec.side_effect = [
        mock_top_stores_result,
        mock_detail_a,
        mock_detail_b,
    ]

    # Act
    result = await analytics_service.get_top_stores(year=2025, limit=10)

    # Assert
    assert len(result.stores) == 2
    assert result.stores[0].store_name == "Store A"
    assert result.stores[0].visit_count == 5
    assert len(result.stores[0].totals_by_currency) == 1
    assert result.stores[0].totals_by_currency[0].amount == Decimal("200.00")


@pytest.mark.asyncio
async def test_get_top_stores_with_month_filter(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_top_stores filters by month."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    # Act
    result = await analytics_service.get_top_stores(year=2025, month=1)

    # Assert
    assert result.month == 1
    assert result.stores == []


@pytest.mark.asyncio
async def test_get_category_breakdown_empty(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_category_breakdown returns empty when no data."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    # Act
    result = await analytics_service.get_category_breakdown(year=2025, month=1)

    # Assert
    assert result.categories == []
    assert result.totals_by_currency == []


@pytest.mark.asyncio
async def test_get_category_breakdown_with_data(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_category_breakdown returns categories grouped by currency."""
    # Arrange - tuples: (category_id, category_name, currency, item_count, category_total)
    mock_result = MagicMock()
    mock_result.all.return_value = [
        (1, "Groceries", "EUR", 8, Decimal("80.00")),
        (1, "Groceries", "GBP", 2, Decimal("20.00")),
        (2, "Electronics", "EUR", 5, Decimal("50.00")),
    ]
    mock_session.exec.return_value = mock_result

    # Act
    result = await analytics_service.get_category_breakdown(year=2025)

    # Assert
    assert len(result.categories) == 2

    # Groceries has two currencies
    groceries = result.categories[0]
    assert groceries.category_id == 1
    assert groceries.category_name == "Groceries"
    assert groceries.item_count == 10  # 8 + 2
    assert len(groceries.totals_by_currency) == 2

    # Electronics has one currency
    electronics = result.categories[1]
    assert electronics.category_id == 2
    assert electronics.item_count == 5

    # Overall totals
    assert len(result.totals_by_currency) == 2  # EUR and GBP

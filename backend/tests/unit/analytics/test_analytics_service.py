"""Unit tests for the analytics service."""

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
    """Test get_summary returns zeros when no data exists."""
    # Arrange - mock exec() to return tuple results
    mock_result = MagicMock()
    mock_result.one.return_value = (None, 0)  # (total_amount, receipt_count)

    mock_category_result = MagicMock()
    mock_category_result.first.return_value = None

    mock_session.exec.side_effect = [mock_result, mock_category_result]

    # Act
    summary = await analytics_service.get_summary(year=2025, month=1)

    # Assert
    assert summary.total_spent == Decimal("0")
    assert summary.receipt_count == 0
    assert summary.avg_per_receipt == Decimal("0")
    assert summary.top_category is None
    assert summary.year == 2025
    assert summary.month == 1


@pytest.mark.asyncio
async def test_get_summary_with_data(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_summary returns correct calculations."""
    # Arrange - tuples: (total_amount, receipt_count)
    mock_result = MagicMock()
    mock_result.one.return_value = (Decimal("100.00"), 4)

    mock_category_result = MagicMock()
    mock_category_result.first.return_value = None

    mock_session.exec.side_effect = [mock_result, mock_category_result]

    # Act
    summary = await analytics_service.get_summary(year=2025, month=1)

    # Assert
    assert summary.total_spent == Decimal("100.00")
    assert summary.receipt_count == 4
    assert summary.avg_per_receipt == Decimal("25.00")


@pytest.mark.asyncio
async def test_get_summary_yearly(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_summary works for yearly data (no month filter)."""
    # Arrange
    mock_result = MagicMock()
    mock_result.one.return_value = (Decimal("1200.00"), 24)

    mock_category_result = MagicMock()
    mock_category_result.first.return_value = None

    mock_session.exec.side_effect = [mock_result, mock_category_result]

    # Act
    summary = await analytics_service.get_summary(year=2025, month=None)

    # Assert
    assert summary.total_spent == Decimal("1200.00")
    assert summary.receipt_count == 24
    assert summary.month is None


@pytest.mark.asyncio
async def test_get_summary_with_top_category(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_summary returns top category when data exists."""
    # Arrange
    mock_result = MagicMock()
    mock_result.one.return_value = (Decimal("500.00"), 10)

    mock_category_result = MagicMock()
    # Tuple: (category_name, category_total)
    mock_category_result.first.return_value = ("Groceries", Decimal("200.00"))

    mock_session.exec.side_effect = [mock_result, mock_category_result]

    # Act
    summary = await analytics_service.get_summary(year=2025, month=1)

    # Assert
    assert summary.top_category == "Groceries"
    assert summary.top_category_amount == Decimal("200.00")


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
    """Test get_trends returns correct trend data."""
    # Arrange - tuples: (period_date, total_amount, receipt_count)
    mock_result = MagicMock()
    mock_result.all.return_value = [
        ("2025-01-01", Decimal("50.00"), 2),
        ("2025-01-02", Decimal("75.00"), 3),
    ]
    mock_session.exec.return_value = mock_result

    # Act
    start = datetime(2025, 1, 1)
    end = datetime(2025, 1, 31)
    trends = await analytics_service.get_trends(start, end, period="daily")

    # Assert
    assert len(trends.trends) == 2
    assert trends.trends[0].date == "2025-01-01"
    assert trends.trends[0].total == Decimal("50.00")
    assert trends.trends[1].date == "2025-01-02"
    assert trends.trends[1].total == Decimal("75.00")


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
    """Test get_top_stores returns ranked stores."""
    # Arrange - tuples: (store_name, visit_count, total_spent)
    mock_result = MagicMock()
    mock_result.all.return_value = [
        ("Store A", 5, Decimal("200.00")),
        ("Store B", 3, Decimal("150.00")),
    ]
    mock_session.exec.return_value = mock_result

    # Act
    result = await analytics_service.get_top_stores(year=2025, limit=10)

    # Assert
    assert len(result.stores) == 2
    assert result.stores[0].store_name == "Store A"
    assert result.stores[0].total_spent == Decimal("200.00")
    assert result.stores[0].avg_per_visit == Decimal("40.00")
    assert result.stores[1].store_name == "Store B"


@pytest.mark.asyncio
async def test_get_top_stores_with_month_filter(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_top_stores filters by month."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = [
        ("Monthly Store", 2, Decimal("80.00")),
    ]
    mock_session.exec.return_value = mock_result

    # Act
    result = await analytics_service.get_top_stores(year=2025, month=1)

    # Assert
    assert result.month == 1
    assert len(result.stores) == 1


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
    assert result.total_spent == Decimal("0")


@pytest.mark.asyncio
async def test_get_category_breakdown_with_data(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_category_breakdown returns correct percentages."""
    # Arrange - tuples: (category_id, category_name, item_count, category_total)
    mock_result = MagicMock()
    mock_result.all.return_value = [
        (1, "Groceries", 10, Decimal("100.00")),
        (2, "Electronics", 5, Decimal("50.00")),
    ]
    mock_session.exec.return_value = mock_result

    # Act
    result = await analytics_service.get_category_breakdown(year=2025)

    # Assert
    assert len(result.categories) == 2
    assert result.total_spent == Decimal("150.00")

    # First category (Groceries) - 100/150 = 66.7%
    assert result.categories[0].category_id == 1
    assert result.categories[0].category_name == "Groceries"
    assert result.categories[0].item_count == 10
    assert result.categories[0].total_spent == Decimal("100.00")
    assert result.categories[0].percentage == Decimal("66.7")

    # Second category (Electronics) - 50/150 = 33.3%
    assert result.categories[1].category_id == 2
    assert result.categories[1].percentage == Decimal("33.3")

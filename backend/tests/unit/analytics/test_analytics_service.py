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
    # Arrange - mock the execute to return empty results
    mock_result = MagicMock()
    mock_result.one.return_value = MagicMock(total=None, count=0)
    mock_session.execute.return_value = mock_result

    # Mock category query to return empty
    mock_category_result = MagicMock()
    mock_category_result.first.return_value = None
    mock_session.execute.side_effect = [mock_result, mock_category_result]

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
    # Arrange
    mock_result = MagicMock()
    mock_result.one.return_value = MagicMock(total=Decimal("100.00"), count=4)

    mock_category_result = MagicMock()
    mock_category_result.first.return_value = None

    mock_session.execute.side_effect = [mock_result, mock_category_result]

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
    mock_result.one.return_value = MagicMock(total=Decimal("1200.00"), count=24)

    mock_category_result = MagicMock()
    mock_category_result.first.return_value = None

    mock_session.execute.side_effect = [mock_result, mock_category_result]

    # Act
    summary = await analytics_service.get_summary(year=2025, month=None)

    # Assert
    assert summary.total_spent == Decimal("1200.00")
    assert summary.receipt_count == 24
    assert summary.month is None


@pytest.mark.asyncio
async def test_get_trends_empty_data(
    analytics_service: AnalyticsService, mock_session: AsyncMock
) -> None:
    """Test get_trends returns empty list when no data exists."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

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
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = [
        MagicMock(period_date="2025-01-01", total=Decimal("50.00"), count=2),
        MagicMock(period_date="2025-01-02", total=Decimal("75.00"), count=3),
    ]
    mock_session.execute.return_value = mock_result

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
    mock_session.execute.return_value = mock_result

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
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = [
        MagicMock(store_name="Store A", visit_count=5, total_spent=Decimal("200.00")),
        MagicMock(store_name="Store B", visit_count=3, total_spent=Decimal("150.00")),
    ]
    mock_session.execute.return_value = mock_result

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
        MagicMock(store_name="Monthly Store", visit_count=2, total_spent=Decimal("80.00")),
    ]
    mock_session.execute.return_value = mock_result

    # Act
    result = await analytics_service.get_top_stores(year=2025, month=1)

    # Assert
    assert result.month == 1
    assert len(result.stores) == 1

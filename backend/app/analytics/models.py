from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel


class CurrencyAmount(SQLModel):
    """Amount in a specific currency."""

    currency: str
    amount: Decimal


class SpendingSummary(SQLModel):
    """Summary of spending for a given period.

    Totals are grouped by original currency for frontend conversion.
    """

    totals_by_currency: list[CurrencyAmount]
    receipt_count: int
    top_category: str | None
    top_category_amounts: list[CurrencyAmount] | None  # Grouped by currency
    year: int
    month: int | None


class SpendingTrend(SQLModel):
    """Single data point in spending trends.

    Totals are grouped by original currency for frontend conversion.
    """

    date: str  # ISO format date string
    totals_by_currency: list[CurrencyAmount]
    receipt_count: int


class SpendingTrendsResponse(SQLModel):
    """Response for spending trends endpoint."""

    trends: list[SpendingTrend]
    period: str  # 'daily', 'weekly', 'monthly'
    start_date: datetime
    end_date: datetime


class StoreVisit(SQLModel):
    """Store visit statistics.

    Totals are grouped by original currency for frontend conversion.
    """

    store_name: str
    visit_count: int
    totals_by_currency: list[CurrencyAmount]


class TopStoresResponse(SQLModel):
    """Response for top stores endpoint."""

    stores: list[StoreVisit]
    year: int
    month: int | None


class CategorySpending(SQLModel):
    """Spending data for a single category.

    Totals are grouped by original currency for frontend conversion.
    """

    category_id: int
    category_name: str
    item_count: int
    totals_by_currency: list[CurrencyAmount]


class CategoryBreakdownResponse(SQLModel):
    """Response for category breakdown endpoint.

    Note: Percentages are calculated on frontend after currency conversion.
    """

    categories: list[CategorySpending]
    totals_by_currency: list[CurrencyAmount]
    year: int
    month: int | None

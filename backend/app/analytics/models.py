from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel


class SpendingSummary(SQLModel):
    """Summary of spending for a given period."""

    total_spent: Decimal
    receipt_count: int
    avg_per_receipt: Decimal
    top_category: str | None
    top_category_amount: Decimal | None
    currency: str
    year: int
    month: int | None


class SpendingTrend(SQLModel):
    """Single data point in spending trends."""

    date: str  # ISO format date string
    total: Decimal
    receipt_count: int
    currency: str


class SpendingTrendsResponse(SQLModel):
    """Response for spending trends endpoint."""

    trends: list[SpendingTrend]
    period: str  # 'daily', 'weekly', 'monthly'
    start_date: datetime
    end_date: datetime


class StoreVisit(SQLModel):
    """Store visit statistics."""

    store_name: str
    visit_count: int
    total_spent: Decimal
    avg_per_visit: Decimal
    currency: str


class TopStoresResponse(SQLModel):
    """Response for top stores endpoint."""

    stores: list[StoreVisit]
    year: int
    month: int | None


class CategorySpending(SQLModel):
    """Spending data for a single category."""

    category_id: int
    category_name: str
    item_count: int
    total_spent: Decimal
    percentage: Decimal
    currency: str


class CategoryBreakdownResponse(SQLModel):
    """Response for category breakdown endpoint."""

    categories: list[CategorySpending]
    total_spent: Decimal
    year: int
    month: int | None

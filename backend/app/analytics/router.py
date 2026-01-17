from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Query, status

from app.analytics.deps import AnalyticsDeps
from app.analytics.models import (
    CategoryBreakdownResponse,
    SpendingSummary,
    SpendingTrendsResponse,
    TopStoresResponse,
)
from app.auth.deps import CurrentUser, require_user_id

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary", response_model=SpendingSummary, status_code=status.HTTP_200_OK)
async def get_spending_summary(
    current_user: CurrentUser,
    service: AnalyticsDeps,
    year: int = Query(default_factory=lambda: datetime.now().year, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
) -> SpendingSummary:
    """
    Get spending summary for a given period.

    Returns totals grouped by original currency for frontend conversion.
    """
    user_id = require_user_id(current_user)
    return await service.get_summary(user_id=user_id, year=year, month=month)


@router.get(
    "/trends", response_model=SpendingTrendsResponse, status_code=status.HTTP_200_OK
)
async def get_spending_trends(
    current_user: CurrentUser,
    service: AnalyticsDeps,
    start: datetime = Query(..., description="Start date (ISO format)"),
    end: datetime = Query(..., description="End date (ISO format)"),
    period: Literal["daily", "weekly", "monthly"] = Query(default="monthly"),
) -> SpendingTrendsResponse:
    """
    Get spending trends over time.

    Returns time-series data grouped by original currency for frontend conversion.
    """
    user_id = require_user_id(current_user)
    return await service.get_trends(
        user_id=user_id,
        start_date=start,
        end_date=end,
        period=period,
    )


@router.get(
    "/top-stores", response_model=TopStoresResponse, status_code=status.HTTP_200_OK
)
async def get_top_stores(
    current_user: CurrentUser,
    service: AnalyticsDeps,
    year: int = Query(default_factory=lambda: datetime.now().year, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    limit: int = Query(default=10, ge=1, le=50),
) -> TopStoresResponse:
    """
    Get top stores by spending.

    Returns stores with totals grouped by original currency for frontend conversion.
    """
    user_id = require_user_id(current_user)
    return await service.get_top_stores(
        user_id=user_id,
        year=year,
        month=month,
        limit=limit,
    )


@router.get(
    "/category-breakdown",
    response_model=CategoryBreakdownResponse,
    status_code=status.HTTP_200_OK,
)
async def get_category_breakdown(
    current_user: CurrentUser,
    service: AnalyticsDeps,
    year: int = Query(default_factory=lambda: datetime.now().year, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
) -> CategoryBreakdownResponse:
    """
    Get spending breakdown by category.

    Returns categories with totals grouped by original currency for frontend conversion.
    Percentages are calculated on frontend after currency conversion.
    """
    user_id = require_user_id(current_user)
    return await service.get_category_breakdown(
        user_id=user_id,
        year=year,
        month=month,
    )

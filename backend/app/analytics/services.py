from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import extract, func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.receipt.models import Receipt, ReceiptItem

from .models import (
    CategoryBreakdownResponse,
    CategorySpending,
    SpendingSummary,
    SpendingTrend,
    SpendingTrendsResponse,
    StoreVisit,
    TopStoresResponse,
)


class AnalyticsService:
    """Service for analytics and spending insights."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(
        self,
        year: int,
        month: int | None = None,
        currency: str = "EUR",
    ) -> SpendingSummary:
        """Get spending summary for a given period."""
        # Build base query
        stmt = select(
            func.sum(Receipt.total_amount).label("total"),
            func.count(Receipt.id).label("count"),
        ).where(extract("year", Receipt.purchase_date) == year)

        if month:
            stmt = stmt.where(extract("month", Receipt.purchase_date) == month)

        result = await self.session.execute(stmt)
        row = result.one()

        total_spent = row.total or Decimal("0")
        receipt_count = row.count or 0
        avg_per_receipt = (
            total_spent / receipt_count if receipt_count > 0 else Decimal("0")
        )

        # Get top category
        top_category = None
        top_category_amount = None

        category_stmt = (
            select(
                ReceiptItem.category_id,
                func.sum(ReceiptItem.total_price).label("category_total"),
            )
            .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
            .where(extract("year", Receipt.purchase_date) == year)
        )

        if month:
            category_stmt = category_stmt.where(
                extract("month", Receipt.purchase_date) == month
            )

        category_stmt = (
            category_stmt.where(ReceiptItem.category_id.isnot(None))
            .group_by(ReceiptItem.category_id)
            .order_by(func.sum(ReceiptItem.total_price).desc())
            .limit(1)
        )

        category_result = await self.session.execute(category_stmt)
        top_cat_row = category_result.first()

        if top_cat_row and top_cat_row.category_id:
            # Get category name
            from app.category.models import Category

            cat = await self.session.get(Category, top_cat_row.category_id)
            if cat:
                top_category = cat.name
                top_category_amount = top_cat_row.category_total

        return SpendingSummary(
            total_spent=total_spent,
            receipt_count=receipt_count,
            avg_per_receipt=round(avg_per_receipt, 2),
            top_category=top_category,
            top_category_amount=top_category_amount,
            currency=currency,
            year=year,
            month=month,
        )

    async def get_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        period: Literal["daily", "weekly", "monthly"] = "monthly",
        currency: str = "EUR",
    ) -> SpendingTrendsResponse:
        """Get spending trends over time."""
        # Determine grouping based on period - using PostgreSQL date_trunc
        if period == "daily":
            date_trunc = func.date_trunc("day", Receipt.purchase_date)
        elif period == "weekly":
            date_trunc = func.date_trunc("week", Receipt.purchase_date)
        else:  # monthly
            date_trunc = func.date_trunc("month", Receipt.purchase_date)

        stmt = (
            select(
                date_trunc.label("period_date"),
                func.sum(Receipt.total_amount).label("total"),
                func.count(Receipt.id).label("count"),
            )
            .where(Receipt.purchase_date >= start_date)
            .where(Receipt.purchase_date <= end_date)
            .group_by(date_trunc)
            .order_by(date_trunc)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        trends = [
            SpendingTrend(
                date=str(row.period_date),
                total=row.total or Decimal("0"),
                receipt_count=row.count or 0,
                currency=currency,
            )
            for row in rows
        ]

        return SpendingTrendsResponse(
            trends=trends,
            period=period,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_top_stores(
        self,
        year: int,
        month: int | None = None,
        limit: int = 10,
        currency: str = "EUR",
    ) -> TopStoresResponse:
        """Get top stores by spending."""
        stmt = select(
            Receipt.store_name,
            func.count(Receipt.id).label("visit_count"),
            func.sum(Receipt.total_amount).label("total_spent"),
        ).where(extract("year", Receipt.purchase_date) == year)

        if month:
            stmt = stmt.where(extract("month", Receipt.purchase_date) == month)

        stmt = (
            stmt.group_by(Receipt.store_name)
            .order_by(func.sum(Receipt.total_amount).desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        stores = [
            StoreVisit(
                store_name=row.store_name,
                visit_count=row.visit_count,
                total_spent=row.total_spent or Decimal("0"),
                avg_per_visit=round(
                    (row.total_spent or Decimal("0")) / row.visit_count, 2
                )
                if row.visit_count > 0
                else Decimal("0"),
                currency=currency,
            )
            for row in rows
        ]

        return TopStoresResponse(
            stores=stores,
            year=year,
            month=month,
        )

    async def get_category_breakdown(
        self,
        year: int,
        month: int | None = None,
        currency: str = "EUR",
    ) -> CategoryBreakdownResponse:
        """Get spending breakdown by category."""
        from app.category.models import Category

        # Get total for percentage calculation
        total_stmt = (
            select(func.sum(ReceiptItem.total_price))
            .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
            .where(extract("year", Receipt.purchase_date) == year)
        )
        if month:
            total_stmt = total_stmt.where(
                extract("month", Receipt.purchase_date) == month
            )

        total_result = await self.session.execute(total_stmt)
        total_spent = total_result.scalar() or Decimal("0")

        # Get spending by category
        stmt = (
            select(
                ReceiptItem.category_id,
                func.count(ReceiptItem.id).label("item_count"),
                func.sum(ReceiptItem.total_price).label("category_total"),
            )
            .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
            .where(extract("year", Receipt.purchase_date) == year)
            .where(ReceiptItem.category_id.isnot(None))
        )

        if month:
            stmt = stmt.where(extract("month", Receipt.purchase_date) == month)

        stmt = stmt.group_by(ReceiptItem.category_id).order_by(
            func.sum(ReceiptItem.total_price).desc()
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        # Build category spending list with names
        categories = []
        for row in rows:
            cat = await self.session.get(Category, row.category_id)
            if cat:
                cat_total = row.category_total or Decimal("0")
                percentage = (
                    (cat_total / total_spent * 100) if total_spent > 0 else Decimal("0")
                )
                categories.append(
                    CategorySpending(
                        category_id=row.category_id,
                        category_name=cat.name,
                        item_count=row.item_count,
                        total_spent=cat_total,
                        percentage=round(percentage, 1),
                        currency=currency,
                    )
                )

        return CategoryBreakdownResponse(
            categories=categories,
            total_spent=total_spent,
            year=year,
            month=month,
        )

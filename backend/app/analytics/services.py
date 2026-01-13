from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from sqlmodel import col, extract, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.category.models import Category
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
        stmt = select(
            func.sum(col(Receipt.total_amount)).label("total_amount"),
            func.count(col(Receipt.id)).label("receipt_count"),
        ).where(
            extract("year", col(Receipt.purchase_date)) == year,
            col(Receipt.currency) == currency,
        )

        if month:
            stmt = stmt.where(extract("month", col(Receipt.purchase_date)) == month)

        result = await self.session.exec(stmt)
        row = result.one()

        total_amount_val, receipt_count_val = row
        total_spent = Decimal(total_amount_val or 0)
        receipt_count = int(receipt_count_val or 0)
        avg_per_receipt = (
            total_spent / receipt_count if receipt_count > 0 else Decimal("0")
        )

        # Get top category with JOIN
        top_category = None
        top_category_amount = None

        category_stmt: Any = (
            select(
                col(Category.name).label("category_name"),
                func.sum(col(ReceiptItem.total_price)).label("category_total"),
            )
            .join(Receipt, col(ReceiptItem.receipt_id) == col(Receipt.id))
            .join(Category, col(ReceiptItem.category_id) == col(Category.id))
            .where(
                extract("year", col(Receipt.purchase_date)) == year,
                col(Receipt.currency) == currency,
                col(ReceiptItem.category_id).is_not(None),
            )
        )

        if month:
            category_stmt = category_stmt.where(
                extract("month", col(Receipt.purchase_date)) == month
            )

        category_stmt = (
            category_stmt.group_by(col(Category.name))
            .order_by(func.sum(col(ReceiptItem.total_price)).desc())
            .limit(1)
        )

        category_result = await self.session.exec(category_stmt)
        top_cat_row = category_result.first()

        if top_cat_row:
            top_category, top_category_amount = top_cat_row

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
        if period == "daily":
            date_trunc = func.date_trunc("day", col(Receipt.purchase_date))
        elif period == "weekly":
            date_trunc = func.date_trunc("week", col(Receipt.purchase_date))
        else:
            date_trunc = func.date_trunc("month", col(Receipt.purchase_date))

        stmt = (
            select(
                date_trunc.label("period_date"),
                func.sum(col(Receipt.total_amount)).label("total_amount"),
                func.count(col(Receipt.id)).label("receipt_count"),
            )
            .where(
                col(Receipt.purchase_date) >= start_date,
                col(Receipt.purchase_date) <= end_date,
                col(Receipt.currency) == currency,
            )
            .group_by(date_trunc)
            .order_by(date_trunc)
        )

        result = await self.session.exec(stmt)
        rows = result.all()

        trends = [
            SpendingTrend(
                date=str(period_date),
                total=Decimal(total_amount or 0),
                receipt_count=int(receipt_count_val or 0),
                currency=currency,
            )
            for period_date, total_amount, receipt_count_val in rows
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
        stmt: Any = select(
            col(Receipt.store_name).label("store_name"),
            func.count(col(Receipt.id)).label("visit_count"),
            func.sum(col(Receipt.total_amount)).label("total_spent"),
        ).where(
            extract("year", col(Receipt.purchase_date)) == year,
            col(Receipt.currency) == currency,
        )

        if month:
            stmt = stmt.where(extract("month", col(Receipt.purchase_date)) == month)

        stmt = (
            stmt.group_by(col(Receipt.store_name))
            .order_by(func.sum(col(Receipt.total_amount)).desc())
            .limit(limit)
        )

        result = await self.session.exec(stmt)
        rows = result.all()

        stores = []
        for store_name, visit_count_val, total_spent_val in rows:
            visit_count = int(visit_count_val or 0)
            total_spent = Decimal(total_spent_val or 0)
            avg_per_visit = (
                round(total_spent / visit_count, 2) if visit_count > 0 else Decimal("0")
            )
            stores.append(
                StoreVisit(
                    store_name=store_name,
                    visit_count=visit_count,
                    total_spent=total_spent,
                    avg_per_visit=avg_per_visit,
                    currency=currency,
                )
            )

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
        stmt: Any = (
            select(
                col(ReceiptItem.category_id).label("category_id"),
                col(Category.name).label("category_name"),
                func.count(col(ReceiptItem.id)).label("item_count"),
                func.sum(col(ReceiptItem.total_price)).label("category_total"),
            )
            .join(Receipt, col(ReceiptItem.receipt_id) == col(Receipt.id))
            .join(Category, col(ReceiptItem.category_id) == col(Category.id))
            .where(
                extract("year", col(Receipt.purchase_date)) == year,
                col(Receipt.currency) == currency,
                col(ReceiptItem.category_id).is_not(None),
            )
        )

        if month:
            stmt = stmt.where(extract("month", col(Receipt.purchase_date)) == month)

        stmt = stmt.group_by(col(ReceiptItem.category_id), col(Category.name)).order_by(
            func.sum(col(ReceiptItem.total_price)).desc()
        )

        result = await self.session.exec(stmt)
        rows = result.all()

        total_spent = Decimal(sum(cat_total or 0 for _, _, _, cat_total in rows) or 0)

        categories = []
        if total_spent > 0:
            for category_id, category_name, item_count_val, cat_total in rows:
                cat_total_dec = Decimal(cat_total or 0)
                percentage = round((cat_total_dec / total_spent) * 100, 1)
                categories.append(
                    CategorySpending(
                        category_id=int(category_id),
                        category_name=category_name,
                        item_count=int(item_count_val or 0),
                        total_spent=cat_total_dec,
                        percentage=percentage,
                        currency=currency,
                    )
                )

        return CategoryBreakdownResponse(
            categories=categories,
            total_spent=total_spent,
            year=year,
            month=month,
        )

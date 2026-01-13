from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import select as sa_select
from sqlmodel import col, extract, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.category.models import Category
from app.receipt.models import Receipt, ReceiptItem

from .models import (
    CategoryBreakdownResponse,
    CategorySpending,
    CurrencyAmount,
    SpendingSummary,
    SpendingTrend,
    SpendingTrendsResponse,
    StoreVisit,
    TopStoresResponse,
)


class AnalyticsService:
    """Service for analytics and spending insights.

    All methods return data grouped by original currency.
    Frontend converts to display currency using live exchange rates.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(
        self,
        year: int,
        month: int | None = None,
    ) -> SpendingSummary:
        """Get spending summary for a given period, grouped by currency."""
        # Get totals grouped by currency
        stmt = select(
            col(Receipt.currency).label("currency"),
            func.sum(col(Receipt.total_amount)).label("total_amount"),
            func.count(col(Receipt.id)).label("receipt_count"),
        ).where(
            extract("year", col(Receipt.purchase_date)) == year,
        )

        if month:
            stmt = stmt.where(extract("month", col(Receipt.purchase_date)) == month)

        stmt = stmt.group_by(col(Receipt.currency))

        result = await self.session.exec(stmt)
        rows = result.all()

        totals_by_currency = []
        total_receipt_count = 0

        for currency, total_amount, receipt_count in rows:
            totals_by_currency.append(
                CurrencyAmount(
                    currency=currency,
                    amount=Decimal(total_amount or 0),
                )
            )
            total_receipt_count += int(receipt_count or 0)

        # Get top category with amounts grouped by currency
        top_category = None
        top_category_amounts: list[CurrencyAmount] | None = None

        category_stmt: Any = (
            select(
                col(Category.name).label("category_name"),
                col(Receipt.currency).label("currency"),
                func.sum(col(ReceiptItem.total_price)).label("category_total"),
            )
            .join(Receipt, col(ReceiptItem.receipt_id) == col(Receipt.id))
            .join(Category, col(ReceiptItem.category_id) == col(Category.id))
            .where(
                extract("year", col(Receipt.purchase_date)) == year,
                col(ReceiptItem.category_id).is_not(None),
            )
        )

        if month:
            category_stmt = category_stmt.where(
                extract("month", col(Receipt.purchase_date)) == month
            )

        # First find the top category by total spending (across all currencies)
        top_cat_stmt = (
            select(
                col(Category.name).label("category_name"),
                func.sum(col(ReceiptItem.total_price)).label("category_total"),
            )
            .join(Receipt, col(ReceiptItem.receipt_id) == col(Receipt.id))
            .join(Category, col(ReceiptItem.category_id) == col(Category.id))
            .where(
                extract("year", col(Receipt.purchase_date)) == year,
                col(ReceiptItem.category_id).is_not(None),
            )
        )

        if month:
            top_cat_stmt = top_cat_stmt.where(
                extract("month", col(Receipt.purchase_date)) == month
            )

        top_cat_stmt = (
            top_cat_stmt.group_by(col(Category.name))
            .order_by(func.sum(col(ReceiptItem.total_price)).desc())
            .limit(1)
        )

        top_cat_result = await self.session.exec(top_cat_stmt)
        top_cat_row = top_cat_result.first()

        if top_cat_row:
            top_category = top_cat_row[0]

            # Get amounts by currency for top category
            cat_currency_stmt: Any = (
                select(
                    col(Receipt.currency).label("currency"),
                    func.sum(col(ReceiptItem.total_price)).label("category_total"),
                )
                .join(Receipt, col(ReceiptItem.receipt_id) == col(Receipt.id))
                .join(Category, col(ReceiptItem.category_id) == col(Category.id))
                .where(
                    extract("year", col(Receipt.purchase_date)) == year,
                    col(Category.name) == top_category,
                    col(ReceiptItem.category_id).is_not(None),
                )
            )

            if month:
                cat_currency_stmt = cat_currency_stmt.where(
                    extract("month", col(Receipt.purchase_date)) == month
                )

            cat_currency_stmt = cat_currency_stmt.group_by(col(Receipt.currency))

            cat_currency_result = await self.session.exec(cat_currency_stmt)
            cat_currency_rows = cat_currency_result.all()

            top_category_amounts = [
                CurrencyAmount(currency=curr, amount=Decimal(amt or 0))
                for curr, amt in cat_currency_rows
            ]

        return SpendingSummary(
            totals_by_currency=totals_by_currency,
            receipt_count=total_receipt_count,
            top_category=top_category,
            top_category_amounts=top_category_amounts,
            year=year,
            month=month,
        )

    async def get_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        period: Literal["daily", "weekly", "monthly"] = "monthly",
    ) -> SpendingTrendsResponse:
        """Get spending trends over time, grouped by currency."""
        if period == "daily":
            date_trunc = func.date_trunc("day", col(Receipt.purchase_date))
        elif period == "weekly":
            date_trunc = func.date_trunc("week", col(Receipt.purchase_date))
        else:
            date_trunc = func.date_trunc("month", col(Receipt.purchase_date))

        stmt = (
            select(
                date_trunc.label("period_date"),
                col(Receipt.currency).label("currency"),
                func.sum(col(Receipt.total_amount)).label("total_amount"),
                func.count(col(Receipt.id)).label("receipt_count"),
            )
            .where(
                col(Receipt.purchase_date) >= start_date,
                col(Receipt.purchase_date) <= end_date,
            )
            .group_by(date_trunc, col(Receipt.currency))
            .order_by(date_trunc)
        )

        result = await self.session.exec(stmt)
        rows = result.all()

        # Group rows by date
        date_data: dict[str, dict[str, Any]] = {}
        for period_date, currency, total_amount, receipt_count in rows:
            # Convert to ISO 8601 format for Safari compatibility
            date_str = (
                period_date.isoformat()
                if hasattr(period_date, "isoformat")
                else str(period_date).replace(" ", "T")
            )
            if date_str not in date_data:
                date_data[date_str] = {"totals": [], "receipt_count": 0}

            date_data[date_str]["totals"].append(
                CurrencyAmount(currency=currency, amount=Decimal(total_amount or 0))
            )
            date_data[date_str]["receipt_count"] += int(receipt_count or 0)

        trends = [
            SpendingTrend(
                date=date_str,
                totals_by_currency=data["totals"],
                receipt_count=data["receipt_count"],
            )
            for date_str, data in date_data.items()
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
    ) -> TopStoresResponse:
        """Get top stores by spending, grouped by currency."""
        # First get the top stores by total spending (cross-currency)
        top_stores_stmt: Any = select(
            col(Receipt.store_name).label("store_name"),
            func.sum(col(Receipt.total_amount)).label("total_spent"),
        ).where(
            extract("year", col(Receipt.purchase_date)) == year,
        )

        if month:
            top_stores_stmt = top_stores_stmt.where(
                extract("month", col(Receipt.purchase_date)) == month
            )

        top_stores_stmt = (
            top_stores_stmt.group_by(col(Receipt.store_name))
            .order_by(func.sum(col(Receipt.total_amount)).desc())
            .limit(limit)
        )

        top_result = await self.session.exec(top_stores_stmt)
        top_stores = [row[0] for row in top_result.all()]

        if not top_stores:
            return TopStoresResponse(stores=[], year=year, month=month)

        # Get detailed data for all top stores in a single batch query
        detail_stmt: Any = select(
            col(Receipt.store_name).label("store_name"),
            col(Receipt.currency).label("currency"),
            func.count(col(Receipt.id)).label("visit_count"),
            func.sum(col(Receipt.total_amount)).label("total_spent"),
        ).where(
            extract("year", col(Receipt.purchase_date)) == year,
            col(Receipt.store_name).in_(top_stores),
        )

        if month:
            detail_stmt = detail_stmt.where(
                extract("month", col(Receipt.purchase_date)) == month
            )

        detail_stmt = detail_stmt.group_by(
            col(Receipt.store_name), col(Receipt.currency)
        )

        detail_result = await self.session.exec(detail_stmt)
        detail_rows = detail_result.all()

        # Group results by store
        store_data: dict[str, dict[str, Any]] = {
            store_name: {"totals": [], "visit_count": 0} for store_name in top_stores
        }

        for store_name, currency, visit_count, total_spent in detail_rows:
            store_data[store_name]["totals"].append(
                CurrencyAmount(currency=currency, amount=Decimal(total_spent or 0))
            )
            store_data[store_name]["visit_count"] += int(visit_count or 0)

        # Build response maintaining top stores order
        stores = [
            StoreVisit(
                store_name=store_name,
                visit_count=store_data[store_name]["visit_count"],
                totals_by_currency=store_data[store_name]["totals"],
            )
            for store_name in top_stores
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
    ) -> CategoryBreakdownResponse:
        """Get spending breakdown by category, grouped by currency."""
        stmt: Any = (
            sa_select(
                col(ReceiptItem.category_id).label("category_id"),
                col(Category.name).label("category_name"),
                col(Receipt.currency).label("currency"),
                func.count(col(ReceiptItem.id)).label("item_count"),
                func.sum(col(ReceiptItem.total_price)).label("category_total"),
            )
            .join(Receipt, col(ReceiptItem.receipt_id) == col(Receipt.id))
            .join(Category, col(ReceiptItem.category_id) == col(Category.id))
            .where(
                extract("year", col(Receipt.purchase_date)) == year,
                col(ReceiptItem.category_id).is_not(None),
            )
        )

        if month:
            stmt = stmt.where(extract("month", col(Receipt.purchase_date)) == month)

        stmt = stmt.group_by(
            col(ReceiptItem.category_id),
            col(Category.name),
            col(Receipt.currency),
        )

        result = await self.session.exec(stmt)
        rows = result.all()

        # Group by category
        category_data: dict[int, dict[str, Any]] = {}
        overall_totals: dict[str, Decimal] = {}

        for category_id, category_name, currency, item_count, cat_total in rows:
            cat_id = int(category_id)
            if cat_id not in category_data:
                category_data[cat_id] = {
                    "name": category_name,
                    "item_count": 0,
                    "totals": {},
                }

            category_data[cat_id]["item_count"] += int(item_count or 0)
            curr_total = Decimal(cat_total or 0)
            category_data[cat_id]["totals"][currency] = (
                category_data[cat_id]["totals"].get(currency, Decimal(0)) + curr_total
            )

            # Track overall totals
            overall_totals[currency] = (
                overall_totals.get(currency, Decimal(0)) + curr_total
            )

        # Convert to response format
        categories = []
        for cat_id, data in category_data.items():
            totals_list = [
                CurrencyAmount(currency=curr, amount=amt)
                for curr, amt in data["totals"].items()
            ]
            categories.append(
                CategorySpending(
                    category_id=cat_id,
                    category_name=data["name"],
                    item_count=data["item_count"],
                    totals_by_currency=totals_list,
                )
            )

        # Sort categories by total spending (sum across currencies - rough ordering)
        categories.sort(
            key=lambda c: sum(t.amount for t in c.totals_by_currency),
            reverse=True,
        )

        totals_by_currency = [
            CurrencyAmount(currency=curr, amount=amt)
            for curr, amt in overall_totals.items()
        ]

        return CategoryBreakdownResponse(
            categories=categories,
            totals_by_currency=totals_by_currency,
            year=year,
            month=month,
        )

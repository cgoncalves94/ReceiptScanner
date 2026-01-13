"""
Test script to verify query count for get_top_stores endpoint.
This script directly tests the AnalyticsService method to count SQL queries.
"""
import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy import event
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import async_session_factory, engine
from app.analytics.services import AnalyticsService
from app.receipt.models import Receipt
from app.category.models import Category


# Configure logging to show SQL queries
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)

# Set SQL echo to True to see queries
engine.echo = True

# Counter for queries
query_count = 0


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Count each SQL query execution."""
    global query_count
    query_count += 1
    print(f"\n{'='*80}")
    print(f"QUERY #{query_count}")
    print(f"{'='*80}")
    print(statement)
    if parameters:
        print(f"\nParameters: {parameters}")
    print(f"{'='*80}\n")


async def seed_test_data(session: AsyncSession) -> None:
    """Create test receipts with multiple stores."""
    print("\n" + "="*80)
    print("SEEDING TEST DATA")
    print("="*80 + "\n")

    # Check if we already have data
    from sqlmodel import select
    result = await session.exec(select(Receipt))
    existing = result.all()

    if len(existing) >= 10:
        print(f"Found {len(existing)} existing receipts, skipping seed")
        return

    # Create test receipts with various stores
    stores = [
        ("Tesco", "GBP", 100.00),
        ("Tesco", "GBP", 150.00),
        ("Tesco", "EUR", 80.00),
        ("Sainsbury's", "GBP", 75.00),
        ("Sainsbury's", "GBP", 90.00),
        ("Lidl", "EUR", 45.00),
        ("Lidl", "EUR", 55.00),
        ("Aldi", "GBP", 60.00),
        ("Asda", "GBP", 85.00),
        ("Waitrose", "GBP", 120.00),
    ]

    for store_name, currency, amount in stores:
        receipt = Receipt(
            store_name=store_name,
            purchase_date=datetime(2024, 1, 15),
            currency=currency,
            total_amount=Decimal(str(amount)),
            image_url="test.jpg"
        )
        session.add(receipt)

    await session.commit()
    print(f"Created {len(stores)} test receipts")


async def test_get_top_stores():
    """Test the get_top_stores method and count queries."""
    global query_count

    async with async_session_factory() as session:
        # Seed data first (queries don't count for our test)
        await seed_test_data(session)

        # Reset query counter
        query_count = 0

        print("\n" + "="*80)
        print("TESTING get_top_stores - COUNTING QUERIES")
        print("="*80 + "\n")

        # Create service and call get_top_stores
        service = AnalyticsService(session)
        result = await service.get_top_stores(year=2024, month=1, limit=10)

        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"\nTotal queries executed: {query_count}")
        print(f"Number of stores returned: {len(result.stores)}")
        print("\nStores:")
        for i, store in enumerate(result.stores, 1):
            totals = ", ".join(f"{t.currency} {t.amount}" for t in store.totals_by_currency)
            print(f"  {i}. {store.store_name}: {store.visit_count} visits, Totals: [{totals}]")

        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        if query_count == 2:
            print("\n✅ SUCCESS: Exactly 2 queries executed (optimized batch query)")
            print("   - Query 1: Get top store names")
            print("   - Query 2: Get currency details for all stores (single batch)")
        elif query_count > 2:
            print(f"\n❌ FAILURE: {query_count} queries executed")
            print(f"   Expected: 2 queries (batch)")
            print(f"   This indicates N+1 query pattern is still present")
        else:
            print(f"\n⚠️  WARNING: Only {query_count} query executed (unexpected)")

        print("="*80 + "\n")

        return query_count == 2


if __name__ == "__main__":
    success = asyncio.run(test_get_top_stores())
    exit(0 if success else 1)

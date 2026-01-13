"""
Manual verification test to count queries for get_top_stores.
Run with: pytest test_manual_query_verification.py -v -s
"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from sqlalchemy import event

from app.core.db import async_session_factory
from app.analytics.services import AnalyticsService
from app.receipt.models import Receipt


@pytest.mark.asyncio
async def test_query_count_for_top_stores():
    """Verify that get_top_stores executes exactly 2 queries."""
    query_count = 0
    queries_executed = []

    def count_query(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1
        # Store query for inspection
        queries_executed.append({
            'number': query_count,
            'statement': statement,
            'parameters': parameters
        })
        print(f"\n{'='*80}")
        print(f"QUERY #{query_count}")
        print(f"{'='*80}")
        print(statement)
        if parameters:
            print(f"\nParameters: {parameters}")
        print(f"{'='*80}\n")

    async with async_session_factory() as session:
        # Setup: Create test data
        stores_data = [
            ("Tesco", "GBP", 100), ("Tesco", "EUR", 80),
            ("Sainsbury's", "GBP", 75), ("Sainsbury's", "GBP", 90),
            ("Lidl", "EUR", 45), ("Lidl", "EUR", 55),
            ("Aldi", "GBP", 60), ("Asda", "GBP", 85),
            ("Waitrose", "GBP", 120), ("Morrisons", "GBP", 95),
        ]

        for store, currency, amount in stores_data:
            receipt = Receipt(
                store_name=store,
                purchase_date=datetime(2024, 6, 15),
                currency=currency,
                total_amount=Decimal(str(amount)),
                image_url="test.jpg"
            )
            session.add(receipt)
        await session.commit()

        # Reset counter and attach listener
        query_count = 0
        queries_executed = []

        from app.core.db import engine
        event.listen(engine.sync_engine, "before_cursor_execute", count_query)

        try:
            # Execute the method under test
            print("\n" + "="*80)
            print("TESTING get_top_stores - COUNTING QUERIES")
            print("="*80 + "\n")

            service = AnalyticsService(session)
            result = await service.get_top_stores(year=2024, month=6, limit=10)

            print("\n" + "="*80)
            print("RESULTS")
            print("="*80)
            print(f"\nTotal queries executed: {query_count}")
            print(f"Number of stores returned: {len(result.stores)}")

            # Verify query count
            print("\n" + "="*80)
            print("VERIFICATION")
            print("="*80)
            if query_count == 2:
                print("\n✅ SUCCESS: Exactly 2 queries executed")
                print("   Query 1: Get top store names")
                print("   Query 2: Batch get currency details for all stores")
            else:
                print(f"\n❌ FAILURE: {query_count} queries executed (expected 2)")

            assert query_count == 2, f"Expected 2 queries, got {query_count}"

        finally:
            event.remove(engine.sync_engine, "before_cursor_execute", count_query)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_query_count_for_top_stores())

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import Category


class CategoryRepository:
    """Repository for Category database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, category: Category) -> Category:
        """Create a new category."""
        self.session.add(category)
        await self.session.flush()
        return category

    async def get(self, category_id: int) -> Category | None:
        """Get a category by ID."""
        stmt = select(Category).where(Category.id == category_id)
        return await self.session.scalar(stmt)

    async def get_by_name(self, name: str) -> Category | None:
        """Get a category by name."""
        stmt = select(Category).where(Category.name == name)
        return await self.session.scalar(stmt)

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        """List all categories."""
        stmt = select(Category).offset(skip).limit(limit)
        result = await self.session.scalars(stmt)
        return result.all()

    async def update(self, category: Category, update_data: dict) -> Category:
        """Update a category."""
        category.sqlmodel_update(update_data)
        category.updated_at = datetime.now(UTC)
        await self.session.flush()
        return category

    async def delete(self, category: Category) -> None:
        """Delete a category."""
        await self.session.delete(category)
        await self.session.flush()

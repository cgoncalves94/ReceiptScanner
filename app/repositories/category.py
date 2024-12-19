from collections.abc import Sequence
from typing import Any

from sqlmodel import col, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, obj_in: Category) -> Category:
        """Create a new category using the DB model."""
        self.session.add(obj_in)
        await self.session.flush()
        await self.session.refresh(obj_in)
        return obj_in

    async def get(self, *, category_id: int) -> Category | None:
        """Get a category by ID."""
        return await self.session.get(Category, category_id)

    async def get_by_name(self, *, name: str) -> Category | None:
        """Get a category by name."""
        statement = select(Category).where(Category.name == name)
        result = await self.session.exec(statement)
        return result.first()

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        """List all categories with pagination."""
        statement = select(Category).offset(skip).limit(limit)
        result = await self.session.exec(statement)
        return result.all()

    async def update(self, *, db_obj: Category, obj_in: dict[str, Any]) -> Category:
        """Update a category using existing DB object and update data."""
        db_obj.sqlmodel_update(obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, *, category_id: int) -> None:
        """Delete a category."""
        statement = delete(Category).where(col(Category.id) == category_id)
        await self.session.exec(statement)

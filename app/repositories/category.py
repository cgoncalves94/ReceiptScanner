import logging
from collections.abc import Sequence
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Category

logger = logging.getLogger(__name__)


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
        for field, value in obj_in.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, *, category_id: int) -> bool:
        """Delete a category. Returns True if deleted, False if not found."""
        db_obj = await self.get(category_id=category_id)
        if not db_obj:
            return False
        await self.session.delete(db_obj)
        return True

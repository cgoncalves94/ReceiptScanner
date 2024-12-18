import logging
from collections.abc import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    Category,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)

logger = logging.getLogger(__name__)


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, *, category_in: CategoryCreate) -> CategoryRead:
        """Create a new category."""
        db_obj = Category.model_validate(category_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)

        category = CategoryRead.model_validate(db_obj)
        await self.db.commit()
        return category

    async def get(self, *, category_id: int) -> CategoryRead | None:
        """Get a category by ID."""
        statement = select(Category).filter_by(id=category_id)
        result = await self.db.exec(statement)
        db_obj = result.first()
        if not db_obj:
            return None
        return CategoryRead.model_validate(db_obj)

    async def get_by_name(self, *, name: str) -> CategoryRead | None:
        """Get a category by name."""
        statement = select(Category).filter_by(name=name)
        result = await self.db.exec(statement)
        db_obj = result.first()
        if not db_obj:
            return None
        return CategoryRead.model_validate(db_obj)

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[CategoryRead]:
        """List all categories with pagination."""
        statement = select(Category).offset(skip).limit(limit)
        results = await self.db.exec(statement)
        categories = results.all()
        return [CategoryRead.model_validate(cat) for cat in categories]

    async def update(
        self, *, db_obj: CategoryRead, category_in: CategoryUpdate
    ) -> CategoryRead:
        """Update a category."""
        # Get the actual model instance
        statement = select(Category).filter_by(id=db_obj.id)
        result = await self.db.exec(statement)
        model_obj = result.first()

        # Update the model
        category_data = category_in.model_dump(exclude_unset=True)
        for key, value in category_data.items():
            setattr(model_obj, key, value)

        self.db.add(model_obj)
        await self.db.flush()
        await self.db.refresh(model_obj)

        category = CategoryRead.model_validate(model_obj)
        await self.db.commit()
        return category

    async def delete(self, *, category_id: int) -> None:
        """Delete a category."""
        statement = select(Category).filter_by(id=category_id)
        result = await self.db.exec(statement)
        model_obj = result.first()
        if model_obj:
            await self.db.delete(model_obj)
            await self.db.flush()
            await self.db.commit()

from collections.abc import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError

from .models import Category, CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for managing categories."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, category_in: CategoryCreate) -> Category:
        """Create a new category."""
        # Check if category exists
        stmt = select(Category).where(Category.name == category_in.name)
        existing = await self.session.scalar(stmt)
        if existing:
            raise ConflictError(
                f"Category with name '{category_in.name}' already exists"
            )

        # Create new category
        category = Category.model_validate(category_in)
        self.session.add(category)
        await self.session.flush()
        return category

    async def get(self, category_id: int) -> Category:
        """Get a category by ID."""
        stmt = select(Category).where(Category.id == category_id)
        category = await self.session.scalar(stmt)
        if not category:
            raise NotFoundError(f"Category with ID {category_id} not found")
        return category

    async def get_by_name(self, name: str) -> Category | None:
        """Get a category by name."""
        stmt = select(Category).where(Category.name == name)
        return await self.session.scalar(stmt)

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        """List all categories."""
        stmt = select(Category).offset(skip).limit(limit)
        result = await self.session.scalars(stmt)
        return result.all()

    async def update(self, category_id: int, category_in: CategoryUpdate) -> Category:
        """Update a category."""
        # Get the category
        category = await self.get(category_id)

        # If name is being updated, check for uniqueness
        if category_in.name is not None and category_in.name != category.name:
            stmt = select(Category).where(Category.name == category_in.name)  # type: ignore
            existing = await self.session.scalar(stmt)
            if existing:
                raise ConflictError(
                    f"Category with name '{category_in.name}' already exists"
                )

        # Update fields using sqlmodel_update
        update_data = category_in.model_dump(exclude_unset=True, exclude={"id"})
        category.sqlmodel_update(update_data)

        await self.session.flush()
        return category

    async def delete(self, category_id: int) -> None:
        """Delete a category."""
        category = await self.get(category_id)
        await self.session.delete(category)

from collections.abc import Sequence

from app.core.exceptions import ConflictError, NotFoundError

from .models import Category, CategoryCreate, CategoryUpdate
from .repositories import CategoryRepository


class CategoryService:
    """Service for managing categories."""

    def __init__(self, category_repository: CategoryRepository) -> None:
        self.repository = category_repository

    async def create(self, category_in: CategoryCreate) -> Category:
        """Create a new category."""
        # Check if category exists
        existing = await self.repository.get_by_name(category_in.name)
        if existing:
            raise ConflictError(
                f"Category with name '{category_in.name}' already exists"
            )

        # Create new category
        category = Category.model_validate(category_in)
        return await self.repository.create(category)

    async def get(self, category_id: int) -> Category:
        """Get a category by ID."""
        category = await self.repository.get(category_id)
        if not category:
            raise NotFoundError(f"Category with ID {category_id} not found")
        return category

    async def get_by_name(self, name: str) -> Category | None:
        """Get a category by name."""
        return await self.repository.get_by_name(name)

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        """List all categories."""
        return await self.repository.list(skip=skip, limit=limit)

    async def update(self, category_id: int, category_in: CategoryUpdate) -> Category:
        """Update a category."""
        # Get the category
        category = await self.get(category_id)

        # If name is being updated, check for uniqueness
        if category_in.name is not None and category_in.name != category.name:
            existing = await self.repository.get_by_name(category_in.name)
            if existing:
                raise ConflictError(
                    f"Category with name '{category_in.name}' already exists"
                )

        # Prepare update data
        update_data = category_in.model_dump(exclude_unset=True, exclude={"id"})

        # Pass to repository for update
        return await self.repository.update(category, update_data)

    async def delete(self, category_id: int) -> None:
        """Delete a category."""
        category = await self.get(category_id)
        await self.repository.delete(category)

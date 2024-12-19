from collections.abc import Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError
from app.models import Category, CategoryCreate, CategoryRead, CategoryUpdate
from app.repositories import CategoryRepository


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CategoryRepository(session)

    async def create(self, category_in: CategoryCreate) -> CategoryRead:
        """Create a new category."""
        # Check if category exists
        existing = await self.repository.get_by_name(name=category_in.name)
        if existing:
            raise ResourceAlreadyExistsError("Category", f"name '{category_in.name}'")

        # Convert input model to DB model
        db_obj = Category(**category_in.model_dump())

        # Create through repository
        created = await self.repository.create(obj_in=db_obj)
        return CategoryRead.model_validate(created)

    async def get(self, category_id: int) -> CategoryRead:
        """Get a category by ID."""
        db_obj = await self.repository.get(category_id=category_id)
        if not db_obj:
            raise ResourceNotFoundError("Category", category_id)
        return CategoryRead.model_validate(db_obj)

    async def get_by_name(self, name: str) -> CategoryRead | None:
        """Get a category by name."""
        db_obj = await self.repository.get_by_name(name=name)
        return CategoryRead.model_validate(db_obj) if db_obj else None

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[CategoryRead]:
        """List all categories."""
        categories = await self.repository.list(skip=skip, limit=limit)
        return [CategoryRead.model_validate(cat) for cat in categories]

    async def update(
        self, category_id: int, category_in: CategoryUpdate
    ) -> CategoryRead:
        """Update a category."""
        # Get existing category
        await self.get(category_id=category_id)

        # If name is being updated, check for uniqueness
        if category_in.name is not None:
            existing = await self.get_by_name(name=category_in.name)
            if existing and existing.id != category_id:
                raise ResourceAlreadyExistsError(
                    "Category", f"name '{category_in.name}'"
                )

        # Get the DB object to update
        db_obj = await self.repository.get(category_id=category_id)

        # Update through repository
        updated = await self.repository.update(
            db_obj=db_obj, obj_in=category_in.model_dump(exclude_unset=True)
        )
        return CategoryRead.model_validate(updated)

    async def delete(self, category_id: int) -> None:
        """Delete a category."""
        # Check if exists using service's get method
        await self.get(category_id=category_id)

        await self.repository.delete(category_id=category_id)

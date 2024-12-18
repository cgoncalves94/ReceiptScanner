import logging
from collections.abc import Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import DomainException, ErrorCode
from app.models import CategoryCreate, CategoryRead, CategoryUpdate
from app.repositories import CategoryRepository

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.category_repo = CategoryRepository(db)

    async def create(self, category_in: CategoryCreate) -> CategoryRead:
        """Create a new category."""
        # Check if category with same name exists
        existing = await self.get_by_name(category_in.name)
        if existing:
            raise DomainException(
                ErrorCode.ALREADY_EXISTS,
                f"Category with name '{category_in.name}' already exists",
            )

        db_obj = await self.category_repo.create(category_in=category_in)
        return CategoryRead.model_validate(db_obj)

    async def get(self, category_id: int) -> CategoryRead:
        """Get a category by ID."""
        category = await self.category_repo.get(category_id=category_id)
        if not category:
            raise DomainException(
                ErrorCode.NOT_FOUND, f"Category with ID {category_id} not found"
            )
        return CategoryRead.model_validate(category)

    async def get_by_name(self, name: str) -> CategoryRead | None:
        """Get a category by name."""
        db_obj = await self.category_repo.get_by_name(name=name)
        return CategoryRead.model_validate(db_obj) if db_obj else None

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[CategoryRead]:
        """List all categories."""
        categories = await self.category_repo.list(skip=skip, limit=limit)
        return [CategoryRead.model_validate(cat) for cat in categories]

    async def update(
        self, category_id: int, category_in: CategoryUpdate
    ) -> CategoryRead:
        """Update a category."""
        # Get the category to update
        db_obj = await self.category_repo.get(category_id=category_id)
        if not db_obj:
            raise DomainException(
                ErrorCode.NOT_FOUND, f"Category with ID {category_id} not found"
            )

        # Update and return
        updated_obj = await self.category_repo.update(
            db_obj=db_obj, category_in=category_in
        )
        if not updated_obj:
            raise DomainException(
                ErrorCode.NOT_FOUND, f"Category with ID {category_id} not found"
            )
        return CategoryRead.model_validate(updated_obj)

    async def delete(self, category_id: int) -> None:
        """Delete a category."""
        await self.get(category_id)
        await self.category_repo.delete(category_id=category_id)

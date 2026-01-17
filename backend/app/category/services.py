from collections.abc import Sequence
from datetime import UTC, datetime

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.category.models import Category, CategoryCreate, CategoryUpdate
from app.core.exceptions import ConflictError, NotFoundError
from app.receipt.models import Receipt, ReceiptItem


class CategoryService:
    """Service for managing categories."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, category_in: CategoryCreate, user_id: int) -> Category:
        """Create a new category."""
        # Check if category with this name already exists for this user
        existing = await self.get_by_name(category_in.name, user_id)
        if existing:
            raise ConflictError(
                f"Category with name '{category_in.name}' already exists"
            )

        # Create new category with user_id
        category = Category(**category_in.model_dump(), user_id=user_id)
        self.session.add(category)
        await self.session.flush()
        return category

    async def get(self, category_id: int, user_id: int) -> Category:
        """Get a category by ID."""
        stmt = select(Category).where(
            Category.id == category_id, col(Category.user_id) == user_id
        )
        category = await self.session.scalar(stmt)
        if not category:
            raise NotFoundError(f"Category with ID {category_id} not found")
        return category

    async def get_by_name(self, name: str, user_id: int) -> Category | None:
        """Get a category by name for a specific user.

        Args:
            name: The category name to search for.
            user_id: The ID of the user whose categories to search.

        Returns:
            The category if found, None otherwise.
        """
        stmt = select(Category).where(
            Category.name == name, col(Category.user_id) == user_id
        )
        result: Category | None = await self.session.scalar(stmt)
        return result

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        user_id: int,
    ) -> Sequence[Category]:
        """List all categories."""
        stmt = (
            select(Category)
            .where(col(Category.user_id) == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def update(
        self, category_id: int, category_in: CategoryUpdate, user_id: int
    ) -> Category:
        """Update a category."""
        # Get the category
        category = await self.get(category_id, user_id)

        # If name is being updated, check for uniqueness within this user's categories
        if category_in.name is not None and category_in.name != category.name:
            existing = await self.get_by_name(category_in.name, user_id)
            if existing:
                raise ConflictError(
                    f"Category with name '{category_in.name}' already exists"
                )

        # Prepare update data
        update_data = category_in.model_dump(exclude_unset=True, exclude={"id"})

        # Update the category
        category.sqlmodel_update(update_data)
        category.updated_at = datetime.now(UTC)
        await self.session.flush()
        return category

    async def delete(self, category_id: int, user_id: int) -> None:
        """Delete a category.

        Raises ConflictError if the category has items assigned to it.
        """
        category = await self.get(category_id, user_id)

        # Check if any items belonging to this user are using this category
        stmt = (
            select(func.count(col(ReceiptItem.id)))
            .join(Receipt, col(ReceiptItem.receipt_id) == col(Receipt.id))
            .where(
                col(ReceiptItem.category_id) == category_id,
                col(Receipt.user_id) == user_id,
            )
        )
        item_count = await self.session.scalar(stmt)

        if item_count and item_count > 0:
            raise ConflictError(
                f"Cannot delete category '{category.name}': {item_count} item(s) are assigned to it. "
                "Please reassign or remove items first."
            )

        await self.session.delete(category)
        await self.session.flush()

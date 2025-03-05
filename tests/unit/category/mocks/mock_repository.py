"""Mock repository for category unit tests."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from app.domains.category.models import Category
from app.domains.category.repositories import CategoryRepository


class MockCategoryRepository(CategoryRepository):
    """Mock implementation of CategoryRepository for unit tests."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an in-memory store."""
        super().__init__(session)
        self._store: dict[int, Category] = {}
        self._next_id = 1
        self._name_index: dict[str, int] = {}

    async def create(self, category: Category) -> Category:
        """Create a category in memory."""
        # Set ID and timestamps
        category.id = self._next_id
        category.created_at = datetime.now(UTC)
        category.updated_at = datetime.now(UTC)

        # Store category
        self._store[category.id] = category
        self._name_index[category.name] = category.id
        self._next_id += 1

        return category

    async def get(self, category_id: int) -> Category | None:
        """Get category by ID from memory."""
        return self._store.get(category_id)

    async def get_by_name(self, name: str) -> Category | None:
        """Get category by name from memory."""
        category_id = self._name_index.get(name)
        return self._store.get(category_id) if category_id else None

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        """List categories from memory."""
        categories = list(self._store.values())
        return categories[skip : skip + limit]

    async def update(self, category: Category, update_data: dict) -> Category:
        """Update category in memory."""
        # Update name index if name is changing
        if "name" in update_data and update_data["name"] != category.name:
            del self._name_index[category.name]
            self._name_index[update_data["name"]] = category.id

        # Update category
        category.sqlmodel_update(update_data)
        category.updated_at = datetime.now(UTC)
        self._store[category.id] = category

        return category

    async def delete(self, category: Category) -> None:
        """Delete category from memory."""
        if category.id in self._store:
            del self._name_index[category.name]
            del self._store[category.id]

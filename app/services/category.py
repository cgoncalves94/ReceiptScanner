import logging
from collections.abc import Sequence

from sqlmodel import Session

from app.models import Category
from app.repositories import CategoryRepository
from app.schemas import CategoryCreate, CategoryUpdate

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.category_repo = CategoryRepository(db)

    def create_category(self, category_in: CategoryCreate) -> Category:
        """Create a new category."""
        # Check if category with same name already exists
        if self.category_repo.get_by_name(name=category_in.name):
            raise ValueError(f"Category with name '{category_in.name}' already exists")
        return self.category_repo.create(category_in=category_in)

    def get_or_create_categories(self, items_data: list[dict]) -> dict[str, Category]:
        """Get existing categories or create new ones using AI-generated descriptions."""
        category_map = {}

        # First, get all unique category names from items
        unique_categories = {
            item["category_name"]: item["category_description"] for item in items_data
        }

        # Then check which categories already exist
        for category_name, description in unique_categories.items():
            db_category = self.category_repo.get_by_name(name=category_name)
            if db_category:
                logger.info(f"Using existing category: {category_name}")
                category_map[category_name] = db_category
            else:
                logger.info(
                    f"Creating new category: {category_name} with description: {description}"
                )
                db_category = self.category_repo.create(
                    category_in=CategoryCreate(
                        name=category_name,
                        description=description,
                    )
                )
                category_map[category_name] = db_category

        return category_map

    def list_categories(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        """List all categories."""
        return self.category_repo.list(skip=skip, limit=limit)

    def get_category(self, category_id: int) -> Category:
        """Get a specific category by ID."""
        category = self.category_repo.get(category_id=category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found")
        return category

    def get_category_by_name(self, name: str) -> Category | None:
        """Get a specific category by name."""
        return self.category_repo.get_by_name(name=name)

    def update_category(
        self, category_id: int, category_in: CategoryUpdate
    ) -> Category:
        """Update a category."""
        db_obj = self.get_category(category_id)
        if category_in.name and category_in.name != db_obj.name:
            # Check if new name conflicts with existing category
            existing = self.get_category_by_name(category_in.name)
            if existing:
                raise ValueError(
                    f"Category with name '{category_in.name}' already exists"
                )
        return self.category_repo.update(db_obj=db_obj, category_in=category_in)

    def delete_category(self, category_id: int) -> None:
        """Delete a category."""
        # Check if category exists
        self.get_category(category_id)  # Will raise ValueError if not found
        self.category_repo.delete(category_id=category_id)

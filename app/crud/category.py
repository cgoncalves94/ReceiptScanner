from collections.abc import Sequence
from typing import cast

from sqlmodel import Field, Session, select

from app.models.receipt import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, category: Category) -> Category:
        """Create a new category."""
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get(self, category_id: int) -> Category | None:
        """Get a category by ID."""
        statement = select(Category).where(Category.id == category_id)
        return cast(Category | None, self.db.exec(statement).first())

    def get_by_name(self, name: str) -> Category | None:
        """Get a category by name."""
        statement = select(Category).where(cast(Field, Category.name) == name)
        return cast(Category | None, self.db.exec(statement).first())

    def list(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        """List all categories with pagination."""
        statement = select(Category).offset(skip).limit(limit)
        return cast(Sequence[Category], self.db.exec(statement).all())

    def update(self, category: Category) -> Category:
        """Update a category."""
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category_id: int) -> None:
        """Delete a category."""
        category = self.get(category_id)
        if category:
            self.db.delete(category)
            self.db.commit()

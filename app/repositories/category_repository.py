from collections.abc import Sequence
from typing import cast

from sqlmodel import Field, Session, select

from app.models.receipt import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Category | None:
        """Get a category by name."""
        statement = select(Category).where(cast(Field, Category.name) == name)
        return cast(Category | None, self.db.exec(statement).first())

    def create(self, category: Category) -> Category:
        """Create a new category."""
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def list(self) -> Sequence[Category]:
        """List all categories."""
        statement = select(Category)
        return cast(Sequence[Category], self.db.exec(statement).all())

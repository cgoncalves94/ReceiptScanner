from collections.abc import Sequence

from sqlmodel import Session, select

from app.models import Category
from app.schemas import CategoryCreate, CategoryUpdate


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, category_in: CategoryCreate) -> Category:
        """Create a new category."""
        db_obj = Category.model_validate(category_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, *, category_id: int) -> Category | None:
        """Get a category by ID."""
        statement = select(Category).filter_by(id=category_id)
        return self.db.exec(statement).first()

    def get_by_name(self, *, name: str) -> Category | None:
        """Get a category by name."""
        statement = select(Category).filter_by(name=name)
        return self.db.exec(statement).first()

    def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        """List all categories with pagination."""
        statement = select(Category).offset(skip).limit(limit)
        return self.db.exec(statement).all()

    def update(self, *, db_obj: Category, category_in: CategoryUpdate) -> Category:
        """Update a category."""
        category_data = category_in.model_dump(exclude_unset=True)
        db_obj.sqlmodel_update(category_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, *, category_id: int) -> None:
        """Delete a category."""
        db_obj = self.get(category_id=category_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()

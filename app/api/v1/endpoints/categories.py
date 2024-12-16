from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.deps import get_db
from app.models import Category
from app.schemas.category import Category as CategorySchema
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services import CategoryService

router = APIRouter()


@router.post("/", response_model=CategorySchema)
def create_category(
    category_in: CategoryCreate, db: Session = Depends(get_db)
) -> Category:
    """Create a new category."""
    category_service = CategoryService(db)
    try:
        return category_service.create_category(category_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[CategorySchema])
def list_categories(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> Sequence[Category]:
    """List all categories."""
    category_service = CategoryService(db)
    return category_service.list_categories(skip=skip, limit=limit)


@router.get("/{category_id}", response_model=CategorySchema)
def get_category(category_id: int, db: Session = Depends(get_db)) -> Category:
    """Get a specific category by ID."""
    category_service = CategoryService(db)
    try:
        return category_service.get_category(category_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int, category_in: CategoryUpdate, db: Session = Depends(get_db)
) -> Category:
    """Update a category."""
    category_service = CategoryService(db)
    try:
        return category_service.update_category(category_id, category_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a category."""
    category_service = CategoryService(db)
    try:
        category_service.delete_category(category_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

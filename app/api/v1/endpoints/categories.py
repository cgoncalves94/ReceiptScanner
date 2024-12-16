from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_category_service
from app.models import Category
from app.schemas import CategoryCreate, CategoryUpdate
from app.services import CategoryService

router = APIRouter()


@router.post("/", response_model=Category)
def create_category(
    category_in: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service),
) -> Category:
    """Create a new category."""
    try:
        return category_service.create_category(category_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Category])
def list_categories(
    skip: int = 0,
    limit: int = 100,
    category_service: CategoryService = Depends(get_category_service),
) -> Sequence[Category]:
    """List all categories."""
    return category_service.list_categories(skip=skip, limit=limit)


@router.get("/{category_id}", response_model=Category)
def get_category(
    category_id: int, category_service: CategoryService = Depends(get_category_service)
) -> Category:
    """Get a specific category by ID."""
    try:
        return category_service.get_category(category_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    category_service: CategoryService = Depends(get_category_service),
) -> Category:
    """Update a category."""
    try:
        return category_service.update_category(category_id, category_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{category_id}")
def delete_category(
    category_id: int, category_service: CategoryService = Depends(get_category_service)
) -> None:
    """Delete a category."""
    try:
        category_service.delete_category(category_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

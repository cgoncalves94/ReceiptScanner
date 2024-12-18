from fastapi import APIRouter, status

from app.api.deps import CategoryServiceDep
from app.models import (
    CategoriesRead,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)

router = APIRouter()


@router.post("/", response_model=CategoryRead)
async def create_category(
    category_in: CategoryCreate,
    service: CategoryServiceDep,
) -> CategoryRead:
    """Create a new category."""
    return await service.create(category_in)


@router.get("/", response_model=CategoriesRead)
async def list_categories(
    service: CategoryServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> CategoriesRead:
    """List all categories."""
    categories = await service.list(skip=skip, limit=limit)
    return CategoriesRead(data=categories, count=len(categories))


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    service: CategoryServiceDep,
) -> CategoryRead:
    """Get a specific category by ID."""
    return await service.get(category_id)


@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    service: CategoryServiceDep,
) -> CategoryRead:
    """Update a category."""
    return await service.update(category_id, category_in)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    service: CategoryServiceDep,
) -> None:
    """Delete a category."""
    await service.delete(category_id)

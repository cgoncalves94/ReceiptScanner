from fastapi import APIRouter, status

from .deps import CategoryDeps
from .models import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    service: CategoryDeps,
) -> CategoryRead:
    """Create a new category."""
    return await service.create(category_in)


@router.get("", response_model=list[CategoryRead], status_code=status.HTTP_200_OK)
async def list_categories(
    service: CategoryDeps,
    skip: int = 0,
    limit: int = 100,
) -> list[CategoryRead]:
    """List all categories."""
    return await service.list(skip=skip, limit=limit)


@router.get(
    "/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK
)
async def get_category(
    category_id: int,
    service: CategoryDeps,
) -> CategoryRead:
    """Get a specific category by ID."""
    return await service.get(category_id)


@router.patch(
    "/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK
)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    service: CategoryDeps,
) -> CategoryRead:
    """Update a category."""
    return await service.update(category_id, category_in)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    service: CategoryDeps,
) -> None:
    """Delete a category."""
    await service.delete(category_id)

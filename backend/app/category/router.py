from collections.abc import Sequence

from fastapi import APIRouter, status

from app.auth.deps import CurrentUser, require_user_id
from app.category.deps import CategoryDeps
from app.category.models import (
    Category,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    current_user: CurrentUser,
    service: CategoryDeps,
) -> Category:
    """Create a new category."""
    user_id = require_user_id(current_user)
    return await service.create(category_in, user_id=user_id)


@router.get("", response_model=list[CategoryRead], status_code=status.HTTP_200_OK)
async def list_categories(
    current_user: CurrentUser,
    service: CategoryDeps,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Category]:
    """List all categories."""
    user_id = require_user_id(current_user)
    return await service.list(skip=skip, limit=limit, user_id=user_id)


@router.get(
    "/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK
)
async def get_category(
    category_id: int,
    current_user: CurrentUser,
    service: CategoryDeps,
) -> Category:
    """Get a specific category by ID."""
    user_id = require_user_id(current_user)
    return await service.get(category_id, user_id=user_id)


@router.patch(
    "/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK
)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    current_user: CurrentUser,
    service: CategoryDeps,
) -> Category:
    """Update a category."""
    user_id = require_user_id(current_user)
    return await service.update(category_id, category_in, user_id=user_id)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: CurrentUser,
    service: CategoryDeps,
) -> None:
    """Delete a category."""
    user_id = require_user_id(current_user)
    await service.delete(category_id, user_id=user_id)

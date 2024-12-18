from collections.abc import Sequence

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CategoryServiceDep
from app.exceptions import DomainException, ErrorCode
from app.schemas import (
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
    try:
        return await service.create(category_in)
    except DomainException as e:
        if e.code == ErrorCode.ALREADY_EXISTS:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("/", response_model=list[CategoryRead])
async def list_categories(
    service: CategoryServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[CategoryRead]:
    """List all categories."""
    return await service.list(skip=skip, limit=limit)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    service: CategoryServiceDep,
) -> CategoryRead:
    """Get a specific category by ID."""
    try:
        return await service.get(category_id)
    except DomainException as e:
        if e.code == ErrorCode.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    service: CategoryServiceDep,
) -> CategoryRead:
    """Update a category."""
    try:
        return await service.update(category_id, category_in)
    except DomainException as e:
        if e.code == ErrorCode.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
        if e.code == ErrorCode.ALREADY_EXISTS:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    service: CategoryServiceDep,
) -> None:
    """Delete a category."""
    try:
        await service.delete(category_id)
    except DomainException as e:
        if e.code == ErrorCode.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

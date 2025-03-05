"""Unit tests for the category domain."""

from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.domains.category.models import Category, CategoryCreate, CategoryUpdate
from app.domains.category.services import CategoryService


@pytest.fixture
def mock_category_repo() -> AsyncMock:
    """Create a mock category repository."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def category_service(mock_category_repo: AsyncMock) -> CategoryService:
    """Create a CategoryService with a mock repository."""
    return CategoryService(mock_category_repo)


@pytest.mark.asyncio
async def test_create_category(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test creating a category."""
    # Arrange
    category_in = CategoryCreate(
        name="Test Category",
        description="Test Description",
    )
    mock_category_repo.get_by_name.return_value = None
    mock_category_repo.create.return_value = Category(
        id=1,
        name=category_in.name,
        description=category_in.description,
    )

    # Act
    created_category = await category_service.create(category_in)

    # Assert
    assert created_category.id == 1
    assert created_category.name == category_in.name
    assert created_category.description == category_in.description
    mock_category_repo.get_by_name.assert_called_once_with(category_in.name)
    mock_category_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_duplicate_category(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test creating a category with a duplicate name."""
    # Arrange
    category_in = CategoryCreate(
        name="Test Category",
        description="Test Description",
    )
    mock_category_repo.get_by_name.return_value = Category(
        id=1,
        name=category_in.name,
        description="Existing category",
    )

    # Act & Assert
    with pytest.raises(ConflictError) as exc_info:
        await category_service.create(category_in)
    assert "already exists" in str(exc_info.value)
    mock_category_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_category(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test getting a category by ID."""
    # Arrange
    category = Category(
        id=1,
        name="Test Category",
        description="Test Description",
    )
    mock_category_repo.get.return_value = category

    # Act
    retrieved_category = await category_service.get(category.id)

    # Assert
    assert retrieved_category.id == category.id
    assert retrieved_category.name == category.name
    assert retrieved_category.description == category.description
    mock_category_repo.get.assert_called_once_with(category.id)


@pytest.mark.asyncio
async def test_get_nonexistent_category(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test getting a category that doesn't exist."""
    # Arrange
    mock_category_repo.get.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await category_service.get(999)
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_categories(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test listing categories."""
    # Arrange
    categories = [
        Category(id=i, name=f"Category {i}", description=f"Description {i}")
        for i in range(1, 4)
    ]
    mock_category_repo.list.return_value = categories[:2]  # Return only first 2

    # Act
    retrieved_categories = await category_service.list(skip=0, limit=2)

    # Assert
    assert len(retrieved_categories) == 2
    mock_category_repo.list.assert_called_once_with(skip=0, limit=2)


@pytest.mark.asyncio
async def test_update_category(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test updating a category."""
    # Arrange
    existing_category = Category(
        id=1,
        name="Old Category",
        description="Old Description",
    )
    mock_category_repo.get.return_value = existing_category
    mock_category_repo.get_by_name.return_value = None

    update_data = CategoryUpdate(
        name="New Category",
        description="New Description",
    )

    mock_category_repo.update.return_value = Category(
        id=existing_category.id,
        name=update_data.name,
        description=update_data.description,
    )

    # Act
    updated_category = await category_service.update(existing_category.id, update_data)

    # Assert
    assert updated_category.name == update_data.name
    assert updated_category.description == update_data.description
    mock_category_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_category(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test updating a category that doesn't exist."""
    # Arrange
    mock_category_repo.get.return_value = None
    update_data = CategoryUpdate(
        name="New Category",
        description="New Description",
    )

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await category_service.update(999, update_data)
    assert "not found" in str(exc_info.value)
    mock_category_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_category_duplicate_name(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test updating a category with a name that already exists."""
    # Arrange
    existing_category = Category(
        id=1,
        name="Category 1",
        description="Description 1",
    )
    mock_category_repo.get.return_value = existing_category

    # Another category exists with the target name
    mock_category_repo.get_by_name.return_value = Category(
        id=2,
        name="Category 2",
        description="Description 2",
    )

    update_data = CategoryUpdate(name="Category 2")

    # Act & Assert
    with pytest.raises(ConflictError) as exc_info:
        await category_service.update(existing_category.id, update_data)
    assert "already exists" in str(exc_info.value)
    mock_category_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_delete_category(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test deleting a category."""
    # Arrange
    category = Category(
        id=1,
        name="Test Category",
        description="Test Description",
    )
    mock_category_repo.get.return_value = category

    # Act
    await category_service.delete(category.id)

    # Assert
    mock_category_repo.delete.assert_called_once_with(category)


@pytest.mark.asyncio
async def test_delete_nonexistent_category(
    category_service: CategoryService, mock_category_repo: AsyncMock
) -> None:
    """Test deleting a category that doesn't exist."""
    # Arrange
    mock_category_repo.get.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await category_service.delete(999)
    assert "not found" in str(exc_info.value)
    mock_category_repo.delete.assert_not_called()

"""Unit tests for the category domain."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.domains.category.models import Category, CategoryCreate, CategoryUpdate
from app.domains.category.services import CategoryService


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    mock = AsyncMock()
    # Configure add method to be a regular MagicMock, not a coroutine
    mock.add = MagicMock()
    return mock


@pytest.fixture
def category_service(mock_session: AsyncMock) -> CategoryService:
    """Create a CategoryService with a mock session."""
    return CategoryService(session=mock_session)


@pytest.mark.asyncio
async def test_create_category(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test creating a category."""
    # Arrange
    category_in = CategoryCreate(
        name="Test Category",
        description="Test Description",
    )
    # Mock the scalar method for get_by_name
    mock_session.scalar.return_value = None

    # Mock the flush method
    mock_session.flush = AsyncMock()

    # Act
    created_category = await category_service.create(category_in)

    # Assert
    assert created_category.name == category_in.name
    assert created_category.description == category_in.description
    mock_session.scalar.assert_called_once()
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_duplicate_category(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test creating a category with a duplicate name."""
    # Arrange
    category_in = CategoryCreate(
        name="Test Category",
        description="Test Description",
    )
    mock_session.scalar.return_value = Category(
        id=1,
        name=category_in.name,
        description="Existing category",
    )

    # Act & Assert
    with pytest.raises(ConflictError) as exc_info:
        await category_service.create(category_in)
    assert "already exists" in str(exc_info.value)
    mock_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_category(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test getting a category by ID."""
    # Arrange
    category = Category(
        id=1,
        name="Test Category",
        description="Test Description",
    )
    mock_session.scalar.return_value = category

    # Act
    retrieved_category = await category_service.get(category.id)

    # Assert
    assert retrieved_category.id == category.id
    assert retrieved_category.name == category.name
    assert retrieved_category.description == category.description
    mock_session.scalar.assert_called_once()


@pytest.mark.asyncio
async def test_get_nonexistent_category(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test getting a category that doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await category_service.get(999)
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_categories(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test listing categories."""
    # Arrange
    categories = [
        Category(id=i, name=f"Category {i}", description=f"Description {i}")
        for i in range(1, 4)
    ]
    # Mock the session.scalars().all() chain
    mock_session.scalars = AsyncMock()
    # Make scalars() return an object with a non-coroutine all() method
    mock_session.scalars.return_value = MagicMock()
    mock_session.scalars.return_value.all.return_value = categories[
        :2
    ]  # Return only first 2

    # Act
    retrieved_categories = await category_service.list(skip=0, limit=2)

    # Assert
    assert len(retrieved_categories) == 2
    mock_session.scalars.assert_called_once()


@pytest.mark.asyncio
async def test_update_category(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test updating a category."""
    # Arrange
    existing_category = Category(
        id=1,
        name="Old Category",
        description="Old Description",
    )

    # First call to scalar for get
    # Second call to scalar for get_by_name
    mock_session.scalar.side_effect = [existing_category, None]

    # Mock the flush method
    mock_session.flush = AsyncMock()

    update_data = CategoryUpdate(
        name="New Category",
        description="New Description",
    )

    # Act
    updated_category = await category_service.update(existing_category.id, update_data)

    # Assert
    assert updated_category.name == update_data.name
    assert updated_category.description == update_data.description
    assert mock_session.scalar.call_count == 2
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_category(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test updating a category that doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None
    update_data = CategoryUpdate(
        name="New Category",
        description="New Description",
    )

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await category_service.update(999, update_data)
    assert "not found" in str(exc_info.value)
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_category_duplicate_name(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test updating a category with a name that already exists."""
    # Arrange
    existing_category = Category(
        id=1,
        name="Category 1",
        description="Description 1",
    )

    # First call to scalar for get
    # Second call to scalar for get_by_name
    mock_session.scalar.side_effect = [
        existing_category,
        Category(
            id=2,
            name="Category 2",
            description="Description 2",
        ),
    ]

    update_data = CategoryUpdate(name="Category 2")

    # Act & Assert
    with pytest.raises(ConflictError) as exc_info:
        await category_service.update(existing_category.id, update_data)
    assert "already exists" in str(exc_info.value)
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_delete_category(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test deleting a category."""
    # Arrange
    category = Category(
        id=1,
        name="Test Category",
        description="Test Description",
    )
    mock_session.scalar.return_value = category

    # Mock the delete and flush methods
    mock_session.delete = AsyncMock()
    mock_session.flush = AsyncMock()

    # Act
    await category_service.delete(category.id)

    # Assert
    mock_session.delete.assert_called_once_with(category)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_delete_nonexistent_category(
    category_service: CategoryService, mock_session: AsyncMock
) -> None:
    """Test deleting a category that doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None

    # Mock the delete method
    mock_session.delete = AsyncMock()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await category_service.delete(999)
    assert "not found" in str(exc_info.value)
    mock_session.delete.assert_not_called()

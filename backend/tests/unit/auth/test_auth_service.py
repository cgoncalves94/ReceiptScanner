"""Unit tests for the auth service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.models import User, UserCreate, UserUpdate
from app.auth.services import AuthService
from app.core.exceptions import ConflictError, NotFoundError


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    mock = AsyncMock()
    # Configure add method to be a regular MagicMock, not a coroutine
    mock.add = MagicMock()
    return mock


@pytest.fixture
def auth_service(mock_session: AsyncMock) -> AuthService:
    """Create an AuthService with a mock session."""
    return AuthService(session=mock_session)


@pytest.mark.asyncio
@patch("app.auth.services.hash_password")
async def test_register_user(
    mock_hash: MagicMock, auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test registering a new user."""
    # Arrange
    user_in = UserCreate(
        email="test@example.com",
        password="securepassword123",
    )
    mock_hash.return_value = "hashed_password"
    # Mock get_user_by_email to return None (no existing user)
    mock_session.scalar.return_value = None
    mock_session.flush = AsyncMock()

    # Act
    created_user = await auth_service.register_user(user_in)

    # Assert
    assert created_user.email == user_in.email
    assert created_user.hashed_password == "hashed_password"
    assert created_user.is_active is True
    mock_hash.assert_called_once_with(user_in.password)
    mock_session.scalar.assert_called_once()
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_register_duplicate_user(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test registering a user with an email that already exists."""
    # Arrange
    user_in = UserCreate(
        email="test@example.com",
        password="securepassword123",
    )
    # Mock get_user_by_email to return existing user
    mock_session.scalar.return_value = User(
        id=1,
        email=user_in.email,
        hashed_password="existing_hash",
    )

    # Act & Assert
    with pytest.raises(ConflictError) as exc_info:
        await auth_service.register_user(user_in)
    assert "already exists" in str(exc_info.value)
    mock_session.add.assert_not_called()


@pytest.mark.asyncio
@patch("app.auth.services.verify_password")
async def test_authenticate_user_success(
    mock_verify: MagicMock, auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test authenticating a user with valid credentials."""
    # Arrange
    email = "test@example.com"
    password = "securepassword123"
    user = User(
        id=1,
        email=email,
        hashed_password="hashed_password",
        is_active=True,
    )
    mock_session.scalar.return_value = user
    mock_verify.return_value = True

    # Act
    authenticated_user = await auth_service.authenticate_user(email, password)

    # Assert
    assert authenticated_user.id == user.id
    assert authenticated_user.email == email
    mock_session.scalar.assert_called_once()
    mock_verify.assert_called_once_with(password, user.hashed_password)


@pytest.mark.asyncio
async def test_authenticate_user_invalid_email(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test authenticating with an invalid email."""
    # Arrange
    mock_session.scalar.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await auth_service.authenticate_user("invalid@example.com", "password")
    assert "Invalid email or password" in str(exc_info.value)


@pytest.mark.asyncio
@patch("app.auth.services.verify_password")
async def test_authenticate_user_invalid_password(
    mock_verify: MagicMock, auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test authenticating with an invalid password."""
    # Arrange
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
    )
    mock_session.scalar.return_value = user
    mock_verify.return_value = False

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await auth_service.authenticate_user("test@example.com", "wrongpassword")
    assert "Invalid email or password" in str(exc_info.value)


@pytest.mark.asyncio
@patch("app.auth.services.verify_password")
async def test_authenticate_inactive_user(
    mock_verify: MagicMock, auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test authenticating an inactive user."""
    # Arrange
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=False,
    )
    mock_session.scalar.return_value = user
    mock_verify.return_value = True

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await auth_service.authenticate_user("test@example.com", "password")
    assert "inactive" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_by_email_found(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test getting a user by email when user exists."""
    # Arrange
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
    )
    mock_session.scalar.return_value = user

    # Act
    result = await auth_service.get_user_by_email("test@example.com")

    # Assert
    assert result is not None
    assert result.id == user.id
    assert result.email == user.email
    mock_session.scalar.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test getting a user by email when user doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None

    # Act
    result = await auth_service.get_user_by_email("nonexistent@example.com")

    # Assert
    assert result is None
    mock_session.scalar.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_id_found(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test getting a user by ID when user exists."""
    # Arrange
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
    )
    assert user.id is not None
    mock_session.scalar.return_value = user

    # Act
    result = await auth_service.get_user_by_id(user.id)

    # Assert
    assert result.id == user.id
    assert result.email == user.email
    mock_session.scalar.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test getting a user by ID when user doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await auth_service.get_user_by_id(999)
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
@patch("app.auth.services.hash_password")
async def test_update_user_password(
    mock_hash: MagicMock, auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test updating a user's password."""
    # Arrange
    existing_user = User(
        id=1,
        email="test@example.com",
        hashed_password="old_hash",
    )
    assert existing_user.id is not None

    mock_session.scalar.return_value = existing_user
    mock_session.flush = AsyncMock()
    mock_hash.return_value = "new_hash"

    update_data = UserUpdate(password="newpassword123")

    # Act
    updated_user = await auth_service.update_user(existing_user.id, update_data)

    # Assert
    assert updated_user.hashed_password == "new_hash"
    mock_hash.assert_called_once_with("newpassword123")
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_email(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test updating a user's email."""
    # Arrange
    existing_user = User(
        id=1,
        email="old@example.com",
        hashed_password="hash",
    )
    assert existing_user.id is not None

    # First call for get_user_by_id, second for email uniqueness check
    mock_session.scalar.side_effect = [existing_user, None]
    mock_session.flush = AsyncMock()

    update_data = UserUpdate(email="new@example.com")

    # Act
    updated_user = await auth_service.update_user(existing_user.id, update_data)

    # Assert
    assert updated_user.email == "new@example.com"
    assert mock_session.scalar.call_count == 2
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_email_conflict(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test updating a user's email to one that already exists."""
    # Arrange
    existing_user = User(
        id=1,
        email="old@example.com",
        hashed_password="hash",
    )
    conflicting_user = User(
        id=2,
        email="new@example.com",
        hashed_password="hash",
    )
    assert existing_user.id is not None

    # First call for get_user_by_id, second for email uniqueness check
    mock_session.scalar.side_effect = [existing_user, conflicting_user]

    update_data = UserUpdate(email="new@example.com")

    # Act & Assert
    with pytest.raises(ConflictError) as exc_info:
        await auth_service.update_user(existing_user.id, update_data)
    assert "already exists" in str(exc_info.value)
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_user_is_active(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test updating a user's is_active status."""
    # Arrange
    existing_user = User(
        id=1,
        email="test@example.com",
        hashed_password="hash",
        is_active=True,
    )
    assert existing_user.id is not None

    mock_session.scalar.return_value = existing_user
    mock_session.flush = AsyncMock()

    update_data = UserUpdate(is_active=False)

    # Act
    updated_user = await auth_service.update_user(existing_user.id, update_data)

    # Assert
    assert updated_user.is_active is False
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_user(
    auth_service: AuthService, mock_session: AsyncMock
) -> None:
    """Test updating a user that doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None
    update_data = UserUpdate(email="new@example.com")

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await auth_service.update_user(999, update_data)
    assert "not found" in str(exc_info.value)
    mock_session.flush.assert_not_called()

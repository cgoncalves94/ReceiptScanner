"""Tests for the auth API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils import hash_password


def test_register_user(test_client: TestClient) -> None:
    """Test registering a new user via API."""
    # Arrange
    user_data = {
        "email": "test@example.com",
        "password": "securepassword123",
    }

    # Act
    response = test_client.post("/api/v1/auth/register", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "hashed_password" not in data  # Should not expose password
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test registering a user with an email that already exists."""
    # Arrange: Create existing user
    existing_user = User(
        email="existing@example.com",
        hashed_password=hash_password("password123"),
    )
    test_session.add(existing_user)
    await test_session.commit()

    # Act: Try to register with same email
    response = test_client.post(
        "/api/v1/auth/register",
        json={"email": "existing@example.com", "password": "newpassword456"},
    )

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test successful login returns an access token."""
    # Arrange: Create a user
    user = User(
        email="login@example.com",
        hashed_password=hash_password("mypassword"),
    )
    test_session.add(user)
    await test_session.commit()

    # Act: Login with correct credentials
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "mypassword"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_email(test_client: TestClient) -> None:
    """Test login with non-existent email returns 404."""
    # Act: Try to login with non-existent email
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )

    # Assert
    assert response.status_code == 404
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_invalid_password(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test login with incorrect password returns 404."""
    # Arrange: Create a user
    user = User(
        email="wrongpass@example.com",
        hashed_password=hash_password("correctpassword"),
    )
    test_session.add(user)
    await test_session.commit()

    # Act: Try to login with wrong password
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "wrongpassword"},
    )

    # Assert
    assert response.status_code == 404
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test login with inactive user returns 404."""
    # Arrange: Create an inactive user
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("password123"),
        is_active=False,
    )
    test_session.add(user)
    await test_session.commit()

    # Act: Try to login with inactive account
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "password123"},
    )

    # Assert
    assert response.status_code == 404
    assert "inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_current_user(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test getting current user info with valid token."""
    # Arrange: Create a user and login to get token
    user = User(
        email="currentuser@example.com",
        hashed_password=hash_password("password123"),
    )
    test_session.add(user)
    await test_session.commit()

    # Login to get token
    login_response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "currentuser@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Act: Get current user with token
    response = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "currentuser@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "hashed_password" not in data


def test_get_current_user_unauthorized(test_client: TestClient) -> None:
    """Test getting current user without token returns 401."""
    # Act: Try to get current user without token
    response = test_client.get("/api/v1/auth/me")

    # Assert
    assert response.status_code == 401


def test_get_current_user_invalid_token(test_client: TestClient) -> None:
    """Test getting current user with invalid token returns 401."""
    # Act: Try to get current user with invalid token
    response = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"},
    )

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_invalid_email_format(test_client: TestClient) -> None:
    """Test registering with invalid email format returns validation error."""
    # Act: Try to register with invalid email
    response = test_client.post(
        "/api/v1/auth/register",
        json={"email": "ab", "password": "password123"},  # Too short
    )

    # Assert
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_short_password(test_client: TestClient) -> None:
    """Test registering with password less than 8 characters returns validation error."""
    # Act: Try to register with short password
    response = test_client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "short"},  # Only 5 chars
    )

    # Assert
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_after_registration(test_client: TestClient) -> None:
    """Test that a user can login immediately after registration."""
    # Arrange: Register a new user
    user_data = {"email": "newuser@example.com", "password": "password123"}
    register_response = test_client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201

    # Act: Login with same credentials
    login_response = test_client.post("/api/v1/auth/login", json=user_data)

    # Assert
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

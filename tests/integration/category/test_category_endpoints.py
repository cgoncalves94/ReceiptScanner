"""Tests for the category API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.category.models import Category


def test_create_category(test_client: TestClient) -> None:
    """Test creating a category via API."""
    # Arrange
    category_data = {
        "name": "Test Category",
        "description": "Test Description",
    }

    # Act
    response = test_client.post("/api/v1/categories/", json=category_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == category_data["name"]
    assert data["description"] == category_data["description"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_category(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test getting a category by ID via API."""
    # Arrange
    category = Category(name="Test Category", description="Test Description")
    test_session.add(category)
    await test_session.commit()

    # Act
    response = test_client.get(f"/api/v1/categories/{category.id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == category.id
    assert data["name"] == category.name
    assert data["description"] == category.description


@pytest.mark.asyncio
async def test_list_categories(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test listing categories via API."""
    # Arrange
    categories = [
        Category(name=f"Category {i}", description=f"Description {i}") for i in range(3)
    ]
    test_session.add_all(categories)
    await test_session.commit()

    # Act
    response = test_client.get("/api/v1/categories/")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("id" in category for category in data)
    assert all("name" in category for category in data)
    assert all("description" in category for category in data)


@pytest.mark.asyncio
async def test_update_category(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test updating a category via API."""
    # Arrange
    category = Category(name="Old Name", description="Old Description")
    test_session.add(category)
    await test_session.commit()

    update_data = {
        "name": "New Name",
        "description": "New Description",
    }

    # Act
    response = test_client.patch(
        f"/api/v1/categories/{category.id}",
        json=update_data,
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == category.id
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


@pytest.mark.asyncio
async def test_delete_category(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test deleting a category via API."""
    # Arrange
    category = Category(name="Test Category", description="Test Description")
    test_session.add(category)
    await test_session.commit()

    # Act
    response = test_client.delete(f"/api/v1/categories/{category.id}")

    # Assert
    assert response.status_code == 204

    # Verify category is deleted
    get_response = test_client.get(f"/api/v1/categories/{category.id}")
    assert get_response.status_code == 404


def test_get_nonexistent_category(test_client: TestClient) -> None:
    """Test getting a category that doesn't exist."""
    response = test_client.get("/api/v1/categories/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_duplicate_category(
    test_client: TestClient, test_session: AsyncSession
) -> None:
    """Test creating a category with a name that already exists."""
    # Arrange
    category = Category(name="Test Category", description="Test Description")
    test_session.add(category)
    await test_session.commit()

    # Act
    response = test_client.post(
        "/api/v1/categories/",
        json={"name": "Test Category", "description": "New Description"},
    )

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

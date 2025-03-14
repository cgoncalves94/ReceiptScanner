"""Unit tests for the main module."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_root_endpoint(test_client):
    """Test the root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Warestack Core API!"}


@pytest.mark.asyncio
async def test_healthcheck_endpoint():
    """Test the healthcheck endpoint."""
    # Mock the check_db_connection function to return True
    with patch("app.main.check_db_connection", AsyncMock(return_value=True)):
        # Use TestClient in a context manager to ensure proper cleanup
        with TestClient(app) as client:
            response = client.get("/healthcheck")
            assert response.status_code == 200
            assert response.json() == {
                "status": "healthy",
                "database": "connected",
            }


@pytest.mark.asyncio
async def test_healthcheck_endpoint_db_disconnected():
    """Test the healthcheck endpoint when the database is disconnected."""
    # Mock the check_db_connection function to return False
    with patch("app.main.check_db_connection", AsyncMock(return_value=False)):
        # Use TestClient in a context manager to ensure proper cleanup
        with TestClient(app) as client:
            response = client.get("/healthcheck")
            assert response.status_code == 200
            assert response.json() == {
                "status": "healthy",
                "database": "disconnected",
            }


@pytest.mark.asyncio
async def test_lifespan_exception_handling():
    """Test exception handling in the lifespan function."""
    # Mock init_db to raise a SQLAlchemyError
    from sqlalchemy.exc import SQLAlchemyError

    with patch(
        "app.main.init_db", AsyncMock(side_effect=SQLAlchemyError("Test error"))
    ):
        # Create a new FastAPI app with the mocked lifespan
        from fastapi import FastAPI

        from app.main import lifespan

        test_app = FastAPI(lifespan=lifespan)

        # Use TestClient to trigger the lifespan
        with pytest.raises(SQLAlchemyError):
            with TestClient(test_app):
                pass  # The exception should be raised when entering the context

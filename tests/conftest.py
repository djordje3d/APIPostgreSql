"""Pytest fixtures for API integration tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


# pytest fixture for the HTTP client
# pytest fixture for the database session
# pytest fixture for the database engine
# pytest fixture for the database
# pytest fixture for the database models
# pytest fixture for the database schemas
# pytest fixture for the database routers
# pytest fixture for the database services
# pytest fixture for the database utils
# pytest fixture for the database tests
# pytest fixture for the database test client
# pytest fixture for the database test database
# pytest fixture for the database test database engine
# pytest fixture for the database test database models
# pytest fixture for the database test database schemas
# pytest fixture for the database test database routers
@pytest.fixture
def client() -> TestClient:
    """HTTP client for testing the API. Uses the real app and database."""
    return TestClient(app)

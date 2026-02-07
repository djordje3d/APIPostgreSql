"""Pytest fixtures for API integration tests with transactional rollback isolation."""

import os

# So tests work without DB triggers: API computes fee on exit and payment_status after payments.
os.environ.setdefault("USE_API_FEE_CALCULATION", "true")
os.environ.setdefault("USE_API_PAYMENT_STATUS", "true")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_db, engine

# Session bound to a connection; we control the transaction and roll back after each test.
_SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def _reset_sequences() -> None:
    """Ensure sequences are ahead of max(id) to avoid duplicate key errors when rolling back."""
    tables_serial = [
        ("vehicle", "id"),
        ("vehicle_types", "id"),
        ("parking_config", "id"),
        ("parking_spot", "id"),
        ("tickets", "id"),
        ("payments", "id"),
    ]
    with engine.connect() as conn:
        for table, col in tables_serial:
            # Set sequence to max(id)+1 so next insert gets a new id (identifiers are from our list).
            conn.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
                )
            )
        conn.commit()


@pytest.fixture(scope="session", autouse=True)
def _reset_db_sequences() -> None:
    """Reset sequences once per test run so inserts get unique ids after rollbacks."""
    _reset_sequences()


@pytest.fixture
def client() -> TestClient:
    """
    HTTP client for testing the API. Each test runs inside a transaction that is
    rolled back at the end, so the database is not modified and tests are isolated.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = _SessionLocal(bind=connection)

    # Make commit() only flush, so the app thinks it committed but we can roll back later.
    def fake_commit():
        session.flush()

    session.commit = fake_commit  # type: ignore[method-assign]

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()

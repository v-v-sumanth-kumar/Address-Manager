"""Shared pytest fixtures for API integration tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite://"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional in-memory database session for each test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI test client with overridden database dependency."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_address_payload() -> dict[str, object]:
    """Return a valid address payload for create requests."""
    return {
        "name": "Acme Corporation",
        "address_line1": "123 Main Street",
        "address_line2": "Suite 400",
        "city": "San Francisco",
        "state": "CA",
        "country": "United States",
        "postal_code": "94105",
        "latitude": 37.7749,
        "longitude": -122.4194,
    }


@pytest.fixture
def created_address(client: TestClient, sample_address_payload: dict[str, object]) -> dict:
    """Create and return an address via the API."""
    response = client.post("/addresses", json=sample_address_payload)
    assert response.status_code == 201
    return response.json()["data"]

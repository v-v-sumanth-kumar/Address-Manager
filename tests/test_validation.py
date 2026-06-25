"""Tests for request validation and error responses."""

from fastapi.testclient import TestClient


def test_create_address_invalid_latitude(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Latitude outside valid range returns 422."""
    payload = {**sample_address_payload, "latitude": 95.0}
    response = client.post("/addresses", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "latitude" in body["message"].lower()


def test_create_address_invalid_longitude(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Longitude outside valid range returns 422."""
    payload = {**sample_address_payload, "longitude": 200.0}
    response = client.post("/addresses", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "longitude" in body["message"].lower()


def test_create_address_blank_name(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Blank required string fields return 422."""
    payload = {**sample_address_payload, "name": "   "}
    response = client.post("/addresses", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False


def test_create_address_empty_postal_code(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Empty postal code returns 422."""
    payload = {**sample_address_payload, "postal_code": ""}
    response = client.post("/addresses", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False


def test_create_address_missing_required_field(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Missing required fields return 422 with consistent error format."""
    payload = {k: v for k, v in sample_address_payload.items() if k != "city"}
    response = client.post("/addresses", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "city" in body["message"].lower()


def test_nearby_invalid_latitude(client: TestClient) -> None:
    """Invalid nearby search latitude returns 422."""
    response = client.get(
        "/addresses/nearby",
        params={"latitude": 100.0, "longitude": 0.0, "distance_km": 10},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False


def test_nearby_invalid_longitude(client: TestClient) -> None:
    """Invalid nearby search longitude returns 422."""
    response = client.get(
        "/addresses/nearby",
        params={"latitude": 0.0, "longitude": -200.0, "distance_km": 10},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False


def test_nearby_invalid_distance(client: TestClient) -> None:
    """Non-positive distance_km returns 422."""
    response = client.get(
        "/addresses/nearby",
        params={"latitude": 0.0, "longitude": 0.0, "distance_km": 0},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False


def test_invalid_uuid_format(client: TestClient) -> None:
    """Invalid UUID path parameter returns 422."""
    response = client.get("/addresses/not-a-uuid")

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False


def test_format_validation_errors_helper() -> None:
    """Validation error formatter produces readable messages."""
    from app.schemas.address import format_validation_errors

    errors = [{"loc": ("body", "name"), "msg": "Field required"}]
    message = format_validation_errors(errors)
    assert "body.name" in message
    assert "Field required" in message

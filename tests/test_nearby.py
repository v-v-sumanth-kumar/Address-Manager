"""Tests for nearby address search endpoint."""

from fastapi.testclient import TestClient


def test_nearby_search_finds_close_addresses(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Nearby search returns addresses within the specified radius."""
    client.post("/addresses", json=sample_address_payload)

    far_payload = {
        **sample_address_payload,
        "name": "Far Away Office",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "city": "New York",
    }
    client.post("/addresses", json=far_payload)

    response = client.get(
        "/addresses/nearby",
        params={"latitude": 37.7749, "longitude": -122.4194, "distance_km": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Acme Corporation"
    assert "distance_km" in body["data"][0]
    assert body["data"][0]["distance_km"] == 0.0


def test_nearby_search_sorted_by_distance(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Nearby results are sorted by ascending distance."""
    near_payload = {
        **sample_address_payload,
        "name": "Near Office",
        "latitude": 37.7750,
        "longitude": -122.4195,
    }
    farther_payload = {
        **sample_address_payload,
        "name": "Farther Office",
        "latitude": 37.8000,
        "longitude": -122.4000,
    }
    client.post("/addresses", json=farther_payload)
    client.post("/addresses", json=near_payload)

    response = client.get(
        "/addresses/nearby",
        params={"latitude": 37.7749, "longitude": -122.4194, "distance_km": 50},
    )

    assert response.status_code == 200
    distances = [item["distance_km"] for item in response.json()["data"]]
    assert distances == sorted(distances)


def test_nearby_search_no_results(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Nearby search returns an empty list when no addresses match."""
    client.post("/addresses", json=sample_address_payload)

    response = client.get(
        "/addresses/nearby",
        params={"latitude": 0.0, "longitude": 0.0, "distance_km": 1},
    )

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_haversine_distance_calculation() -> None:
    """Haversine utility computes known distance between two cities."""
    from app.utils.geo import haversine_distance_km

    # Approximate distance San Francisco to Los Angeles ~ 559 km
    distance = haversine_distance_km(37.7749, -122.4194, 34.0522, -118.2437)
    assert 540 < distance < 580

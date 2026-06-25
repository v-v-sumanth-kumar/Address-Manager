"""Tests for address creation and retrieval endpoints."""

from fastapi.testclient import TestClient


def test_create_address_success(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Creating a valid address returns 201 with success wrapper."""
    response = client.post("/addresses", json=sample_address_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == sample_address_payload["name"]
    assert body["data"]["city"] == sample_address_payload["city"]
    assert "id" in body["data"]
    assert "created_at" in body["data"]
    assert "updated_at" in body["data"]


def test_get_address_success(client: TestClient, created_address: dict) -> None:
    """Retrieving an existing address returns 200 with the correct data."""
    address_id = created_address["id"]
    response = client.get(f"/addresses/{address_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == address_id
    assert body["data"]["name"] == created_address["name"]


def test_list_addresses_pagination(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Listing addresses returns paginated results with metadata."""
    for index in range(3):
        payload = {**sample_address_payload, "name": f"Company {index}"}
        client.post("/addresses", json=payload)

    response = client.get("/addresses", params={"page": 1, "page_size": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["items"]) == 2
    assert body["data"]["pagination"]["total_items"] == 3
    assert body["data"]["pagination"]["total_pages"] == 2
    assert body["data"]["pagination"]["has_next"] is True


def test_list_addresses_sort_by_name(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Addresses can be sorted by name in ascending order."""
    for name in ["Zebra Inc", "Alpha Inc"]:
        payload = {**sample_address_payload, "name": name}
        client.post("/addresses", json=payload)

    response = client.get("/addresses", params={"sort_by": "name", "sort_order": "asc"})

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["data"]["items"]]
    assert names == sorted(names)


def test_list_addresses_filter_by_country(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Country filter returns only matching addresses."""
    client.post("/addresses", json=sample_address_payload)
    canada_payload = {**sample_address_payload, "country": "Canada", "name": "Maple Co"}
    client.post("/addresses", json=canada_payload)

    response = client.get("/addresses", params={"country": "United"})

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["country"] == "United States"


def test_list_addresses_search_by_name(
    client: TestClient,
    sample_address_payload: dict[str, object],
) -> None:
    """Name search matches partial name or city values."""
    client.post("/addresses", json=sample_address_payload)
    other_payload = {**sample_address_payload, "name": "Other Corp", "city": "Oakland"}
    client.post("/addresses", json=other_payload)

    response = client.get("/addresses", params={"name": "Acme"})

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Acme Corporation"


def test_health_endpoint(client: TestClient) -> None:
    """Health endpoint returns healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"

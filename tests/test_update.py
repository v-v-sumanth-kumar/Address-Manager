"""Tests for address update endpoint."""

from fastapi.testclient import TestClient


def test_update_address_success(client: TestClient, created_address: dict) -> None:
    """Updating an existing address returns the modified record."""
    address_id = created_address["id"]
    update_payload = {"name": "Acme Corp HQ", "city": "Oakland"}

    response = client.put(f"/addresses/{address_id}", json=update_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Acme Corp HQ"
    assert body["data"]["city"] == "Oakland"
    assert body["data"]["state"] == created_address["state"]


def test_update_address_not_found(client: TestClient) -> None:
    """Updating a non-existent address returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000001"
    response = client.put(f"/addresses/{fake_id}", json={"name": "Ghost"})

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Address not found"


def test_update_address_empty_payload(client: TestClient, created_address: dict) -> None:
    """Updating with an empty payload returns 422."""
    address_id = created_address["id"]
    response = client.put(f"/addresses/{address_id}", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False

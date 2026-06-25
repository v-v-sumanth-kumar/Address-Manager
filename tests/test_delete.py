"""Tests for address deletion endpoint."""

from fastapi.testclient import TestClient


def test_delete_address_success(client: TestClient, created_address: dict) -> None:
    """Deleting an existing address returns success and removes the record."""
    address_id = created_address["id"]
    response = client.delete(f"/addresses/{address_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["message"] == "Address deleted successfully"

    get_response = client.get(f"/addresses/{address_id}")
    assert get_response.status_code == 404


def test_delete_address_not_found(client: TestClient) -> None:
    """Deleting a non-existent address returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000002"
    response = client.delete(f"/addresses/{fake_id}")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Address not found"


def test_get_address_not_found(client: TestClient) -> None:
    """Retrieving a non-existent address returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000003"
    response = client.get(f"/addresses/{fake_id}")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Address not found"

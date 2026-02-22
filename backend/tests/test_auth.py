import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    response = await client.post(
        "/api/v1/auth/register",
        json={"device_id": "test-device-001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["device_id"] == "test-device-001"
    assert data["user"]["subscription_tier"] == "free"

    # Login with same device
    response = await client.post(
        "/api/v1/auth/login",
        json={"device_id": "test-device-001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"device_id": "test-device-dup"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"device_id": "test-device-dup"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_not_found(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"device_id": "nonexistent-device"},
    )
    assert response.status_code == 404

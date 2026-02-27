from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.services.receipt_validator import ValidationResult


async def _register_and_get_token(client: AsyncClient, device_id: str = "sub-test-device") -> str:
    """Helper: register a user and return auth token."""
    resp = await client.post("/api/v1/auth/register", json={"device_id": device_id})
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.mark.asyncio
async def test_verify_receipt_pro_subscription_ios(client: AsyncClient):
    """Test successful Pro subscription verification via iOS."""
    token = await _register_and_get_token(client, "ios-pro-device")

    mock_result = ValidationResult(
        valid=True,
        product_id="com.endlessrumination.pro.monthly",
        is_subscription=True,
        expires_at="2026-03-26T00:00:00+00:00",
    )

    with patch(
        "app.routers.subscription._get_apple_validator"
    ) as mock_get_validator:
        mock_validator = AsyncMock()
        mock_validator.validate_purchase = AsyncMock(return_value=mock_result)
        mock_get_validator.return_value = mock_validator

        resp = await client.post(
            "/api/v1/subscription/verify-receipt",
            json={
                "platform": "ios",
                "product_id": "com.endlessrumination.pro.monthly",
                "purchase_token": "fake-ios-token-123",
                "is_subscription": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["product_id"] == "com.endlessrumination.pro.monthly"
    assert data["is_subscription"] is True


@pytest.mark.asyncio
async def test_verify_receipt_pack_android(client: AsyncClient):
    """Test successful voice pack purchase verification via Android."""
    token = await _register_and_get_token(client, "android-pack-device")

    mock_result = ValidationResult(
        valid=True,
        product_id="com.endlessrumination.pack.strategists",
        is_subscription=False,
    )

    with patch(
        "app.routers.subscription._get_google_validator"
    ) as mock_get_validator:
        mock_validator = AsyncMock()
        mock_validator.validate_purchase = AsyncMock(return_value=mock_result)
        mock_get_validator.return_value = mock_validator

        resp = await client.post(
            "/api/v1/subscription/verify-receipt",
            json={
                "platform": "android",
                "product_id": "com.endlessrumination.pack.strategists",
                "purchase_token": "fake-android-token-456",
                "is_subscription": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["product_id"] == "com.endlessrumination.pack.strategists"
    assert data["is_subscription"] is False


@pytest.mark.asyncio
async def test_verify_receipt_invalid_receipt(client: AsyncClient):
    """Test receipt validation failure returns 400."""
    token = await _register_and_get_token(client, "invalid-receipt-device")

    mock_result = ValidationResult(
        valid=False,
        error="Transaction not found on Apple servers",
    )

    with patch(
        "app.routers.subscription._get_apple_validator"
    ) as mock_get_validator:
        mock_validator = AsyncMock()
        mock_validator.validate_purchase = AsyncMock(return_value=mock_result)
        mock_get_validator.return_value = mock_validator

        resp = await client.post(
            "/api/v1/subscription/verify-receipt",
            json={
                "platform": "ios",
                "product_id": "com.endlessrumination.pro.monthly",
                "purchase_token": "invalid-token",
                "is_subscription": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 400
    assert "validation failed" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_receipt_no_auth(client: AsyncClient):
    """Test verify-receipt without auth returns 401/403."""
    resp = await client.post(
        "/api/v1/subscription/verify-receipt",
        json={
            "platform": "ios",
            "product_id": "com.endlessrumination.pro.monthly",
            "purchase_token": "some-token",
            "is_subscription": True,
        },
    )
    # Should fail without auth (either 401 or 403 depending on auth impl)
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_verify_receipt_invalid_platform(client: AsyncClient):
    """Test invalid platform returns 422 (validation error)."""
    token = await _register_and_get_token(client, "bad-platform-device")

    resp = await client.post(
        "/api/v1/subscription/verify-receipt",
        json={
            "platform": "windows",
            "product_id": "com.endlessrumination.pro.monthly",
            "purchase_token": "some-token",
            "is_subscription": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    # Pydantic pattern validation should catch this
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_verify_receipt_unconfigured_validator(client: AsyncClient):
    """Test 503 when validator is not configured."""
    token = await _register_and_get_token(client, "no-config-device")

    with patch(
        "app.routers.subscription._get_apple_validator", return_value=None
    ):
        resp = await client.post(
            "/api/v1/subscription/verify-receipt",
            json={
                "platform": "ios",
                "product_id": "com.endlessrumination.pro.monthly",
                "purchase_token": "some-token",
                "is_subscription": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_subscription_status(client: AsyncClient, mock_redis):
    """Test subscription status endpoint returns expected structure."""
    token = await _register_and_get_token(client, "status-device")

    resp = await client.get(
        "/api/v1/subscription/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "free"
    assert "daily_takes_used" in data
    assert "daily_takes_limit" in data

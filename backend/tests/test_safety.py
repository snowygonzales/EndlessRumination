from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_safety_check_safe(client: AsyncClient, mock_anthropic):
    mock_anthropic.messages.create.return_value.content = [
        AsyncMock(text="SAFE")
    ]

    response = await client.post(
        "/api/v1/safety-check",
        json={"problem": "I'm worried about my job interview tomorrow"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["safe"] is True


@pytest.mark.asyncio
async def test_safety_check_unsafe(client: AsyncClient, mock_anthropic):
    mock_anthropic.messages.create.return_value.content = [
        AsyncMock(text="UNSAFE:self-harm")
    ]

    response = await client.post(
        "/api/v1/safety-check",
        json={"problem": "test unsafe content"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["safe"] is False
    assert data["category"] == "self-harm"
    assert len(data["resources"]) > 0
    assert data["resources"][0]["name"] == "988 Suicide & Crisis Lifeline"


@pytest.mark.asyncio
async def test_safety_check_empty_problem(client: AsyncClient):
    response = await client.post(
        "/api/v1/safety-check",
        json={"problem": ""},
    )
    assert response.status_code == 422  # Validation error

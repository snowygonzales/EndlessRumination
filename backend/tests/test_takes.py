from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_single_take(client: AsyncClient, mock_anthropic, mock_redis):
    response = await client.post(
        "/api/v1/generate-take",
        json={
            "problem": "I bombed my job interview and sent an angry email",
            "lens_index": 0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lens_index"] == 0
    assert "headline" in data
    assert "body" in data


@pytest.mark.asyncio
async def test_generate_take_invalid_lens(client: AsyncClient):
    response = await client.post(
        "/api/v1/generate-take",
        json={
            "problem": "test problem text here",
            "lens_index": 25,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_batch_returns_sse(client: AsyncClient, mock_anthropic, mock_redis):
    response = await client.post(
        "/api/v1/generate-batch",
        json={
            "problem": "I bombed my job interview and sent an angry email",
            "lens_indices": [0, 1],
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


@pytest.mark.asyncio
async def test_history_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/takes/history")
    assert response.status_code == 401

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Endless Rumination" in data["app"]


@pytest.mark.asyncio
async def test_lenses_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/lenses")
    assert response.status_code == 200
    lenses = response.json()
    assert len(lenses) == 20
    assert lenses[0]["name"] == "The Comedian"
    assert lenses[0]["emoji"] == "\U0001f602"
    assert lenses[19]["name"] == "Your Dog"
    # System prompts should NOT be exposed
    assert "system_prompt" not in lenses[0]

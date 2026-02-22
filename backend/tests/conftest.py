import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, get_db


# Use SQLite for tests (in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_anthropic():
    """Mock the Anthropic client for tests that don't need real API calls."""
    mock_response = AsyncMock()
    mock_response.content = [AsyncMock(text="Test headline\n\nTest body text here.")]

    with patch("app.services.claude_service._get_client") as mock_client, \
         patch("app.services.safety_service._get_client") as mock_safety_client:
        client_instance = AsyncMock()
        client_instance.messages.create = AsyncMock(return_value=mock_response)
        mock_client.return_value = client_instance
        mock_safety_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_redis():
    """Mock Redis for rate limiting tests."""
    with patch("app.services.rate_limiter.get_redis") as mock:
        redis_instance = AsyncMock()
        redis_instance.get = AsyncMock(return_value=None)
        redis_instance.incr = AsyncMock(return_value=1)
        redis_instance.expire = AsyncMock()
        mock.return_value = redis_instance
        yield redis_instance

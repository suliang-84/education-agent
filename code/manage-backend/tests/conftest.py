import fakeredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.core.redis as redis_module
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def fake_redis():
    """Replace real Redis with fakeredis for all tests."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    redis_module._redis = fake
    yield fake
    await fake.aclose()


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

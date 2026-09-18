from redis.asyncio import Redis, from_url

from app.core.config import get_settings

settings = get_settings()

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        if settings.APP_ENV == "development":
            from fakeredis import aioredis as fake_aioredis
            _redis = fake_aioredis.FakeRedis(decode_responses=True)
        else:
            _redis = from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None

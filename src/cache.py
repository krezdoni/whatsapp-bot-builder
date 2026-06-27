"""
Redis client for ephemeral state — OAuth PKCE state tokens, rate limiting.
Falls back to an in-memory dict if Redis is not configured (dev convenience only).
"""
import os
from typing import Optional

_USE_REDIS = bool(os.environ.get("REDIS_URL"))

if _USE_REDIS:
    import redis.asyncio as aioredis
    _pool: Optional[aioredis.Redis] = None

    async def get_redis() -> aioredis.Redis:
        global _pool
        if _pool is None:
            _pool = aioredis.from_url(
                os.environ["REDIS_URL"],
                encoding="utf-8",
                decode_responses=True,
            )
        return _pool

    async def cache_set(key: str, value: str, ttl_seconds: int = 600) -> None:
        r = await get_redis()
        await r.setex(key, ttl_seconds, value)

    async def cache_get(key: str) -> str | None:
        r = await get_redis()
        return await r.get(key)

    async def cache_delete(key: str) -> None:
        r = await get_redis()
        await r.delete(key)

else:
    # Dev fallback — in-memory, single-process only
    _store: dict[str, str] = {}

    async def cache_set(key: str, value: str, ttl_seconds: int = 600) -> None:
        _store[key] = value

    async def cache_get(key: str) -> str | None:
        return _store.get(key)

    async def cache_delete(key: str) -> None:
        _store.pop(key, None)

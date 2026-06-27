"""Test in-memory cache fallback (used when REDIS_URL is not set)."""
import os
# Ensure REDIS_URL is not set so we use in-memory fallback
os.environ.pop("REDIS_URL", None)
os.environ["FIELD_ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://x:x@localhost/x"

import pytest
from src.cache import cache_set, cache_get, cache_delete


@pytest.mark.asyncio
async def test_set_and_get():
    await cache_set("test:key1", "hello")
    assert await cache_get("test:key1") == "hello"


@pytest.mark.asyncio
async def test_get_missing_returns_none():
    assert await cache_get("test:nonexistent-key-xyz") is None


@pytest.mark.asyncio
async def test_delete():
    await cache_set("test:del_key", "value")
    await cache_delete("test:del_key")
    assert await cache_get("test:del_key") is None


@pytest.mark.asyncio
async def test_overwrite():
    await cache_set("test:over", "first")
    await cache_set("test:over", "second")
    assert await cache_get("test:over") == "second"


@pytest.mark.asyncio
async def test_oauth_state_pattern():
    state = "abc123xyz"
    user_id = "user-uuid-here"
    await cache_set(f"oauth:state:{state}", user_id, ttl_seconds=600)
    retrieved = await cache_get(f"oauth:state:{state}")
    assert retrieved == user_id
    await cache_delete(f"oauth:state:{state}")
    assert await cache_get(f"oauth:state:{state}") is None

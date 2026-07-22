"""
====================================================
Redis Cache Service
====================================================
Async Redis wrapper for caching ML artifacts
and API responses.
====================================================
"""
from __future__ import annotations

import json
from typing import Any, Optional

import orjson
from loguru import logger
from redis import asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings


# ====================================================
# Global Redis Pool
# =====================================================
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[aioredis.Redis] = None


async def init_cache() -> None:
    """Initialize Redis connection pool.

    Tolerant in dev: if Redis is unreachable, the cache is left
    uninitialized and individual cache operations become no-ops.
    Production should require Redis (raises on failure).
    """
    global _redis_pool, _redis_client

    _redis_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        password=settings.REDIS_PASSWORD or None,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=False,
        socket_connect_timeout=0.5,
        socket_timeout=0.5,
    )
    _redis_client = aioredis.Redis(connection_pool=_redis_pool)
    try:
        await _redis_client.ping()
        logger.info("✅ Redis cache initialized")
    except Exception as e:
        logger.warning(
            f"⚠️  Redis unreachable ({e}); cache disabled for this run"
        )
        # Leave _redis_client in place; every cache op is wrapped in
        # try/except and degrades to a no-op when Redis is down.
        if settings.IS_PRODUCTION:
            raise


async def close_cache() -> None:
    """Close Redis connection pool."""
    global _redis_client, _redis_pool
    if _redis_client:
        await _redis_client.aclose()
    if _redis_pool:
        await _redis_pool.aclose()
    logger.info("✅ Redis cache closed")


def get_redis() -> aioredis.Redis:
    """Get the Redis client (lazy initialization).

    Uses short socket timeouts so requests don't hang when Redis is down.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD or None,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=False,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
    return _redis_client


# ====================================================
# Cache Operations
# =====================================================
class CacheService:
    """High-level cache service."""

    def __init__(self, prefix: str = "crime_intel"):
        self.prefix = prefix
        self.client = get_redis()

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.client.get(self._key(key))
            if value is None:
                return None
            return orjson.loads(value)
        except Exception as e:
            logger.warning(f"Cache GET failed for {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache with TTL."""
        try:
            ttl = ttl or settings.CACHE_TTL_SECONDS
            payload = orjson.dumps(value)
            await self.client.set(self._key(key), payload, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache SET failed for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            await self.client.delete(self._key(key))
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE failed for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        try:
            full_pattern = self._key(pattern)
            count = 0
            async for key in self.client.scan_iter(match=full_pattern):
                await self.client.delete(key)
                count += 1
            return count
        except Exception as e:
            logger.warning(f"Cache DELETE PATTERN failed for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return bool(await self.client.exists(self._key(key)))
        except Exception:
            return False

    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache, or call factory and set."""
        value = await self.get(key)
        if value is not None:
            return value
        value = await factory() if callable(factory) else factory
        if value is not None:
            await self.set(key, value, ttl)
        return value

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        try:
            return int(await self.client.incrby(self._key(key), amount))
        except Exception as e:
            logger.warning(f"Cache INCR failed for {key}: {e}")
            return 0

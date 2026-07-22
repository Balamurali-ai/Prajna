"""
====================================================
Redis Cache Service
====================================================
Async Redis wrapper for caching ML artifacts
and API responses.
====================================================
"""
from __future__ import annotations

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
_cache_enabled = False


async def init_cache(required: bool = False) -> None:
    """Initialize Redis connection pool.

    Redis is optional. If REDIS_URL is not configured, or Redis is
    unreachable, caching is disabled and the application continues.
    Set required=True only for deployments that must have Redis.
    """
    global _redis_pool, _redis_client, _cache_enabled

    _redis_pool = None
    _redis_client = None
    _cache_enabled = False

    if not settings.REDIS_URL:
        logger.warning("Redis URL not configured; cache disabled")
        return

    try:
        _redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD or None,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=False,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        _redis_client = aioredis.Redis(connection_pool=_redis_pool)
        await _redis_client.ping()
        _cache_enabled = True
        logger.info("Redis cache initialized")
    except Exception as exc:
        logger.warning(f"Redis unavailable ({exc}); cache disabled")
        await close_cache()
        if required:
            raise


async def close_cache() -> None:
    """Close Redis connection pool."""
    global _redis_client, _redis_pool, _cache_enabled

    if _redis_client:
        await _redis_client.aclose()
    if _redis_pool:
        await _redis_pool.aclose()

    _redis_client = None
    _redis_pool = None
    _cache_enabled = False
    logger.info("Redis cache closed")


def get_redis() -> Optional[aioredis.Redis]:
    """Get the Redis client when cache is enabled."""
    if not _cache_enabled:
        return None
    return _redis_client


# ====================================================
# Cache Operations
# =====================================================
class CacheService:
    """High-level cache service."""

    def __init__(self, prefix: str = "crime_intel"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = get_redis()
        if client is None:
            return None

        try:
            value = await client.get(self._key(key))
            if value is None:
                return None
            return orjson.loads(value)
        except Exception as exc:
            logger.warning(f"Cache GET failed for {key}: {exc}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache with TTL."""
        client = get_redis()
        if client is None:
            return False

        try:
            ttl = ttl or settings.CACHE_TTL_SECONDS
            payload = orjson.dumps(value)
            await client.set(self._key(key), payload, ex=ttl)
            return True
        except Exception as exc:
            logger.warning(f"Cache SET failed for {key}: {exc}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        client = get_redis()
        if client is None:
            return False

        try:
            await client.delete(self._key(key))
            return True
        except Exception as exc:
            logger.warning(f"Cache DELETE failed for {key}: {exc}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        client = get_redis()
        if client is None:
            return 0

        try:
            full_pattern = self._key(pattern)
            count = 0
            async for key in client.scan_iter(match=full_pattern):
                await client.delete(key)
                count += 1
            return count
        except Exception as exc:
            logger.warning(f"Cache DELETE PATTERN failed for {pattern}: {exc}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        client = get_redis()
        if client is None:
            return False

        try:
            return bool(await client.exists(self._key(key)))
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
        client = get_redis()
        if client is None:
            return 0

        try:
            return int(await client.incrby(self._key(key), amount))
        except Exception as exc:
            logger.warning(f"Cache INCR failed for {key}: {exc}")
            return 0

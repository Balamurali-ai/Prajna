"""
====================================================
Dashboard Cache Repository
====================================================
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.dashboard_cache import CacheType, DashboardCache


class DashboardCacheRepository:
    """Repository for DashboardCache operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, cache_key: str) -> Optional[DashboardCache]:
        result = await self.session.execute(
            select(DashboardCache).where(DashboardCache.cache_key == cache_key)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        cache_key: str,
        cache_type: CacheType,
        payload: dict,
        ttl_seconds: int = 300,
        source: Optional[str] = None,
    ) -> DashboardCache:
        existing = await self.get(cache_key)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)

        if existing:
            existing.payload = payload
            existing.payload_size = len(str(payload))
            existing.expires_at = expires
            existing.last_refreshed_at = now
            existing.ttl_seconds = ttl_seconds
            if source:
                existing.source = source
            existing.hit_count = (existing.hit_count or 0) + 1
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        new_entry = DashboardCache(
            cache_key=cache_key,
            cache_type=cache_type,
            payload=payload,
            expires_at=expires,
            last_refreshed_at=now,
            ttl_seconds=ttl_seconds,
            source=source,
        )
        self.session.add(new_entry)
        await self.session.commit()
        await self.session.refresh(new_entry)
        return new_entry

    async def delete(self, cache_key: str) -> None:
        entry = await self.get(cache_key)
        if entry:
            await self.session.delete(entry)
            await self.session.commit()

    async def list_by_type(self, cache_type: CacheType) -> List[DashboardCache]:
        result = await self.session.execute(
            select(DashboardCache).where(DashboardCache.cache_type == cache_type)
        )
        return list(result.scalars().all())

    async def clean_expired(self) -> int:
        """Delete all expired cache entries. Returns count deleted."""
        from sqlalchemy import delete
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            delete(DashboardCache).where(DashboardCache.expires_at < now)
        )
        await self.session.commit()
        return result.rowcount

"""
====================================================
Analytics Service
====================================================
"""
from __future__ import annotations

from typing import Optional

from app.schemas.analytics import (
    AnalyticsReport,
    CategoryDistribution,
    NeighborInfluence,
    Seasonality,
    TrendsData,
)
from app.services.cache import CacheService
from ml.ml_loader import MLArtifactLoader


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(
        self,
        ml_loader: MLArtifactLoader,
        cache: Optional[CacheService] = None,
    ) -> None:
        self.ml_loader = ml_loader
        self.cache = cache or CacheService()

    async def get_full_report(self) -> AnalyticsReport:
        """Get the full analytics report."""
        cache_key = "analytics:full"
        cached = await self.cache.get(cache_key)
        if cached:
            return AnalyticsReport(**cached)

        raw = self.ml_loader.get_analytics_report()
        report = AnalyticsReport(
            trends=TrendsData(**raw.get("trends", {})) if raw.get("trends") else None,
            seasonality=Seasonality(**raw.get("seasonality", {})) if raw.get("seasonality") else None,
            category_distribution=(
                CategoryDistribution(**raw["category_distribution"])
                if raw.get("category_distribution") else None
            ),
            neighbor_influence=(
                NeighborInfluence(**raw["neighbor_influence"])
                if raw.get("neighbor_influence") else None
            ),
            generated_at=raw.get("generated_at"),
        )
        await self.cache.set(cache_key, report.model_dump(), ttl=600)
        return report

    async def get_trends(self) -> dict:
        cache_key = "analytics:trends"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        data = self.ml_loader.get_trends()
        await self.cache.set(cache_key, data, ttl=600)
        return data

    async def get_seasonality(self) -> dict:
        cache_key = "analytics:seasonality"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        data = self.ml_loader.get_seasonality()
        await self.cache.set(cache_key, data, ttl=600)
        return data

    async def get_categories(self) -> dict:
        cache_key = "analytics:categories"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        data = self.ml_loader.get_category_distribution()
        await self.cache.set(cache_key, data, ttl=600)
        return data

    async def get_neighbor_influence(self) -> dict:
        cache_key = "analytics:neighbor"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        data = self.ml_loader.get_neighbor_influence()
        await self.cache.set(cache_key, data, ttl=600)
        return data

"""
====================================================
Hotspot Service
====================================================
"""
from __future__ import annotations

from typing import List, Optional

from app.schemas.hotspot import HotspotGeoJSON, HotspotRanking
from app.services.cache import CacheService
from ml.ml_loader import MLArtifactLoader


class HotspotService:
    """Service for hotspot operations."""

    def __init__(
        self,
        ml_loader: MLArtifactLoader,
        cache: Optional[CacheService] = None,
    ) -> None:
        self.ml_loader = ml_loader
        self.cache = cache or CacheService()

    async def get_all(self) -> List[HotspotRanking]:
        """Get all hotspot rankings."""
        cache_key = "hotspots:all"
        cached = await self.cache.get(cache_key)
        if cached:
            return [HotspotRanking(**h) for h in cached]

        df = self.ml_loader.get_hotspot_rankings()
        result = [
            HotspotRanking(
                h3_cell=str(row["h3_cell"]),
                hotspot_score=float(row["hotspot_score"]),
                rank=int(row["rank"]),
            )
            for _, row in df.iterrows()
        ]
        await self.cache.set(cache_key, [r.model_dump() for r in result], ttl=300)
        return result

    async def get_top(self, n: Optional[int] = None) -> List[HotspotRanking]:
        """Get top N hotspots."""
        all_h = await self.get_all()
        return all_h[: (n or 20)]

    async def get_geojson(self) -> HotspotGeoJSON:
        """Get hotspots as GeoJSON FeatureCollection."""
        cache_key = "hotspots:geojson"
        cached = await self.cache.get(cache_key)
        if cached:
            return HotspotGeoJSON(**cached)
        geojson = self.ml_loader.get_hotspots_geojson()
        await self.cache.set(cache_key, geojson, ttl=300)
        return HotspotGeoJSON(**geojson)

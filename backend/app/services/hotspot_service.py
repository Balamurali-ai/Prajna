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

# [lng, lat] centroids for Indian states/UTs
_INDIA_CENTROIDS: dict[str, list[float]] = {
    "Andhra Pradesh": [79.74, 15.91], "Arunachal Pradesh": [94.73, 28.21],
    "Assam": [92.93, 26.20], "Bihar": [85.31, 25.09],
    "Chhattisgarh": [81.87, 21.27], "Goa": [74.12, 15.29],
    "Gujarat": [71.19, 22.25], "Haryana": [76.08, 29.05],
    "Himachal Pradesh": [77.17, 31.10], "Jharkhand": [85.27, 23.61],
    "Karnataka": [75.71, 15.31], "Kerala": [76.27, 10.85],
    "Madhya Pradesh": [78.65, 22.97], "Maharashtra": [75.71, 19.75],
    "Manipur": [93.90, 24.66], "Meghalaya": [91.36, 25.46],
    "Mizoram": [92.93, 23.16], "Nagaland": [94.56, 26.15],
    "Odisha": [85.09, 20.94], "Punjab": [75.34, 31.14],
    "Rajasthan": [74.21, 27.02], "Sikkim": [88.51, 27.53],
    "Tamil Nadu": [78.65, 11.12], "Telangana": [79.01, 17.36],
    "Tripura": [91.98, 23.94], "Uttar Pradesh": [80.94, 26.84],
    "Uttarakhand": [79.01, 30.06], "West Bengal": [87.85, 22.98],
    "Andaman and Nicobar Islands": [92.73, 11.74],
    "Chandigarh": [76.77, 30.73],
    "Dadra and Nagar Haveli and Daman and Diu": [73.01, 20.19],
    "Delhi": [77.10, 28.70], "Central Delhi": [77.22, 28.65],
    "New Delhi": [77.20, 28.61], "North Delhi": [77.20, 28.73],
    "North East Delhi": [77.27, 28.69], "North West Delhi": [77.07, 28.73],
    "East Delhi": [77.31, 28.66], "South Delhi": [77.22, 28.52],
    "South West Delhi": [77.06, 28.58], "West Delhi": [77.08, 28.65],
    "Shahdara": [77.29, 28.67], "South East Delhi": [77.29, 28.56],
    "Jammu and Kashmir": [74.79, 33.72], "Ladakh": [77.57, 34.15],
    "Lakshadweep": [72.63, 10.56], "Puducherry": [79.83, 11.93],
}

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
        # Try hotspot_rankings.csv first
        try:
            df = self.ml_loader.get_hotspot_rankings()
            return [
                HotspotRanking(
                    h3_cell=str(row["h3_cell"]),
                    hotspot_score=float(row["hotspot_score"]),
                    rank=int(row["rank"]),
                )
                for _, row in df.iterrows()
            ]
        except Exception:
            pass

        # Fallback: derive from risk_rankings in analytics_report
        try:
            raw = self.ml_loader.get_analytics_report()
            rankings = raw.get("risk_rankings", [])
            return [
                HotspotRanking(
                    h3_cell=r["district"],
                    hotspot_score=float(r["score"]),
                    rank=int(r["rank"]),
                )
                for r in rankings
            ]
        except Exception:
            return []

    async def get_top(self, n: Optional[int] = None) -> List[HotspotRanking]:
        """Get top N hotspots."""
        all_h = await self.get_all()
        return all_h[: (n or 20)]

    async def get_geojson(self) -> HotspotGeoJSON:
        """Get hotspots as GeoJSON FeatureCollection."""
        # Try real geojson file first
        geojson = self.ml_loader.get_hotspots_geojson()
        if geojson.get("features"):
            return HotspotGeoJSON(**geojson)

        # Fallback: build point features from risk_rankings using state centroids
        try:
            raw = self.ml_loader.get_analytics_report()
            rankings = raw.get("risk_rankings", [])
            features = []
            for r in rankings:
                coords = _INDIA_CENTROIDS.get(r["district"])
                if coords:
                    features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": coords},
                        "properties": {
                            "h3_cell": r["district"],
                            "hotspot_score": r["score"],
                            "rank": r["rank"],
                        },
                    })
            return HotspotGeoJSON(type="FeatureCollection", features=features)
        except Exception:
            return HotspotGeoJSON(type="FeatureCollection", features=[])

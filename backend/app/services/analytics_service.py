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


def _build_trends(raw: dict) -> Optional[TrendsData]:
    """Map actual JSON structure to TrendsData."""
    monthly_raw = raw.get("monthly_trends", {})
    crime_trends = raw.get("crime_trends", {})

    # Build monthly list from monthly_trends {"1": 4767, ...}
    monthly = [
        {"month": int(k), "value": v}
        for k, v in sorted(monthly_raw.items(), key=lambda x: int(x[0]))
    ] if monthly_raw else []

    # Overall direction from crime_trends majority
    directions = [v.get("direction", "") for v in crime_trends.values()]
    increasing = directions.count("increasing")
    decreasing = directions.count("decreasing")
    direction = "up" if increasing > decreasing else ("down" if decreasing > increasing else "stable")

    # Average change pct
    changes = [v.get("change_pct", 0) for v in crime_trends.values() if v.get("change_pct") is not None]
    avg_change = sum(changes) / len(changes) if changes else None

    return TrendsData(direction=direction, percentage_change=avg_change, monthly=monthly)


def _build_seasonality(raw: dict) -> Optional[Seasonality]:
    """Map actual JSON structure to Seasonality."""
    season_raw = raw.get("seasonality", {})
    monthly_raw = raw.get("monthly_trends", {})

    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    }

    monthly_pattern = [
        {"month": month_names.get(int(k), k), "value": v}
        for k, v in sorted(monthly_raw.items(), key=lambda x: int(x[0]))
    ] if monthly_raw else []

    # Peak month from monthly_trends
    peak_month = None
    if monthly_raw:
        peak_k = max(monthly_raw, key=lambda k: monthly_raw[k])
        peak_month = month_names.get(int(peak_k), peak_k)

    return Seasonality(monthly_pattern=monthly_pattern, peak_month=peak_month)


def _build_categories(raw: dict) -> Optional[CategoryDistribution]:
    """Map actual JSON structure to CategoryDistribution."""
    cat_raw = raw.get("crime_category_distribution", {})
    if not cat_raw:
        return CategoryDistribution(categories=[])

    categories = [
        {"name": name, "count": v.get("count", 0), "percentage": v.get("pct", 0)}
        for name, v in cat_raw.items()
    ]
    total = sum(c["count"] for c in categories)
    return CategoryDistribution(categories=categories, total_crimes=total)


def _build_neighbor(raw: dict) -> Optional[NeighborInfluence]:
    """Map actual JSON structure to NeighborInfluence."""
    ni_raw = raw.get("neighbor_influence", {})
    if not ni_raw:
        return NeighborInfluence()

    # Shape: {"Neighbor_District_Risk": {"correlation_with_crime": 0.3066, "mean": 5013}}
    corr = None
    for v in ni_raw.values():
        if isinstance(v, dict):
            corr = v.get("correlation_with_crime")
            break

    # Build clusters from risk_rankings
    rankings = raw.get("risk_rankings", [])
    clusters = [
        {"district": r["district"], "score": r["score"]}
        for r in rankings[:10]
    ]

    return NeighborInfluence(
        moran_i=corr,
        spatial_lag=corr,
        hotspots_clusters=clusters,
        summary=f"Neighbor correlation: {corr:.3f}" if corr else None,
    )


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
        raw = self.ml_loader.get_analytics_report()
        return AnalyticsReport(
            trends=_build_trends(raw),
            seasonality=_build_seasonality(raw),
            category_distribution=_build_categories(raw),
            neighbor_influence=_build_neighbor(raw),
            generated_at=raw.get("generated_at"),
        )

    async def get_trends(self) -> dict:
        raw = self.ml_loader.get_analytics_report()
        return _build_trends(raw).model_dump() if _build_trends(raw) else {}

    async def get_seasonality(self) -> dict:
        raw = self.ml_loader.get_analytics_report()
        s = _build_seasonality(raw)
        return s.model_dump() if s else {}

    async def get_categories(self) -> dict:
        raw = self.ml_loader.get_analytics_report()
        c = _build_categories(raw)
        return c.model_dump() if c else {}

    async def get_neighbor_influence(self) -> dict:
        raw = self.ml_loader.get_analytics_report()
        n = _build_neighbor(raw)
        return n.model_dump() if n else {}

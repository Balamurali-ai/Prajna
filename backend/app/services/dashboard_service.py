"""
====================================================
Dashboard Service
====================================================
Builds the full dashboard payload from ML artifacts.
====================================================
"""
from __future__ import annotations

import time
from typing import Optional

from fastapi import Request
from loguru import logger

from app.core.exceptions import MLArtifactException
from app.schemas.dashboard import DashboardMetrics, DashboardResponse
from app.schemas.hotspot import HotspotRanking
from app.schemas.risk import RiskRanking
from app.services.cache import CacheService
from ml.ml_loader import MLArtifactLoader


class DashboardService:
    """Service for building dashboard payloads."""

    def __init__(
        self,
        ml_loader: MLArtifactLoader,
        cache: Optional[CacheService] = None,
    ) -> None:
        self.ml_loader = ml_loader
        self.cache = cache or CacheService()

    async def get_full_dashboard(self) -> DashboardResponse:
        """Build the complete dashboard payload in one call."""
        cache_key = "dashboard:full"

        async def _build():
            try:
                metrics = self._build_metrics()
                top_districts = self._build_top_districts(n=10)
                top_hotspots = self._build_top_hotspots(n=10)
                alerts = self._build_alerts(top_districts, top_hotspots)
                return DashboardResponse(
                    metrics=metrics,
                    top_districts=top_districts,
                    top_hotspots=top_hotspots,
                    alerts=alerts,
                    generated_at=time.time(),
                ).model_dump()
            except Exception as e:
                logger.error(f"Failed to build dashboard: {e}")
                raise MLArtifactException(f"Dashboard build failed: {e}")

        cached = await self.cache.get_or_set(cache_key, _build, ttl=300)
        return DashboardResponse(**cached)

    def _build_metrics(self) -> DashboardMetrics:
        raw = self.ml_loader.get_dashboard_metrics()
        return DashboardMetrics(
            total_crimes=int(raw.get("total_crimes", 0)),
            hotspot_count=int(raw.get("hotspot_count", 0)),
            average_risk_score=float(raw.get("average_risk_score", 0.0)),
            high_risk_districts=int(raw.get("high_risk_districts", 0)),
            trend_direction=str(raw.get("trend_direction", "stable")),
        )

    def _build_top_districts(self, n: int = 10) -> list[RiskRanking]:
        try:
            df = self.ml_loader.get_top_n(n)
            results = []
            for _, row in df.iterrows():
                results.append(
                    RiskRanking(
                        district=str(row.get("district", "")),
                        state=row.get("state"),
                        risk_score=float(row.get("risk_score", 0)),
                        risk_rank=int(row.get("risk_rank", 0)),
                        confidence=float(row.get("confidence", 0)),
                        predicted_crime_count=(
                            int(row["predicted_crime_count"])
                            if "predicted_crime_count" in row and not _isnan(row["predicted_crime_count"])
                            else None
                        ),
                    )
                )
            if results:
                return results
        except Exception:
            pass
        # Fallback: analytics_report risk_rankings
        try:
            raw = self.ml_loader.get_analytics_report()
            rankings = raw.get("risk_rankings", [])[:n]
            return [
                RiskRanking(district=r["district"], risk_score=float(r["score"]), risk_rank=int(r["rank"]))
                for r in rankings
            ]
        except Exception:
            return []

    def _build_top_hotspots(self, n: int = 10) -> list[HotspotRanking]:
        try:
            df = self.ml_loader.get_top_hotspots(n)
            results = []
            for _, row in df.iterrows():
                results.append(
                    HotspotRanking(
                        h3_cell=str(row.get("h3_cell", "")),
                        hotspot_score=float(row.get("hotspot_score", 0)),
                        rank=int(row.get("rank", 0)),
                    )
                )
            if results:
                return results
        except Exception:
            pass
        # Fallback: top districts as hotspot proxies
        try:
            raw = self.ml_loader.get_analytics_report()
            rankings = raw.get("risk_rankings", [])[:n]
            return [
                HotspotRanking(h3_cell=r["district"], hotspot_score=float(r["score"]), rank=int(r["rank"]))
                for r in rankings
            ]
        except Exception:
            return []

    def _build_alerts(
        self,
        districts: list[RiskRanking],
        hotspots: list[HotspotRanking],
    ) -> list[dict]:
        alerts = []
        for d in districts[:3]:
            if d.risk_score >= 75:
                alerts.append({
                    "type": "high_risk_district",
                    "severity": "critical" if d.risk_score >= 85 else "high",
                    "title": f"High risk in {d.district}",
                    "description": f"Risk score {d.risk_score:.1f} (rank #{d.risk_rank})",
                    "district": d.district,
                    "score": d.risk_score,
                })
        for h in hotspots[:5]:
            if h.hotspot_score >= 80:
                alerts.append({
                    "type": "hotspot",
                    "severity": "high",
                    "title": f"Hotspot detected at {h.h3_cell}",
                    "description": f"Score {h.hotspot_score:.1f} (rank #{h.rank})",
                    "h3_cell": h.h3_cell,
                    "score": h.hotspot_score,
                })
        return alerts


def _isnan(v) -> bool:
    try:
        import math
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return False

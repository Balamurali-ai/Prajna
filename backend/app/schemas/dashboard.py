"""
====================================================
Dashboard Schemas
====================================================
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.hotspot import HotspotRanking
from app.schemas.risk import RiskRanking


class DashboardMetrics(BaseModel):
    """KPI cards for the dashboard."""
    total_crimes: int = Field(..., description="Total number of crimes")
    hotspot_count: int = Field(..., description="Number of active hotspots")
    average_risk_score: float = Field(..., description="Mean risk score")
    high_risk_districts: int = Field(..., description="Count of high-risk districts")
    trend_direction: str = Field(..., description="Overall trend (up/down/stable)")


class DashboardResponse(BaseModel):
    """Full dashboard payload — single round-trip for the SPA."""
    metrics: DashboardMetrics
    top_districts: List[RiskRanking]
    top_hotspots: List[HotspotRanking]
    alerts: Optional[List[dict]] = []
    generated_at: float

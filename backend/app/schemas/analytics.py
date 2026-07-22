"""
====================================================
Analytics Schemas
====================================================
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TrendsData(BaseModel):
    """Trend analysis output."""
    direction: str = Field(..., description="up | down | stable")
    percentage_change: Optional[float] = None
    monthly: List[Dict[str, Any]] = []
    yearly: List[Dict[str, Any]] = []
    summary: Optional[str] = None


class Seasonality(BaseModel):
    """Seasonality patterns."""
    monthly_pattern: List[Dict[str, Any]] = []
    weekly_pattern: List[Dict[str, Any]] = []
    quarterly_pattern: List[Dict[str, Any]] = []
    peak_month: Optional[str] = None
    peak_day_of_week: Optional[str] = None


class CategoryDistribution(BaseModel):
    """Crime category distribution."""
    categories: List[Dict[str, Any]] = []
    total_crimes: Optional[int] = None


class NeighborInfluence(BaseModel):
    """Spatial neighbor influence / spillover analysis."""
    spatial_lag: Optional[float] = None
    moran_i: Optional[float] = None
    hotspots_clusters: List[Dict[str, Any]] = []
    summary: Optional[str] = None


class AnalyticsReport(BaseModel):
    """Full analytics report payload."""
    trends: Optional[TrendsData] = None
    seasonality: Optional[Seasonality] = None
    category_distribution: Optional[CategoryDistribution] = None
    neighbor_influence: Optional[NeighborInfluence] = None
    generated_at: Optional[float] = None

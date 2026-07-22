"""
====================================================
Hotspot Schemas
====================================================
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HotspotRanking(BaseModel):
    """Single H3 hotspot cell ranking."""
    h3_cell: str = Field(..., description="H3 hexagonal cell ID")
    hotspot_score: float = Field(..., ge=0)
    rank: int = Field(..., ge=1)


class HotspotFeature(BaseModel):
    """GeoJSON Feature for a hotspot."""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class HotspotGeoJSON(BaseModel):
    """GeoJSON FeatureCollection of hotspots."""
    type: str = "FeatureCollection"
    features: List[HotspotFeature]

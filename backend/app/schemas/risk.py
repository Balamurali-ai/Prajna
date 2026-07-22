"""
====================================================
Risk Schemas
====================================================
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class RiskRanking(BaseModel):
    """District risk ranking row."""
    district: str
    state: Optional[str] = None
    risk_score: float = Field(..., ge=0, le=100)
    risk_rank: int = Field(..., ge=1)
    confidence: float = Field(..., ge=0, le=1)
    predicted_crime_count: Optional[int] = None


class DistrictPrediction(BaseModel):
    """Single district prediction detail."""
    district: str
    state: Optional[str] = None
    risk_score: float
    risk_rank: int
    confidence: float
    predicted_crime_count: Optional[int] = None
    additional_metrics: Optional[dict] = None


class TopDistricts(BaseModel):
    """Top N districts response."""
    top_n: int
    districts: List[RiskRanking]

"""
====================================================
Explainability Schemas
====================================================
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FeatureImportance(BaseModel):
    """Single feature importance entry."""
    feature: str
    importance: float
    rank: Optional[int] = None
    direction: Optional[str] = Field(None, description="positive | negative")


class GlobalExplanation(BaseModel):
    """Global SHAP explanation."""
    model_config = {"protected_namespaces": ()}

    features: List[FeatureImportance]
    base_value: Optional[float] = None
    model_type: Optional[str] = None
    summary: Optional[str] = None


class DistrictExplanation(BaseModel):
    """Per-district SHAP drivers."""
    district: str
    base_value: float
    predicted_value: float
    top_features: List[FeatureImportance]
    full_features: Optional[Dict[str, float]] = None

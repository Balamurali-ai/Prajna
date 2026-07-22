"""
====================================================
Explainability Service
====================================================
"""
from __future__ import annotations

from typing import List, Optional

from loguru import logger

from app.core.exceptions import NotFoundException
from app.schemas.explainability import (
    DistrictExplanation,
    FeatureImportance,
    GlobalExplanation,
)
from app.services.cache import CacheService
from ml.ml_loader import MLArtifactLoader


class ExplainabilityService:
    """Service for SHAP-based explainability."""

    def __init__(
        self,
        ml_loader: MLArtifactLoader,
        cache: Optional[CacheService] = None,
    ) -> None:
        self.ml_loader = ml_loader
        self.cache = cache or CacheService()

    async def get_global(self) -> GlobalExplanation:
        """Get global SHAP feature importance."""
        cache_key = "explain:global"
        cached = await self.cache.get(cache_key)
        if cached:
            return GlobalExplanation(**cached)

        df = self.ml_loader.get_feature_importance()

        # Identify importance column
        importance_col = None
        feature_col = "feature"
        for candidate in ["importance", "shap_value", "mean_abs_shap", "value"]:
            if candidate in df.columns:
                importance_col = candidate
                break

        if importance_col is None:
            logger.warning("Feature importance CSV has no recognized importance column")
            return GlobalExplanation(features=[])

        # Identify feature column
        for candidate in ["feature", "name", "variable", "column"]:
            if candidate in df.columns:
                feature_col = candidate
                break

        df_sorted = df.sort_values(importance_col, ascending=False).reset_index(drop=True)
        features = []
        for idx, row in df_sorted.iterrows():
            features.append(
                FeatureImportance(
                    feature=str(row[feature_col]),
                    importance=float(row[importance_col]),
                    rank=idx + 1,
                )
            )

        explanation = GlobalExplanation(
            features=features,
            summary=f"Top driver: {features[0].feature}" if features else None,
        )
        await self.cache.set(cache_key, explanation.model_dump(), ttl=600)
        return explanation

    async def get_district_explanation(self, district: str) -> DistrictExplanation:
        """Get SHAP explanation for a specific district."""
        cache_key = f"explain:district:{district.lower()}"
        cached = await self.cache.get(cache_key)
        if cached:
            return DistrictExplanation(**cached)

        # Get base risk score
        district_pred = self.ml_loader.get_district_prediction(district)
        if not district_pred:
            raise NotFoundException(f"District '{district}' not found")

        # Get per-district SHAP values
        shap_row = self.ml_loader.get_district_shap(district)

        # Get global features for fallback
        global_expl = await self.get_global()

        if shap_row:
            top_features = []
            feature_importance = []
            for key, value in shap_row.items():
                if key in ("district", "state", "base_value", "predicted_value"):
                    continue
                try:
                    val = float(value)
                    feature_importance.append(
                        FeatureImportance(
                            feature=key,
                            importance=abs(val),
                            direction="positive" if val > 0 else "negative",
                        )
                    )
                except (TypeError, ValueError):
                    continue
            feature_importance.sort(key=lambda f: f.importance, reverse=True)
            top_features = feature_importance[:10]

            explanation = DistrictExplanation(
                district=district,
                base_value=float(shap_row.get("base_value", 0)),
                predicted_value=float(district_pred.get("risk_score", 0)),
                top_features=top_features,
                full_features={
                    f.feature: f.importance for f in feature_importance
                },
            )
        else:
            # No per-district SHAP — use global ranking
            explanation = DistrictExplanation(
                district=district,
                base_value=0.0,
                predicted_value=float(district_pred.get("risk_score", 0)),
                top_features=global_expl.features[:10],
            )

        await self.cache.set(cache_key, explanation.model_dump(), ttl=300)
        return explanation

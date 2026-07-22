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
        # Try feature_importance.csv first
        try:
            df = self.ml_loader.get_feature_importance()
            importance_col = next(
                (c for c in ["importance", "shap_value", "mean_abs_shap", "value"] if c in df.columns),
                None,
            )
            feature_col = next(
                (c for c in ["feature", "name", "variable", "column"] if c in df.columns),
                None,
            )
            if importance_col and feature_col:
                df_sorted = df.sort_values(importance_col, ascending=False).reset_index(drop=True)
                features = [
                    FeatureImportance(
                        feature=str(row[feature_col]),
                        importance=float(row[importance_col]),
                        rank=idx + 1,
                    )
                    for idx, row in df_sorted.iterrows()
                ]
                return GlobalExplanation(
                    features=features,
                    summary=f"Top driver: {features[0].feature}" if features else None,
                )
        except Exception:
            pass

        # Fallback: derive from analytics_report risk_rankings
        try:
            raw = self.ml_loader.get_analytics_report()
            rankings = raw.get("risk_rankings", [])
            cat_raw = raw.get("crime_category_distribution", {})

            features: List[FeatureImportance] = []
            # Use crime categories as feature proxies
            for i, (name, v) in enumerate(cat_raw.items()):
                features.append(FeatureImportance(
                    feature=name,
                    importance=round(v.get("pct", 0) / 100, 4),
                    rank=i + 1,
                ))
            features.sort(key=lambda f: f.importance, reverse=True)
            for i, f in enumerate(features):
                f.rank = i + 1

            return GlobalExplanation(
                features=features,
                model_type="Ensemble",
                summary=f"Top driver: {features[0].feature}" if features else None,
            )
        except Exception as e:
            logger.warning(f"Could not build global explanation: {e}")
            return GlobalExplanation(features=[])

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

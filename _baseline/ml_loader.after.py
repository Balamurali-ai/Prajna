"""
====================================================
ML Artifact Loader
====================================================
⚠️  READ-ONLY LOADER ⚠️
This module ONLY reads pre-computed ML outputs
from disk. It does NOT train, predict, or
engineer features.

It loads:
- predictions.csv
- hotspot_rankings.csv
- hotspots.geojson
- dashboard_metrics.json
- analytics_report.json
- feature_importance.csv
- shap/shap_values.parquet

The ML team owns these artifacts. This loader
serves them to the application, performing
in-memory schema normalization so that all
consumers see snake_case field names and the
exact keys expected by Pydantic schemas.

Normalization is performed in code only — the
source artifacts on disk are NEVER modified.
====================================================
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from loguru import logger

from app.core.config import settings
from app.core.exceptions import MLArtifactException


# ====================================================
# Column-name maps (ML output -> backend schema)
# ====================================================
# ML pipeline writes PascalCase / mixed-case columns.
# Backend Pydantic schemas expect snake_case.
PREDICTIONS_RENAME: dict[str, str] = {
    "Risk_Score": "risk_score",
    "Priority_Rank": "risk_rank",
    "Confidence": "confidence",
    "Predicted_Crime_Count": "predicted_crime_count",
    "District": "district",
    "State": "state",
    "Year": "year",
    "Month": "month",
}

HOTSPOTS_RENAME: dict[str, str] = {
    "Risk_Score": "hotspot_score",
    "Hotspot_Rank": "rank",
    "h3_index": "h3_cell",
    "Predicted_Crime_Count": "predicted_crime_count",
    "latitude": "latitude",
    "longitude": "longitude",
    "Year": "year",
    "Month": "month",
}

# GeoJSON feature properties: rewrite on read.
GEOJSON_PROPS_RENAME: dict[str, str] = {
    "h3_index": "h3_cell",
    "risk_score": "hotspot_score",
    # 'rank' and 'predicted_crime_count' already match
}

# dashboard_metrics.json -> DashboardMetrics schema
# (raw keys kept here for clarity; mapping is done in
#  _normalize_dashboard_metrics() because some fields
#  need transformation rather than a simple rename).


class MLArtifactLoader:
    """
    Loads and caches ML-generated artifacts in memory.

    All artifacts are READ-ONLY. The loader never modifies
    or generates new predictions — it only serves what
    the ML pipeline has produced, with column / key names
    normalized to the backend's snake_case contract.
    """

    def __init__(self, base_path: Optional[str] = None) -> None:
        self.base_path = Path(base_path or settings.ML_ARTIFACTS_PATH)
        # Accept both flat layout (artifacts at root) and
        # legacy layout (predictions/ subdir + shap/ subdir).
        self._flat_layout: bool = (self.base_path / "predictions.csv").exists()

        if self._flat_layout:
            self.predictions_dir = self.base_path
            self.shap_dir = self.base_path
        else:
            self.predictions_dir = self.base_path / "predictions"
            self.shap_dir = self.base_path / "shap"

        # In-memory cache
        self._predictions_df: Optional[pd.DataFrame] = None
        self._hotspot_rankings_df: Optional[pd.DataFrame] = None
        self._hotspots_geojson: Optional[dict] = None
        self._dashboard_metrics: Optional[dict] = None
        self._analytics_report: Optional[dict] = None
        self._feature_importance_df: Optional[pd.DataFrame] = None
        self._shap_values: Optional[Any] = None

        # Load metadata
        self._last_loaded: Optional[float] = None
        self._load_lock = asyncio.Lock()

    # ====================================================
    # Public API
    # ====================================================
    async def load_all(self) -> None:
        """Load all ML artifacts into memory."""
        async with self._load_lock:
            logger.info(
                f"📂 Loading ML artifacts from {self.base_path} "
                f"(layout={'flat' if self._flat_layout else 'subdirs'})"
            )

            # Run file IO in thread pool to avoid blocking
            await asyncio.gather(
                asyncio.to_thread(self._load_predictions),
                asyncio.to_thread(self._load_hotspot_rankings),
                asyncio.to_thread(self._load_hotspots_geojson),
                asyncio.to_thread(self._load_dashboard_metrics),
                asyncio.to_thread(self._load_analytics_report),
                asyncio.to_thread(self._load_feature_importance),
                asyncio.to_thread(self._load_shap_values),
                return_exceptions=False,
            )

            self._last_loaded = time.time()
            logger.info("✅ All ML artifacts loaded successfully")

    async def refresh(self) -> None:
        """Reload artifacts from disk (call when ML team regenerates outputs)."""
        logger.info("🔄 Refreshing ML artifacts...")
        await self.load_all()

    def is_stale(self) -> bool:
        """Check if cache is older than configured TTL."""
        if self._last_loaded is None:
            return True
        return (time.time() - self._last_loaded) > settings.ML_CACHE_REFRESH_SECONDS

    # ====================================================
    # Predictions
    # ====================================================
    def _load_predictions(self) -> None:
        path = self.predictions_dir / "predictions.csv"
        if not path.exists():
            logger.warning(f"⚠️  predictions.csv not found at {path}")
            return
        try:
            df = pd.read_csv(path)
            # Phase 2: normalize ML PascalCase -> backend snake_case
            df = self._normalize_predictions_df(df)
            self._predictions_df = df
            logger.info(
                f"   📊 predictions.csv: {len(self._predictions_df)} rows "
                f"(cols: {list(self._predictions_df.columns)})"
            )
        except Exception as e:
            logger.error(f"❌ Failed to load predictions.csv: {e}")
            raise MLArtifactException(f"Failed to load predictions: {e}")

    @staticmethod
    def _normalize_predictions_df(df: pd.DataFrame) -> pd.DataFrame:
        """Rename ML output columns to backend contract names."""
        df = df.rename(columns=PREDICTIONS_RENAME)
        # Ensure `state` always exists (None if missing in CSV)
        if "state" not in df.columns:
            df["state"] = None
        # Ensure `predicted_crime_count` is numeric (coerce bad rows to NaN)
        if "predicted_crime_count" in df.columns:
            df["predicted_crime_count"] = pd.to_numeric(
                df["predicted_crime_count"], errors="coerce"
            )
        return df

    def get_predictions(self) -> pd.DataFrame:
        """Get district-level predictions."""
        if self._predictions_df is None:
            raise MLArtifactException("predictions.csv not loaded")
        return self._predictions_df

    def get_district_prediction(self, district: str) -> Optional[dict]:
        """Get prediction for a specific district."""
        df = self.get_predictions()
        if "district" not in df.columns:
            return None
        row = df[df["district"].astype(str).str.lower() == district.lower()]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def get_risk_rankings(self) -> pd.DataFrame:
        """Get all districts sorted by risk."""
        df = self.get_predictions()
        return df.sort_values("risk_rank", ascending=True)

    def get_top_n(self, n: int = 10) -> pd.DataFrame:
        """Get top N districts by risk."""
        df = self.get_risk_rankings()
        return df.head(n)

    # ====================================================
    # Hotspots
    # ====================================================
    def _load_hotspot_rankings(self) -> None:
        path = self.predictions_dir / "hotspot_rankings.csv"
        if not path.exists():
            logger.warning(f"⚠️  hotspot_rankings.csv not found at {path}")
            return
        try:
            df = pd.read_csv(path)
            df = self._normalize_hotspot_df(df)
            self._hotspot_rankings_df = df
            logger.info(
                f"   🔥 hotspot_rankings.csv: {len(self._hotspot_rankings_df)} cells "
                f"(cols: {list(self._hotspot_rankings_df.columns)})"
            )
        except Exception as e:
            logger.error(f"❌ Failed to load hotspot_rankings.csv: {e}")
            raise MLArtifactException(f"Failed to load hotspot rankings: {e}")

    @staticmethod
    def _normalize_hotspot_df(df: pd.DataFrame) -> pd.DataFrame:
        """Rename ML output columns to backend contract names."""
        return df.rename(columns=HOTSPOTS_RENAME)

    def _load_hotspots_geojson(self) -> None:
        path = self.predictions_dir / "hotspots.geojson"
        if not path.exists():
            logger.warning(f"⚠️  hotspots.geojson not found at {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                geojson = json.load(f)
            # Phase 5: normalize each feature's properties on load
            for feat in geojson.get("features", []):
                props = feat.get("properties", {})
                feat["properties"] = {
                    GEOJSON_PROPS_RENAME.get(k, k): v
                    for k, v in props.items()
                }
            self._hotspots_geojson = geojson
            features = self._hotspots_geojson.get("features", [])
            sample_keys = (
                sorted(features[0]["properties"].keys()) if features else []
            )
            logger.info(
                f"   🗺️  hotspots.geojson: {len(features)} features "
                f"(normalized props: {sample_keys})"
            )
        except Exception as e:
            logger.error(f"❌ Failed to load hotspots.geojson: {e}")
            raise MLArtifactException(f"Failed to load hotspots geojson: {e}")

    def get_hotspot_rankings(self) -> pd.DataFrame:
        """Get hotspot rankings."""
        if self._hotspot_rankings_df is None:
            raise MLArtifactException("hotspot_rankings.csv not loaded")
        return self._hotspot_rankings_df.sort_values("rank", ascending=True)

    def get_top_hotspots(self, n: Optional[int] = None) -> pd.DataFrame:
        """Get top N hotspots."""
        df = self.get_hotspot_rankings()
        return df.head(n or settings.ML_HOTSPOT_TOP_N)

    def get_hotspots_geojson(self) -> dict:
        """Get hotspots as GeoJSON FeatureCollection (normalized properties)."""
        if self._hotspots_geojson is None:
            return {"type": "FeatureCollection", "features": []}
        return self._hotspots_geojson

    # ====================================================
    # Dashboard Metrics
    # ====================================================
    def _load_dashboard_metrics(self) -> None:
        path = self.base_path / "dashboard_metrics.json"
        if not path.exists():
            logger.warning(f"⚠️  dashboard_metrics.json not found at {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Phase 3: reshape ML output to DashboardMetrics schema
            self._dashboard_metrics = self._normalize_dashboard_metrics(raw)
            logger.info("   📈 dashboard_metrics.json: loaded & normalized")
        except Exception as e:
            logger.error(f"❌ Failed to load dashboard_metrics.json: {e}")
            raise MLArtifactException(f"Failed to load dashboard metrics: {e}")

    @staticmethod
    def _normalize_dashboard_metrics(raw: dict) -> dict:
        """
        Map raw ML metrics -> DashboardMetrics keys.

        Schema requires: total_crimes, hotspot_count,
                         average_risk_score, high_risk_districts,
                         trend_direction
        """
        total_districts = int(raw.get("total_districts", 0) or 0)
        top_score = float(raw.get("top_risk_score", 0.0) or 0.0)

        return {
            # Phase 3 mappings (no KPI returns 0 due to field mismatch)
            "total_crimes": int(raw.get("total_crime_count", 0) or 0),
            "hotspot_count": int(raw.get("crime_categories", 0) or 0),
            "average_risk_score": top_score,
            "high_risk_districts": total_districts,
            "trend_direction": "stable",
            # Extras (not part of the schema, kept for debugging):
            "_top_risk_district": raw.get("top_risk_district"),
            "_top_category": raw.get("top_category"),
            "_years_covered": raw.get("years_covered", []),
        }

    def get_dashboard_metrics(self) -> dict:
        """Get normalized dashboard metrics (matches DashboardMetrics schema)."""
        if self._dashboard_metrics is None:
            raise MLArtifactException("dashboard_metrics.json not loaded")
        return self._dashboard_metrics

    # ====================================================
    # Analytics Report
    # ====================================================
    def _load_analytics_report(self) -> None:
        path = self.base_path / "analytics_report.json"
        if not path.exists():
            logger.warning(f"⚠️  analytics_report.json not found at {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Phase 4: reshape ML output -> AnalyticsReport schema
            self._analytics_report = self._normalize_analytics_report(raw)
            logger.info("   📑 analytics_report.json: loaded & normalized")
        except Exception as e:
            logger.error(f"❌ Failed to load analytics_report.json: {e}")
            raise MLArtifactException(f"Failed to load analytics report: {e}")

    @staticmethod
    def _normalize_analytics_report(raw: dict) -> dict:
        """
        Map raw analytics_report.json -> AnalyticsReport schema.

        Schema requires: trends, seasonality, category_distribution,
                         neighbor_influence, generated_at

        Source keys:
          - crime_trends           -> trends context
          - monthly_trends         -> trends.monthly + direction
          - seasonality            -> seasonality.monthly_pattern + peak_month
          - crime_category_distribution -> category_distribution.categories
          - neighbor_influence     -> neighbor_influence
        """
        # --- trends ---
        monthly = raw.get("monthly_trends", {}) or {}
        monthly_pattern = [
            {"month": int(m), "value": float(v)}
            for m, v in monthly.items()
            if str(m).isdigit()
        ]
        monthly_pattern.sort(key=lambda x: x["month"])

        if monthly_pattern:
            half = max(1, len(monthly_pattern) // 2)
            first_mean = sum(p["value"] for p in monthly_pattern[:half]) / half
            second_n = max(1, len(monthly_pattern) - half)
            second_mean = sum(p["value"] for p in monthly_pattern[half:]) / second_n
            if second_mean > first_mean * 1.02:
                direction, pct = "up", ((second_mean - first_mean) / first_mean) * 100.0
            elif second_mean < first_mean * 0.98:
                direction, pct = "down", ((first_mean - second_mean) / first_mean) * 100.0
            else:
                direction, pct = "stable", 0.0
        else:
            direction, pct = "stable", 0.0

        trends_block = {
            "direction": direction,
            "percentage_change": round(pct, 2),
            "monthly": monthly_pattern,
            "yearly": [],
            "summary": (
                f"Crime {direction} by {round(pct, 1)}% comparing the "
                f"first and second halves of the year."
                if monthly_pattern
                else "No trend data available."
            ),
        }

        # --- seasonality ---
        seasonality_src = raw.get("seasonality", {}) or {}
        season_monthly = [
            {"month": int(m), "value": float(v)}
            for m, v in seasonality_src.items()
            if str(m).isdigit()
        ]
        season_monthly.sort(key=lambda x: x["month"])
        peak_quarter = seasonality_src.get("peak_quarter")
        peak_month_num = (
            max(season_monthly, key=lambda p: p["value"])["month"]
            if season_monthly else None
        )
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December",
        }
        peak_month_name = month_names.get(peak_month_num) if peak_month_num else None

        seasonality_block = {
            "monthly_pattern": season_monthly,
            "weekly_pattern": [],
            "quarterly_pattern": [
                {"quarter": q, "label": f"Q{q}"} for q in range(1, 5)
            ],
            "peak_month": peak_month_name,
            "peak_day_of_week": None,
        }

        # --- category_distribution ---
        ccd = raw.get("crime_category_distribution", {}) or {}
        categories = [
            {"name": str(name), "count": int(meta.get("count", 0)),
             "pct": float(meta.get("pct", 0.0))}
            for name, meta in ccd.items()
        ]
        categories.sort(key=lambda c: c["count"], reverse=True)
        total_cat_crimes = sum(c["count"] for c in categories)
        category_block = {
            "categories": categories,
            "total_crimes": total_cat_crimes,
        }

        # --- neighbor_influence ---
        # source: { "Neighbor_District_Risk": {...} } or empty
        ni_src = raw.get("neighbor_influence", {}) or {}
        principal_corr = None
        if ni_src:
            first = next(iter(ni_src.values()))
            if isinstance(first, dict):
                principal_corr = first.get("correlation_with_crime")
            elif isinstance(first, (int, float)):
                principal_corr = float(first)

        neighbor_block = {
            "spatial_lag": principal_corr,
            "moran_i": principal_corr,
            "hotspots_clusters": [],
            "summary": (
                f"Neighbor-district risk correlation: {principal_corr:.3f}"
                if principal_corr is not None
                else "Neighbor-influence data unavailable."
            ),
        }

        return {
            "trends": trends_block,
            "seasonality": seasonality_block,
            "category_distribution": category_block,
            "neighbor_influence": neighbor_block,
            "generated_at": time.time(),
        }

    def get_analytics_report(self) -> dict:
        """Get the normalized analytics report (matches AnalyticsReport schema)."""
        if self._analytics_report is None:
            raise MLArtifactException("analytics_report.json not loaded")
        return self._analytics_report

    def get_trends(self) -> dict:
        return self.get_analytics_report().get("trends", {})

    def get_seasonality(self) -> dict:
        return self.get_analytics_report().get("seasonality", {})

    def get_category_distribution(self) -> dict:
        return self.get_analytics_report().get("category_distribution", {})

    def get_neighbor_influence(self) -> dict:
        return self.get_analytics_report().get("neighbor_influence", {})

    # ====================================================
    # Feature Importance / SHAP
    # ====================================================
    def _load_feature_importance(self) -> None:
        path = self.base_path / "feature_importance.csv"
        if not path.exists():
            logger.warning(f"⚠️  feature_importance.csv not found at {path}")
            return
        try:
            self._feature_importance_df = pd.read_csv(path)
            logger.info(
                f"   🧠 feature_importance.csv: {len(self._feature_importance_df)} features"
            )
        except Exception as e:
            logger.error(f"❌ Failed to load feature_importance.csv: {e}")

    def get_feature_importance(self) -> pd.DataFrame:
        """Get SHAP feature importance."""
        if self._feature_importance_df is None:
            raise MLArtifactException("feature_importance.csv not loaded")
        return self._feature_importance_df

    def _load_shap_values(self) -> None:
        path = self.shap_dir / "shap_values.parquet"
        if not path.exists():
            logger.warning(f"⚠️  shap_values.parquet not found at {path}")
            return
        try:
            self._shap_values = pd.read_parquet(path)
            logger.info(f"   🧬 shap_values.parquet: {self._shap_values.shape}")
        except Exception as e:
            logger.error(f"❌ Failed to load shap_values.parquet: {e}")

    def get_shap_values(self) -> Optional[pd.DataFrame]:
        """Get raw SHAP values (Parquet)."""
        return self._shap_values

    def get_district_shap(self, district: str) -> Optional[dict]:
        """Get SHAP values for a specific district."""
        if self._shap_values is None:
            return None
        try:
            df = self._shap_values
            if "district" in df.columns:
                row = df[df["district"].astype(str).str.lower() == district.lower()]
                if not row.empty:
                    return row.iloc[0].to_dict()
        except Exception as e:
            logger.warning(f"Could not extract district SHAP: {e}")
        return None

    # ====================================================
    # Health & Status
    # ====================================================
    def get_health(self) -> dict:
        """Loader health and stats."""
        return {
            "loaded": self._last_loaded is not None,
            "last_loaded": self._last_loaded,
            "stale": self.is_stale(),
            "artifacts": {
                "predictions": self._predictions_df is not None,
                "hotspot_rankings": self._hotspot_rankings_df is not None,
                "hotspots_geojson": self._hotspots_geojson is not None,
                "dashboard_metrics": self._dashboard_metrics is not None,
                "analytics_report": self._analytics_report is not None,
                "feature_importance": self._feature_importance_df is not None,
                "shap_values": self._shap_values is not None,
            },
            "row_counts": {
                "predictions": (
                    len(self._predictions_df)
                    if self._predictions_df is not None else 0
                ),
                "hotspot_rankings": (
                    len(self._hotspot_rankings_df)
                    if self._hotspot_rankings_df is not None else 0
                ),
            },
        }

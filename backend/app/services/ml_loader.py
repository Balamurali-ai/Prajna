"""
====================================================
ML Artifact Loader
====================================================
⚠️  READ-ONLY LOADER ⚠️
This module ONLY reads pre-computed ML outputs
from disk. It does NOT train, predict, or
engineer features.

It loads:
- outputs/predictions/predictions.csv
- outputs/predictions/hotspot_rankings.csv
- outputs/predictions/hotspots.geojson
- outputs/dashboard_metrics.json
- outputs/analytics_report.json
- outputs/feature_importance.csv
- outputs/shap/shap_values.parquet

The ML team owns these artifacts. This loader
serves them to the application.
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


class MLArtifactLoader:
    """
    Loads and caches ML-generated artifacts in memory.

    All artifacts are READ-ONLY. The loader never modifies
    or generates new predictions — it only serves what
    the ML pipeline has produced.
    """

    # Column name normalization maps.
    # ML team ships artifacts with Title_Case columns; the application
    # uses snake_case. Apply on every load so downstream code can rely
    # on a single schema regardless of how the artifact was authored.
    PREDICTIONS_COLUMN_MAP: dict[str, str] = {
        "District": "district",
        "Risk_Score": "risk_score",
        "Priority_Rank": "risk_rank",
        "Confidence": "confidence",
        "Predicted_Crime_Count": "predicted_crime_count",
    }

    HOTSPOT_RANKINGS_COLUMN_MAP: dict[str, str] = {
        "Risk_Score": "hotspot_score",
        "Hotspot_Rank": "rank",
        "h3_index": "h3_cell",
    }

    GEOJSON_PROPERTY_MAP: dict[str, str] = {
        "h3_index": "h3_cell",
        "risk_score": "hotspot_score",
    }

    @staticmethod
    def _normalize_dataframe(
        df: pd.DataFrame,
        column_map: dict[str, str],
    ) -> pd.DataFrame:
        """Rename columns per `column_map` if the source column is present."""
        rename = {src: dst for src, dst in column_map.items() if src in df.columns}
        if not rename:
            return df
        return df.rename(columns=rename)

    @staticmethod
    def _normalize_geojson(
        geojson: dict,
        property_map: dict[str, str],
    ) -> dict:
        """Rewrite feature properties per `property_map` (in place on a copy)."""
        if not isinstance(geojson, dict):
            return geojson
        features = geojson.get("features")
        if not isinstance(features, list):
            return geojson
        normalized = dict(geojson)
        normalized["features"] = [
            {**feat, "properties": {property_map.get(k, k): v for k, v in (feat.get("properties") or {}).items()}}
            if isinstance(feat, dict)
            else feat
            for feat in features
        ]
        return normalized

    def __init__(self, base_path: Optional[str] = None) -> None:
        self.base_path = Path(base_path or settings.ML_ARTIFACTS_PATH)
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

    async def load_all(self) -> None:
        """Load all ML artifacts into memory."""
        async with self._load_lock:
            logger.info(f"📂 Loading ML artifacts from {self.base_path}")
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
        logger.info("🔄 Refreshing ML artifacts...")
        await self.load_all()

    def is_stale(self) -> bool:
        if self._last_loaded is None:
            return True
        return (time.time() - self._last_loaded) > settings.ML_CACHE_REFRESH_SECONDS

    def _load_predictions(self) -> None:
        path = self.predictions_dir / "predictions.csv"
        if not path.exists():
            logger.warning(f"⚠️  predictions.csv not found at {path}")
            return
        try:
            df = pd.read_csv(path)
            self._predictions_df = self._normalize_dataframe(df, self.PREDICTIONS_COLUMN_MAP)
            logger.info(f"   📊 predictions.csv: {len(self._predictions_df)} rows")
        except Exception as e:
            logger.error(f"❌ Failed to load predictions.csv: {e}")
            raise MLArtifactException(f"Failed to load predictions: {e}")

    def get_predictions(self) -> pd.DataFrame:
        if self._predictions_df is None:
            raise MLArtifactException("predictions.csv not loaded")
        return self._predictions_df

    def get_district_prediction(self, district: str) -> Optional[dict]:
        df = self.get_predictions()
        row = df[df["district"].str.lower() == district.lower()]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def get_risk_rankings(self) -> pd.DataFrame:
        df = self.get_predictions()
        return df.sort_values("risk_rank", ascending=True)

    def get_top_n(self, n: int = 10) -> pd.DataFrame:
        df = self.get_risk_rankings()
        return df.head(n)

    def _load_hotspot_rankings(self) -> None:
        path = self.predictions_dir / "hotspot_rankings.csv"
        if not path.exists():
            logger.warning(f"⚠️  hotspot_rankings.csv not found at {path}")
            return
        try:
            df = pd.read_csv(path)
            self._hotspot_rankings_df = self._normalize_dataframe(df, self.HOTSPOT_RANKINGS_COLUMN_MAP)
            logger.info(f"   🔥 hotspot_rankings.csv: {len(self._hotspot_rankings_df)} cells")
        except Exception as e:
            logger.error(f"❌ Failed to load hotspot_rankings.csv: {e}")
            raise MLArtifactException(f"Failed to load hotspot rankings: {e}")

    def _load_hotspots_geojson(self) -> None:
        path = self.predictions_dir / "hotspots.geojson"
        if not path.exists():
            logger.warning(f"⚠️  hotspots.geojson not found at {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._hotspots_geojson = self._normalize_geojson(raw, self.GEOJSON_PROPERTY_MAP)
            features = self._hotspots_geojson.get("features", [])
            logger.info(f"   🗺️  hotspots.geojson: {len(features)} features")
        except Exception as e:
            logger.error(f"❌ Failed to load hotspots.geojson: {e}")
            raise MLArtifactException(f"Failed to load hotspots geojson: {e}")

    def get_hotspot_rankings(self) -> pd.DataFrame:
        if self._hotspot_rankings_df is None:
            raise MLArtifactException("hotspot_rankings.csv not loaded")
        return self._hotspot_rankings_df.sort_values("rank", ascending=True)

    def get_top_hotspots(self, n: Optional[int] = None) -> pd.DataFrame:
        df = self.get_hotspot_rankings()
        return df.head(n or settings.ML_HOTSPOT_TOP_N)

    def get_hotspots_geojson(self) -> dict:
        if self._hotspots_geojson is None:
            return {"type": "FeatureCollection", "features": []}
        return self._hotspots_geojson

    def _load_dashboard_metrics(self) -> None:
        path = self.base_path / "dashboard_metrics.json"
        if not path.exists():
            logger.warning(f"⚠️  dashboard_metrics.json not found at {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._dashboard_metrics = json.load(f)
            logger.info("   📈 dashboard_metrics.json: loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load dashboard_metrics.json: {e}")
            raise MLArtifactException(f"Failed to load dashboard metrics: {e}")

    def get_dashboard_metrics(self) -> dict:
        if self._dashboard_metrics is None:
            raise MLArtifactException("dashboard_metrics.json not loaded")
        return self._dashboard_metrics

    def _load_analytics_report(self) -> None:
        path = self.base_path / "analytics_report.json"
        if not path.exists():
            logger.warning(f"⚠️  analytics_report.json not found at {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._analytics_report = json.load(f)
            logger.info("   📑 analytics_report.json: loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load analytics_report.json: {e}")
            raise MLArtifactException(f"Failed to load analytics report: {e}")

    def get_analytics_report(self) -> dict:
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
        return self._shap_values

    def get_district_shap(self, district: str) -> Optional[dict]:
        if self._shap_values is None:
            return None
        try:
            df = self._shap_values
            if "district" in df.columns:
                row = df[df["district"].str.lower() == district.lower()]
                if not row.empty:
                    return row.iloc[0].to_dict()
        except Exception as e:
            logger.warning(f"Could not extract district SHAP: {e}")
        return None

    def get_health(self) -> dict:
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

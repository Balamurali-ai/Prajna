"""
====================================================
ML Pipeline Configuration
====================================================
Centralized configuration for the ET AI Hackathon 2026
Geospatial Crime Pattern Intelligence pipeline.

This config replaces the original ``project.configs.config``
package layout. The codebase under ``ml/`` imports from
``ml.configs.config`` directly.
====================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


# ====================================================
# Paths
# ====================================================
ML_ROOT: Path = Path(__file__).resolve().parent.parent
ML_OUTPUTS_DIR: Path = ML_ROOT / "outputs"
ML_DATA_DIR: Path = ML_ROOT / "data"
ML_RAW_DATA_DIR: Path = ML_DATA_DIR / "raw"
ML_PROCESSED_DIR: Path = ML_DATA_DIR / "processed"
ML_INTERIM_DIR: Path = ML_DATA_DIR / "interim"
ML_EXTERNAL_DIR: Path = ML_DATA_DIR / "external"
ML_GEOJSON_DIR: Path = ML_DATA_DIR / "geojson"
ML_MODELS_DIR: Path = ML_OUTPUTS_DIR / "models"
ML_FIGURES_DIR: Path = ML_OUTPUTS_DIR / "figures"
ML_PREDICTIONS_DIR: Path = ML_OUTPUTS_DIR / "predictions"
ML_SHAP_DIR: Path = ML_OUTPUTS_DIR / "shap"
ML_REPORTS_DIR: Path = ML_OUTPUTS_DIR / "reports"

# Backwards-compatible absolute paths
DATASET_PARQUET: Path = ML_RAW_DATA_DIR / "crime_dataset_v2.parquet"
DATASET_CSV: Path = ML_RAW_DATA_DIR / "crime_dataset_v2.csv"
FEATURE_DICT: Path = ML_RAW_DATA_DIR / "feature_dictionary_v2.csv"
UNIT_YEAR_AGG: Path = ML_RAW_DATA_DIR / "unit_year_aggregates_v2.csv"
RAW_DATA_DIR: Path = ML_RAW_DATA_DIR

# Model artifact paths
RISK_MODEL_PATH: Path = ML_MODELS_DIR / "risk" / "risk_model.pkl"
HOTSPOT_MODEL_PATH: Path = ML_MODELS_DIR / "hotspot" / "hotspot_model.pkl"
MODEL_METRICS_PATH: Path = ML_OUTPUTS_DIR / "model_metrics.json"
PREDICTIONS_PATH: Path = ML_OUTPUTS_DIR / "predictions.csv"
HOTSPOT_RANKINGS_PATH: Path = ML_OUTPUTS_DIR / "hotspot_rankings.csv"
DASHBOARD_METRICS_PATH: Path = ML_OUTPUTS_DIR / "dashboard_metrics.json"
ANALYTICS_REPORT_PATH: Path = ML_OUTPUTS_DIR / "analytics_report.json"
ANALYTICS_SUMMARY_PATH: Path = ML_OUTPUTS_DIR / "analytics_summary.json"
EXPLANATION_JSON_PATH: Path = ML_SHAP_DIR / "explanation.json"
FEATURE_IMPORTANCE_PATH: Path = ML_OUTPUTS_DIR / "feature_importance.csv"
FINAL_REPORT_PATH: Path = ML_OUTPUTS_DIR / "FINAL_REPORT.md"
CRIME_HEATMAP: Path = ML_FIGURES_DIR / "crime_heatmap.png"
HOTSPOT_MAP: Path = ML_FIGURES_DIR / "hotspot_map.png"
HOTSPOT_GEOJSON_PATH: Path = ML_PREDICTIONS_DIR / "hotspots.geojson"
SHAP_VALUES_PATH: Path = ML_SHAP_DIR / "shap_values.parquet"
SHAP_SUMMARY_PLOT: Path = ML_FIGURES_DIR / "shap_summary.png"
PRED_VS_ACTUAL_PLOT: Path = ML_FIGURES_DIR / "pred_vs_actual.png"
RESIDUAL_PLOT: Path = ML_FIGURES_DIR / "residuals.png"
RISK_DISTRIBUTION_PLOT: Path = ML_FIGURES_DIR / "risk_distribution.png"
TOP20_RISK_PLOT: Path = ML_FIGURES_DIR / "top20_risk.png"
MONTHLY_TREND_PLOT: Path = ML_FIGURES_DIR / "monthly_trend.png"
FEATURE_IMPORTANCE_PLOT: Path = ML_FIGURES_DIR / "feature_importance.png"
NEIGHBOR_DENSITY_PLOT: Path = ML_FIGURES_DIR / "neighbor_density.png"

# Backwards-compatible aliases
OUTPUTS_DIR: Path = ML_OUTPUTS_DIR
FIGURES_DIR: Path = ML_FIGURES_DIR
SHAP_DIR: Path = ML_SHAP_DIR

# Optional h3 dependency
try:
    import h3 as _h3  # type: ignore
    H3 = _h3
    HAS_H3 = True
except Exception:
    H3 = None
    HAS_H3 = False


# ====================================================
# Data section
# ====================================================
@dataclass
class DataConfig:
    """Column names and time split for the crime dataset."""

    id_column: str = "Incident_ID"
    district_column: str = "District"
    state_column: str = "State"
    date_column: str = "Incident_Date"
    year_column: str = "Year"
    month_column: str = "Month"
    quarter_column: str = "Quarter"
    week_column: str = "Week"
    target_column: str = "Crime_Count_District"
    latitude_column: str = "Latitude"
    longitude_column: str = "Longitude"
    train_years: Tuple[int, ...] = (2021, 2022, 2023)
    val_years: Tuple[int, ...] = (2024,)
    test_years: Tuple[int, ...] = (2025, 2026)


# ====================================================
# Features section
# ====================================================
@dataclass
class FeaturesConfig:
    """Feature engineering knobs."""

    h3_resolution: int = 6
    max_lag_months: int = 12
    rolling_windows: List[int] = field(default_factory=lambda: [3, 6, 12])
    ema_span: int = 6


# ====================================================
# Model hyperparameters
# ====================================================
@dataclass
class RiskModelConfig:
    """LightGBM hyperparameters for the risk regression model."""

    n_estimators: int = 500
    learning_rate: float = 0.05
    max_depth: int = 7
    num_leaves: int = 31
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_alpha: float = 0.1
    reg_lambda: float = 0.1
    min_child_samples: int = 20
    random_state: int = 42
    n_jobs: int = -1
    verbose: int = -1
    early_stopping_rounds: int = 50


@dataclass
class HotspotModelConfig:
    """LightGBM hyperparameters for the hotspot regression model."""

    n_estimators: int = 500
    learning_rate: float = 0.05
    max_depth: int = 6
    num_leaves: int = 31
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_alpha: float = 0.1
    reg_lambda: float = 0.1
    min_child_samples: int = 20
    random_state: int = 42
    n_jobs: int = -1
    verbose: int = -1
    early_stopping_rounds: int = 50
    top_n_hotspots: int = 500


# ====================================================
# Evaluation
# ====================================================
@dataclass
class EvalConfig:
    n_splits: int = 5
    cv_gap: int = 1


# ====================================================
# SHAP
# ====================================================
@dataclass
class ShapConfig:
    max_display_features: int = 20
    background_samples: int = 100


# ====================================================
# Top-level CFG
# ====================================================
class _Config:
    """Aggregated configuration root."""

    def __init__(self) -> None:
        self.data = DataConfig()
        self.features = FeaturesConfig()
        self.risk_model = RiskModelConfig()
        self.hotspot_model = HotspotModelConfig()
        self.eval = EvalConfig()
        self.shap = ShapConfig()

    def ensure_dirs(self) -> Path:
        """Create all known output directories. Returns the outputs root."""
        for d in [
            ML_OUTPUTS_DIR, ML_DATA_DIR, ML_PROCESSED_DIR, ML_INTERIM_DIR,
            ML_EXTERNAL_DIR, ML_GEOJSON_DIR, ML_MODELS_DIR, ML_FIGURES_DIR,
            ML_PREDICTIONS_DIR, ML_SHAP_DIR, ML_REPORTS_DIR,
            ML_MODELS_DIR / "risk", ML_MODELS_DIR / "hotspot",
        ]:
            d.mkdir(parents=True, exist_ok=True)
        return ML_OUTPUTS_DIR


CFG: _Config = _Config()

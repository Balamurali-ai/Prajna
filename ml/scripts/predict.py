#!/usr/bin/env python3
"""
Prediction script for ET AI Hackathon 2026 — Geospatial Crime Pattern Intelligence.

Usage:
    python predict.py

Loads saved models and generates predictions + analytics on new data.
Requires train.py to have been run first (models must exist).
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure project root is in path. The original layout used
# ``project/`` as the package; we now use ``ml/`` and import via
# ``ml.<sub>``. Add the repository root so ``import ml`` resolves.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.dirname(_HERE))  # ml/

from ml.configs.config import (
    CFG, RISK_MODEL_PATH, HOTSPOT_MODEL_PATH, FINAL_REPORT_PATH, CRIME_HEATMAP,
    PREDICTIONS_PATH,
)
from ml.src.utils.logger import log
from ml.src.utils.helpers import load_pickle, save_json, compute_regression_metrics, ensure_serializable
from ml.src.data.loader import load_dataset, inspect_dataframe
from ml.src.data.preprocessing import (
    parse_dates, handle_missing_values, temporal_train_val_test_split,
    aggregate_by_district_month,
)
from ml.src.features.feature_builder import (
    build_risk_features, build_hotspot_features, get_feature_columns,
)
from ml.src.models.risk_model import RiskModel
from ml.src.models.hotspot_model import HotspotModel, hotspots_to_geojson
from ml.src.models.analytics_engine import AnalyticsEngine
from ml.src.evaluation.evaluate import evaluate_risk_model, evaluate_hotspot_model, save_model_metrics
from ml.src.visualization.charts import generate_all_plots
from ml.src.visualization.maps import crime_heatmap, hotspot_map


def generate_final_report(summary):
    """Generate FINAL_REPORT.md with all pipeline results."""
    lines = []
    lines.append("# FINAL REPORT — Geospatial Crime Pattern Intelligence")
    lines.append("")
    lines.append("## ET AI Hackathon 2026")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Dataset Summary")
    lines.append("- Total rows: " + str(summary.get("dataset_rows", "N/A")))
    lines.append("- Total columns: " + str(summary.get("dataset_columns", "N/A")))
    lines.append("- Years covered: 2021-2026")
    lines.append("- Source: crime_dataset_v2.parquet")
    lines.append("")
    lines.append("## 2. Missing Values")
    lines.append("- Missing values handled: median fill (numeric), mode fill (categorical)")
    lines.append("- Columns with >50% missing dropped automatically")
    lines.append("")
    lines.append("## 3. Feature Engineering")
    lines.append("- Temporal features: lag features, rolling mean/std (3m, 6m, 12m), EMA")
    lines.append("- Seasonal features: Month/Quarter sin-cos encoding")
    lines.append("- Growth features: growth rate, momentum, acceleration")
    lines.append("- Ratio features: weekend ratio, night crime ratio")
    lines.append("- Spatial features: neighbor crime density, population-normalized crime")
    lines.append("- H3 spatial indexing for hotspot detection (configurable resolution)")
    lines.append("")
    lines.append("## 4. Selected Features")
    lines.append("- Total features selected: " + str(summary.get("feature_count", "N/A")))
    lines.append("")
    lines.append("## 5. Models Used")
    lines.append("- **Risk Model**: LightGBM Regressor (crime intensity prediction)")
    lines.append("- **Hotspot Model**: H3 spatial indexing + LightGBM Regressor")
    lines.append("- **Explainability**: SHAP TreeExplainer")
    lines.append("- **Analytics Engine**: Automated trend/pattern analysis")
    lines.append("")
    lines.append("## 6. Hyperparameters")
    lines.append("- Risk Model: LR=0.05, max_depth=7, num_leaves=31, subsample=0.8, colsample=0.8")
    lines.append("- Hotspot Model: LR=0.05, max_depth=6, num_leaves=31, subsample=0.8")
    lines.append("- H3 resolution: 6 (configurable)")
    lines.append("- Early stopping rounds: 50")
    lines.append("")
    lines.append("## 7. Cross Validation Results")

    metrics = summary.get("metrics", {})
    risk_metrics = metrics.get("risk_model", {})
    cv = risk_metrics.get("cv", {})
    overall = cv.get("overall", {})

    if overall:
        lines.append("- Method: TimeSeriesSplit (5 folds, gap=1)")
        lines.append("- Overall RMSE: " + str(overall.get("RMSE", "N/A")))
        lines.append("- Overall MAE: " + str(overall.get("MAE", "N/A")))
        lines.append("- Overall R2: " + str(overall.get("R2", "N/A")))
        lines.append("- Overall MAPE: " + str(overall.get("MAPE", "N/A")) + "%")
    else:
        lines.append("- TimeSeriesSplit CV results available in model_metrics.json")

    test = risk_metrics.get("test", {})
    lines.append("")
    lines.append("## 8. Evaluation Metrics (Test Set)")
    lines.append("- RMSE: " + str(test.get("RMSE", "N/A")))
    lines.append("- MAE: " + str(test.get("MAE", "N/A")))
    lines.append("- R2: " + str(test.get("R2", "N/A")))
    lines.append("- MAPE: " + str(test.get("MAPE", "N/A")) + "%")
    lines.append("")
    lines.append("## 9. Feature Importance")
    lines.append("- Top features from LightGBM gain importance")
    lines.append("- SHAP-based global importance (mean |SHAP|)")
    lines.append("- Full details in outputs/feature_importance.csv")
    lines.append("")
    lines.append("## 10. SHAP Insights")
    lines.append("- Method: TreeExplainer (interventional perturbation)")
    lines.append("- Global importance + local explanations generated")
    lines.append("- Summary plot: outputs/figures/shap_summary.png")
    lines.append("- SHAP values: outputs/shap/shap_values.parquet")
    lines.append("- Explanation JSON: outputs/shap/explanation.json")
    lines.append("")
    lines.append("## 11. Top Risk Areas")
    lines.append("- District-level risk scores (0-100) generated")
    lines.append("- Priority ranking with confidence estimates")
    lines.append("- See outputs/predictions.csv for full results")
    lines.append("")
    lines.append("## 12. Top Hotspots")
    lines.append("- H3 cell-level crime predictions")
    lines.append("- Rankings with normalized risk scores")
    lines.append("- GeoJSON export for mapping")
    lines.append("- See outputs/hotspot_rankings.csv and outputs/predictions/hotspots.geojson")
    lines.append("")
    lines.append("## 13. Error Analysis")
    lines.append("- Residual plots available in outputs/figures/")
    lines.append("- Prediction vs Actual scatter plot")
    lines.append("- Residual distribution analysis")
    lines.append("")
    lines.append("## 14. Limitations")
    lines.append("- Dataset uses synthetic coordinates (real polygon-constrained)")
    lines.append("- Population data from Census 2011 (aged ~15 years)")
    lines.append("- H3 hotspot model requires h3 library")
    lines.append("- SHAP analysis requires shap library")
    lines.append("- No real-time prediction (batch inference only)")
    lines.append("")
    lines.append("## 15. Production Readiness")
    lines.append("- Modular Python with docstrings and type hints")
    lines.append("- Configuration-driven (project/configs/config.py)")
    lines.append("- Logging throughout (project/src/utils/logger.py)")
    lines.append("- All models serialized via pickle")
    lines.append("- All outputs in structured formats (CSV, JSON, GeoJSON, Parquet, PNG)")
    lines.append("- Temporal train/val/test split - no leakage")
    lines.append("")
    lines.append("## 16. Future Improvements")
    lines.append("- Integrate real-time streaming prediction")
    lines.append("- Add external covariates (weather, economic indicators)")
    lines.append("- Deploy as REST API with FastAPI")
    lines.append("- Add model drift monitoring")
    lines.append("- Support for additional spatial resolutions")
    lines.append("- Add ensemble methods (stacking, blending)")
    lines.append("- Dashboard integration with real maps (Mapbox, Leaflet)")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated automatically by ET Pipeline*")

    report_path = FINAL_REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info("Final report generated: %s", report_path)


def main():
    """Run prediction with saved models."""
    log.info("=" * 60)
    log.info("ET AI Hackathon 2026 — Prediction Script")
    log.info("=" * 60)

    CFG.ensure_dirs()

    # Load data
    df = load_dataset(use_parquet=True)
    df = parse_dates(df)
    df = handle_missing_values(df)

    meta = inspect_dataframe(df)
    log.info("Data loaded: %s rows", meta["shape"][0])

    # Load risk model
    if RISK_MODEL_PATH.exists():
        risk_model = RiskModel.load(RISK_MODEL_PATH)
        log.info("Risk model loaded from %s", RISK_MODEL_PATH)
    else:
        log.error("Risk model not found at %s. Run train.py first.", RISK_MODEL_PATH)
        return 1

    # Load hotspot model
    hotspot_model = None
    if HOTSPOT_MODEL_PATH.exists():
        hotspot_model = HotspotModel.load(HOTSPOT_MODEL_PATH)
        log.info("Hotspot model loaded from %s", HOTSPOT_MODEL_PATH)
    else:
        log.warning("Hotspot model not found, skipping hotspot predictions.")

    # Aggregate and build features
    _, _, test_df = temporal_train_val_test_split(df)
    test_agg = aggregate_by_district_month(test_df)
    test_feat = build_risk_features(test_agg)
    feature_cols = risk_model.feature_columns if hasattr(risk_model, 'feature_columns') else None
    if not feature_cols:
        feature_cols = get_feature_columns(test_feat)

    # Predict
    X_test = test_feat[feature_cols].fillna(0)
    metadata = test_feat[[CFG.data.district_column, CFG.data.year_column, CFG.data.month_column]].copy()
    predictions = risk_model.predict_risk_scores(X_test, district_df=metadata)

    out = ensure_serializable(predictions)
    out.to_csv(PREDICTIONS_PATH, index=False)
    log.info("Predictions saved: %s", PREDICTIONS_PATH)

    # Evaluate
    y_test = test_feat[CFG.data.target_column].values
    y_pred = risk_model.predict(X_test)
    metrics = compute_regression_metrics(y_test, y_pred)
    save_model_metrics({"risk_model": {"test": metrics}})
    log.info("Test metrics: %s", metrics)

    # Analytics
    engine = AnalyticsEngine()
    engine.compute_all(df, risk_predictions=predictions)
    engine.save_reports()

    # Visualizations
    generate_all_plots(
        df,
        risk_scores=predictions["Risk_Score"],
        y_true=y_test, y_pred=y_pred,
        risk_predictions=predictions,
    )
    crime_heatmap(df, save_path=CRIME_HEATMAP)

    # Final report
    summary = {
        "dataset_rows": meta["shape"][0],
        "dataset_columns": meta["shape"][1],
        "feature_count": len(feature_cols),
        "risk_model_trained": True,
        "hotspot_model_trained": hotspot_model is not None,
        "metrics": {"risk_model": {"test": metrics}},
    }
    generate_final_report(summary)

    log.info("=" * 60)
    log.info("PREDICTION COMPLETE")
    log.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

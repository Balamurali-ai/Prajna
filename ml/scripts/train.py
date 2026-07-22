#!/usr/bin/env python3
"""
Training script for the ET AI Hackathon 2026 — Geospatial Crime Pattern Intelligence.

Usage:
    python train.py

Runs the full pipeline:
1. Load / preprocess data
2. Feature engineering
3. Train Risk Model (LightGBM Regressor)
4. Train Hotspot Model (H3 + LightGBM Regressor)
5. SHAP Explainability
6. Analytics Engine
7. Visualizations
8. Save models, predictions, reports
"""

import sys
import os

# Ensure project root is in path. The original layout used
# ``project/`` as the package; we now use ``ml/`` and import via
# ``ml.<sub>``. Add the repository root so ``import ml`` resolves.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.dirname(_HERE))  # ml/

from ml.src.pipeline import Pipeline
from ml.src.utils.logger import log


def main():
    """Execute the full training pipeline."""
    log.info("=" * 60)
    log.info("ET AI Hackathon 2026 — Training Pipeline")
    log.info("=" * 60)

    pipeline = Pipeline()
    summary = pipeline.run_all()

    log.info("=" * 60)
    log.info("TRAINING COMPLETE")
    log.info("Models saved:")
    log.info("  - models/risk/risk_model.pkl")
    log.info("  - models/hotspot/hotspot_model.pkl")
    log.info("Outputs saved:")
    log.info("  - outputs/predictions.csv")
    log.info("  - outputs/hotspot_rankings.csv")
    log.info("  - outputs/dashboard_metrics.json")
    log.info("  - outputs/analytics_report.json")
    log.info("  - outputs/feature_importance.csv")
    log.info("  - outputs/shap_summary.png")
    log.info("  - outputs/model_metrics.json")
    log.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Main pipeline orchestrator for the ET AI Hackathon 2026.

Coordinates:
1. Data loading & preprocessing
2. Feature engineering
3. Model training (Risk + Hotspot)
4. Cross-validation
5. Explainability (SHAP)
6. Prediction
7. Analytics
8. Visualization
9. Final report generation
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ml.configs.config import (
    CFG, PREDICTIONS_PATH, HOTSPOT_RANKINGS_PATH, HOTSPOT_GEOJSON_PATH,
    CRIME_HEATMAP, HOTSPOT_MAP, NEIGHBOR_DENSITY_PLOT,
)
from ml.src.utils.logger import log
from ml.src.utils.helpers import (
    save_pickle, load_pickle, save_json, compute_regression_metrics,
    ensure_serializable,
)
from ml.src.data.loader import load_dataset, load_feature_dictionary, inspect_dataframe
from ml.src.data.preprocessing import (
    parse_dates, handle_missing_values, filter_rows_without_coordinates,
    temporal_train_val_test_split, aggregate_by_district_month,
)
from ml.src.features.feature_builder import (
    build_risk_features, build_hotspot_features, get_feature_columns,
)
from ml.src.models.risk_model import RiskModel
from ml.src.models.hotspot_model import HotspotModel, hotspots_to_geojson
from ml.src.models.analytics_engine import AnalyticsEngine
from ml.src.explainability.shap_analysis import ShapAnalyzer
from ml.src.evaluation.evaluate import (
    timeseries_cross_validation, evaluate_risk_model, save_model_metrics,
)
from ml.src.visualization.charts import generate_all_plots
from ml.src.visualization.maps import crime_heatmap, hotspot_map, neighbor_density_map


class Pipeline:
    """End-to-end ML pipeline for Geospatial Crime Pattern Intelligence."""

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.agg_df: Optional[pd.DataFrame] = None
        self.train_df: Optional[pd.DataFrame] = None
        self.val_df: Optional[pd.DataFrame] = None
        self.test_df: Optional[pd.DataFrame] = None
        self.risk_model: Optional[RiskModel] = None
        self.hotspot_model: Optional[HotspotModel] = None
        self.risk_predictions: Optional[pd.DataFrame] = None
        self.hotspot_rankings: Optional[pd.DataFrame] = None
        self.shap_analyzer: Optional[ShapAnalyzer] = None
        self.analytics: Optional[AnalyticsEngine] = None
        self.metrics: Dict = {}
        self.feature_cols: List[str] = []
        self.dataset_meta: Dict = {}

    def run_all(self) -> Dict:
        """Execute the complete pipeline.

        Returns
        -------
        Dict
            Summary of all results and outputs.
        """
        log.info("=" * 60)
        log.info("ET AI Hackathon 2026 — Pipeline Start")
        log.info("=" * 60)

        CFG.ensure_dirs()

        # Step 1: Load data
        self._load_data()

        # Step 2: Preprocess
        self._preprocess()

        # Step 3: Feature engineering
        self._engineer_features()

        # Step 4: Train risk model
        self._train_risk_model()

        # Step 5: Train hotspot model
        self._train_hotspot_model()

        # Step 6: Explainability
        self._explain()

        # Step 7: Analytics
        self._analyze()

        # Step 8: Visualize
        self._visualize()

        # Step 9: Summary
        summary = self._summarize()

        log.info("=" * 60)
        log.info("Pipeline Complete")
        log.info("=" * 60)
        return summary

    def _load_data(self):
        """Load dataset and feature dictionary."""
        log.info("--- Step 1/9: Loading Data ---")
        self.df = load_dataset(use_parquet=True)
        self.dataset_meta = inspect_dataframe(self.df)
        fd = load_feature_dictionary()
        log.info("Loaded feature dictionary: %s entries", len(fd) if len(fd) > 0 else 0)

    def _preprocess(self):
        """Preprocess: parse dates, handle missing values, temporal split."""
        log.info("--- Step 2/9: Preprocessing ---")
        df = parse_dates(self.df)
        df = handle_missing_values(df)
        self.df = df

        # Test/train/val split
        train, val, test = temporal_train_val_test_split(self.df)
        self.train_df = train
        self.val_df = val
        self.test_df = test

    def _engineer_features(self):
        """Build features for both risk and hotspot models."""
        log.info("--- Step 3/9: Feature Engineering ---")

        # Aggregate by district-month for risk model
        train_agg = aggregate_by_district_month(self.train_df)
        val_agg = aggregate_by_district_month(self.val_df)
        test_agg = aggregate_by_district_month(self.test_df)

        # Build risk features
        train_feat = build_risk_features(train_agg)
        val_feat = build_risk_features(val_agg)
        test_feat = build_risk_features(test_agg)

        # Combine for consistent feature set
        full_feat = pd.concat([train_feat, val_feat, test_feat], ignore_index=True)
        self.feature_cols = get_feature_columns(full_feat)
        log.info("Selected %s features for modelling", len(self.feature_cols))

        # Store aggregated data
        self.agg_df = {
            "train": train_feat,
            "val": val_feat,
            "test": test_feat,
        }

    def _train_risk_model(self):
        """Train and evaluate the risk scoring model."""
        log.info("--- Step 4/9: Risk Model Training ---")

        target = CFG.data.target_column
        train_feat = self.agg_df["train"]
        val_feat = self.agg_df["val"]
        test_feat = self.agg_df["test"]

        # Align columns
        X_train = train_feat[self.feature_cols].fillna(0)
        y_train = train_feat[target]
        X_val = val_feat[self.feature_cols].fillna(0)
        y_val = val_feat[target]
        X_test = test_feat[self.feature_cols].fillna(0)
        y_test = test_feat[target]

        # Train with validation for early stopping
        self.risk_model = RiskModel()
        self.risk_model.fit(
            X_train, y_train, X_val, y_val, feature_columns=self.feature_cols
        )

        # Cross-validation on combined train+val
        X_cv = pd.concat([X_train, X_val], ignore_index=True)
        y_cv = pd.concat([y_train, y_val], ignore_index=True)
        log.info("Running time-series CV...")
        cv_results = timeseries_cross_validation(
            RiskModel, X_cv, y_cv, self.feature_cols, n_splits=CFG.eval.n_splits
        )

        # Test evaluation
        test_metrics = evaluate_risk_model(self.risk_model, X_test, y_test)
        self.metrics["risk_model"] = {
            "cv": cv_results,
            "test": test_metrics,
        }

        # Generate predictions
        all_data = pd.concat(
            [train_feat, val_feat, test_feat], ignore_index=True
        )
        metadata = all_data[[CFG.data.district_column, CFG.data.year_column,
                              CFG.data.month_column]].copy()
        self.risk_predictions = self.risk_model.predict_risk_scores(
            all_data[self.feature_cols].fillna(0),
            district_df=metadata,
        )

        # Save model
        self.risk_model.save()
        log.info("Risk model saved.")

    def _train_hotspot_model(self):
        """Train and evaluate the hotspot detection model."""
        log.info("--- Step 5/9: Hotspot Model Training ---")

        # Build H3 features
        train_h3 = build_hotspot_features(self.train_df)
        val_h3 = build_hotspot_features(self.val_df)
        test_h3 = build_hotspot_features(self.test_df)

        # Get feature columns for hotspot model
        hotspot_cols = get_feature_columns(
            train_h3, exclude_cols=["h3_index", "crime_count"]
        )
        log.info("Hotspot feature columns: %s", len(hotspot_cols))

        if len(hotspot_cols) == 0:
            log.warning("No hotspot features available; skipping hotspot model.")
            self.hotspot_model = None
            self.hotspot_rankings = pd.DataFrame()
            return

        X_train_h3 = train_h3[hotspot_cols].fillna(0)
        y_train_h3 = train_h3["crime_count"]
        X_val_h3 = val_h3[hotspot_cols].fillna(0)
        y_val_h3 = val_h3["crime_count"]
        X_test_h3 = test_h3[hotspot_cols].fillna(0)
        y_test_h3 = test_h3["crime_count"]

        self.hotspot_model = HotspotModel()
        self.hotspot_model.fit(
            X_train_h3, y_train_h3, X_val_h3, y_val_h3,
            feature_columns=hotspot_cols,
        )

        # Predict on combined data
        all_h3 = pd.concat([train_h3, val_h3, test_h3], ignore_index=True)
        X_all_h3 = all_h3[hotspot_cols].fillna(0)
        cell_meta = all_h3[["h3_index", "latitude", "longitude",
                            CFG.data.year_column, CFG.data.month_column]].copy()

        rankings, top_hotspots = self.hotspot_model.predict_hotspots(
            X_all_h3, cell_metadata=cell_meta
        )
        self.hotspot_rankings = rankings

        # Save model
        self.hotspot_model.save()

        # Save rankings CSV
        rankings.to_csv(HOTSPOT_RANKINGS_PATH, index=False)
        log.info("Saved hotspot rankings: %s", HOTSPOT_RANKINGS_PATH)

        # Save GeoJSON
        geojson = hotspots_to_geojson(top_hotspots)
        save_json(geojson, HOTSPOT_GEOJSON_PATH)

    def _explain(self):
        """Run SHAP explainability on the risk model."""
        log.info("--- Step 6/9: Explainability ---")

        if self.risk_model is None or not self.risk_model.is_fitted:
            log.warning("Risk model not fitted; skipping SHAP.")
            return

        train_feat = self.agg_df["train"]
        X_bg = train_feat[self.feature_cols].fillna(0).sample(
            min(CFG.shap.background_samples, len(train_feat)), random_state=42
        )

        self.shap_analyzer = ShapAnalyzer(
            self.risk_model.model, X_bg, self.feature_cols
        )
        self.shap_analyzer.fit()
        export_paths = self.shap_analyzer.export()
        log.info("SHAP analysis complete: %s", export_paths)

    def _analyze(self):
        """Run analytics engine."""
        log.info("--- Step 7/9: Analytics ---")

        engine = AnalyticsEngine()
        engine.compute_all(
            self.df,
            risk_predictions=self.risk_predictions,
            hotspot_rankings=self.hotspot_rankings,
        )
        engine.save_reports()
        self.analytics = engine
        log.info("Analytics complete.")

    def _visualize(self):
        """Generate all visualizations."""
        log.info("--- Step 8/9: Visualizations ---")

        # Charts
        risk_scores = self.risk_predictions["Risk_Score"] if self.risk_predictions is not None else None
        fi = self.shap_analyzer.global_importance() if self.shap_analyzer else None

        # Get y_true, y_pred for test
        y_true = None
        y_pred = None
        if self.agg_df and self.risk_model:
            test_feat = self.agg_df["test"]
            if len(test_feat) > 0:
                y_true = test_feat[CFG.data.target_column].values
                y_pred = self.risk_model.predict(test_feat[self.feature_cols].fillna(0))

        generate_all_plots(
            self.df,
            risk_scores=risk_scores,
            feature_importance=fi,
            y_true=y_true,
            y_pred=y_pred,
            risk_predictions=self.risk_predictions,
        )

        # Maps
        crime_heatmap(self.df, save_path=CRIME_HEATMAP)
        if self.hotspot_rankings is not None and len(self.hotspot_rankings) > 0:
            hotspot_map(self.hotspot_rankings, self.df, save_path=HOTSPOT_MAP)
        neighbor_density_map(self.df, save_path=NEIGHBOR_DENSITY_PLOT)

        log.info("Visualizations generated.")

    def _summarize(self) -> Dict:
        """Generate final summary with model metrics.

        Saves model_metrics.json and predictions.csv.

        Returns
        -------
        Dict
            Summary of pipeline results.
        """
        log.info("--- Step 9/9: Summary ---")

        # Save predictions
        if self.risk_predictions is not None:
            out = ensure_serializable(self.risk_predictions)
            out.to_csv(PREDICTIONS_PATH, index=False)
            log.info("Saved predictions: %s", PREDICTIONS_PATH)

        # Save metrics
        save_model_metrics(self.metrics)

        # Build summary
        summary = {
            "dataset_rows": len(self.df),
            "dataset_columns": len(self.df.columns),
            "feature_count": len(self.feature_cols),
            "risk_model_trained": self.risk_model is not None,
            "hotspot_model_trained": self.hotspot_model is not None,
            "shap_computed": self.shap_analyzer is not None,
            "analytics_computed": self.analytics is not None,
            "metrics": self.metrics,
        }

        log.info("Pipeline summary: %s", summary)
        return summary


def run_pipeline() -> Dict:
    """Convenience function to instantiate and run the pipeline.

    Returns
    -------
    Dict
        Pipeline summary.
    """
    pipeline = Pipeline()
    return pipeline.run_all()

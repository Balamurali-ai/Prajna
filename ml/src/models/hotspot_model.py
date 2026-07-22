"""
Hotspot Detection Model — Model 2.

Uses H3 spatial indexing + LightGBM regression to predict next-month crime counts,
then ranks H3 cells to identify top hotspots.

No hotspot classifier — hotspots are determined post-prediction by ranking.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

import lightgbm as lgb

from ml.configs.config import CFG, HOTSPOT_MODEL_PATH
from ml.src.utils.logger import log
from ml.src.utils.helpers import save_pickle, load_pickle, save_json


class HotspotModel:
    """Hotspot detection model using H3 spatial indexing.

    Predicts crime count per H3 cell per month, then ranks cells by predicted
    risk to identify top hotspot areas.

    Parameters
    ----------
    model_params : dict, optional
        LightGBM parameters. Falls back to CFG.hotspot_model defaults.
    """

    def __init__(self, model_params: Optional[Dict] = None):
        self.params = model_params or {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "n_estimators": CFG.hotspot_model.n_estimators,
            "learning_rate": CFG.hotspot_model.learning_rate,
            "max_depth": CFG.hotspot_model.max_depth,
            "num_leaves": CFG.hotspot_model.num_leaves,
            "subsample": CFG.hotspot_model.subsample,
            "colsample_bytree": CFG.hotspot_model.colsample_bytree,
            "reg_alpha": CFG.hotspot_model.reg_alpha,
            "reg_lambda": CFG.hotspot_model.reg_lambda,
            "min_child_samples": CFG.hotspot_model.min_child_samples,
            "random_state": CFG.hotspot_model.random_state,
            "n_jobs": CFG.hotspot_model.n_jobs,
            "verbose": CFG.hotspot_model.verbose,
        }
        self.model: Optional[lgb.LGBMRegressor] = None
        self.feature_columns: List[str] = []
        self.is_fitted = False

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        feature_columns: Optional[List[str]] = None,
    ) -> "HotspotModel":
        """Train the hotspot LightGBM model.

        Parameters
        ----------
        X_train : pd.DataFrame
            Training features.
        y_train : pd.Series
            Training target.
        X_val : pd.DataFrame, optional
            Validation features for early stopping.
        y_val : pd.Series, optional
            Validation target.
        feature_columns : list, optional
            Feature column names.

        Returns
        -------
        HotspotModel
            Fitted model instance.
        """
        if feature_columns is not None:
            self.feature_columns = feature_columns

        self.model = lgb.LGBMRegressor(**self.params)

        eval_set = None
        callbacks = None
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]
            callbacks = [
                lgb.early_stopping(CFG.hotspot_model.early_stopping_rounds, verbose=False),
                lgb.log_evaluation(0),
            ]

        self.model.fit(
            X_train, y_train, eval_set=eval_set, eval_metric="rmse", callbacks=callbacks,
        )
        self.is_fitted = True
        log.info(
            "Hotspot model trained: %s features",
            self.model.n_features_in_,
        )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict crime counts for H3 cells.

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix.

        Returns
        -------
        np.ndarray
            Predicted crime counts.
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")
        return self.model.predict(X, num_iteration=self.model.best_iteration_)

    def predict_hotspots(
        self,
        X: pd.DataFrame,
        cell_metadata: pd.DataFrame = None,
        top_n: int = None,
    ) -> pd.DataFrame:
        """Rank H3 cells by predicted crime count to identify hotspots.

        Algorithm:
        1. Predict crime count per H3 cell
        2. Normalize to risk score
        3. Rank cells
        4. Return top N as hotspots

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix for H3 cells.
        cell_metadata : pd.DataFrame, optional
            DataFrame with h3_index, latitude, longitude, year, month.
        top_n : int, optional
            Number of top hotspots to return.

        Returns
        -------
        pd.DataFrame
            Hotspot rankings with cell, risk score, rank, lat/lon.
        """
        if top_n is None:
            top_n = CFG.hotspot_model.top_n_hotspots

        preds = self.predict(X)

        # Normalize to risk score
        min_p, max_p = preds.min(), preds.max()
        if max_p > min_p:
            risk_scores = (preds - min_p) / (max_p - min_p) * 100
        else:
            risk_scores = np.zeros_like(preds)

        # Rank (1 = highest risk)
        rank = np.argsort(np.argsort(-risk_scores)) + 1

        results = pd.DataFrame({
            "Predicted_Crime_Count": np.round(preds, 2),
            "Risk_Score": np.round(risk_scores, 2),
            "Hotspot_Rank": rank,
        })

        if cell_metadata is not None:
            for col in cell_metadata.columns:
                if col in cell_metadata.columns and col not in results.columns:
                    results[col] = cell_metadata[col].values

        # Sort by rank and get top N
        results = results.sort_values("Hotspot_Rank").reset_index(drop=True)
        hotspots = results.head(top_n)

        log.info(
            "Hotspot prediction complete: %s cells ranked, top %s hotspots",
            len(results), top_n,
        )
        return results, results  # (all_rankings, top_hotspots)

    def get_feature_importance(self) -> pd.DataFrame:
        """Return feature importance from the trained model.

        Returns
        -------
        pd.DataFrame
            Feature importance sorted by gain.
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")
        importance = self.model.booster_.feature_importance(importance_type="gain")
        fi = pd.DataFrame({
            "feature": self.feature_columns,
            "importance_gain": importance,
        })
        fi = fi.sort_values("importance_gain", ascending=False).reset_index(drop=True)
        fi["importance_pct"] = (
            fi["importance_gain"] / fi["importance_gain"].sum() * 100
        ).round(2)
        return fi

    def save(self, path: Path = None) -> Path:
        """Save model to disk.

        Parameters
        ----------
        path : Path, optional
            Save path.

        Returns
        -------
        Path
            Path to saved model.
        """
        if path is None:
            path = HOTSPOT_MODEL_PATH
        save_pickle(self, path)
        return path

    @classmethod
    def load(cls, path: Path = None) -> "HotspotModel":
        """Load model from disk.

        Parameters
        ----------
        path : Path, optional
            Load path.

        Returns
        -------
        HotspotModel
            Loaded model instance.
        """
        if path is None:
            path = HOTSPOT_MODEL_PATH
        return load_pickle(path)


def hotspots_to_geojson(hotspot_df: pd.DataFrame) -> Dict:
    """Convert hotspot rankings to GeoJSON FeatureCollection.

    Parameters
    ----------
    hotspot_df : pd.DataFrame
        Hotspot data with h3_index, latitude, longitude, Risk_Score columns.

    Returns
    -------
    Dict
        GeoJSON FeatureCollection.
    """
    features = []
    for _, row in hotspot_df.iterrows():
        if "h3_index" not in row:
            continue
        try:
            import h3
            boundary = h3.cell_to_boundary(row["h3_index"])
            coords = [[[lng, lat] for lat, lng in boundary]]
        except Exception:
            coords = [[
                [row.get("longitude", 0), row.get("latitude", 0)],
            ]]

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": coords,
            },
            "properties": {
                "h3_index": row.get("h3_index", ""),
                "risk_score": float(row.get("Risk_Score", 0)),
                "rank": int(row.get("Hotspot_Rank", 0)),
                "predicted_crime_count": float(row.get("Predicted_Crime_Count", 0)),
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "model": "hotspot_lgbm",
            "h3_resolution": CFG.features.h3_resolution,
            "total_hotspots": len(features),
        },
    }
    return geojson

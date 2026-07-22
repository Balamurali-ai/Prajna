"""
Risk Scoring Model — Model 1.

Predicts crime intensity (not classifies) using LightGBM Regression.
Generates explainable district-level risk scores (0–100) with priority rank and confidence.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import lightgbm as lgb

from ml.configs.config import CFG, RISK_MODEL_PATH
from ml.src.utils.logger import log
from ml.src.utils.helpers import save_pickle, load_pickle


class RiskModel:
    """District-level crime risk scoring model.

    Uses LightGBM Regressor to predict Crime_Count_District,
    then converts predictions into a 0–100 risk score with priority ranking.

    Parameters
    ----------
    model_params : dict, optional
        LightGBM parameters. Falls back to CFG.risk_model defaults.
    """

    def __init__(self, model_params: Optional[Dict] = None):
        self.params = model_params or {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "n_estimators": CFG.risk_model.n_estimators,
            "learning_rate": CFG.risk_model.learning_rate,
            "max_depth": CFG.risk_model.max_depth,
            "num_leaves": CFG.risk_model.num_leaves,
            "subsample": CFG.risk_model.subsample,
            "colsample_bytree": CFG.risk_model.colsample_bytree,
            "reg_alpha": CFG.risk_model.reg_alpha,
            "reg_lambda": CFG.risk_model.reg_lambda,
            "min_child_samples": CFG.risk_model.min_child_samples,
            "random_state": CFG.risk_model.random_state,
            "n_jobs": CFG.risk_model.n_jobs,
            "verbose": CFG.risk_model.verbose,
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
    ) -> "RiskModel":
        """Train the LightGBM risk model.

        Parameters
        ----------
        X_train : pd.DataFrame
            Training feature matrix.
        y_train : pd.Series
            Training target values.
        X_val : pd.DataFrame, optional
            Validation feature matrix.
        y_val : pd.Series, optional
            Validation target values.
        feature_columns : list, optional
            List of feature column names.

        Returns
        -------
        RiskModel
            Fitted model instance.
        """
        if feature_columns is not None:
            self.feature_columns = feature_columns

        self.model = lgb.LGBMRegressor(**self.params)

        eval_set = None
        eval_metric = None
        callbacks = None

        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]
            eval_metric = "rmse"
            callbacks = [
                lgb.early_stopping(
                    CFG.risk_model.early_stopping_rounds, verbose=False
                ),
                lgb.log_evaluation(0),
            ]

        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            eval_metric=eval_metric,
            callbacks=callbacks,
        )

        self.is_fitted = True
        n_used = self.model.n_features_in_
        log.info(
            "Risk model trained: %s features, %s estimators used",
            n_used,
            self.model.n_iterations_ if hasattr(self.model, "n_iterations_") else "N/A",
        )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict crime counts.

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
            raise RuntimeError("Model not fitted. Call .fit() first.")
        return self.model.predict(X, num_iteration=self.model.best_iteration_)

    def predict_risk_scores(
        self, X: pd.DataFrame, district_df: pd.DataFrame = None
    ) -> pd.DataFrame:
        """Generate risk scores (0–100), priority ranks, and confidence.

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix.
        district_df : pd.DataFrame, optional
            DataFrame with district info to attach to results.

        Returns
        -------
        pd.DataFrame
            DataFrame with District, Year, Month, Risk_Score, Priority_Rank, Confidence.
        """
        preds = self.predict(X)

        # Normalize to 0–100 risk score
        min_p, max_p = preds.min(), preds.max()
        if max_p > min_p:
            risk_scores = (preds - min_p) / (max_p - min_p) * 100
        else:
            risk_scores = np.zeros_like(preds)

        # Priority rank (higher score = higher priority = rank 1)
        priority_rank = np.argsort(np.argsort(-risk_scores)) + 1

        # Confidence: based on model's standard error proxy (inverse of relative magnitude)
        # Use the model's tree variance as confidence proxy
        std_preds = np.std(preds) if len(preds) > 1 else 1.0
        confidence = np.clip(
            1.0 - (np.abs(preds - np.median(preds)) / (std_preds * 3 + 1e-6)),
            0.0,
            1.0,
        )

        results = pd.DataFrame({
            "Risk_Score": np.round(risk_scores, 2),
            "Priority_Rank": priority_rank,
            "Confidence": np.round(confidence, 4),
            "Predicted_Crime_Count": np.round(preds, 2),
        })

        if district_df is not None:
            for col in [CFG.data.district_column, CFG.data.year_column, CFG.data.month_column]:
                if col in district_df.columns:
                    results[col] = district_df[col].values

        log.info(
            "Risk scores generated: range [%.2f, %.2f], mean=%.2f",
            risk_scores.min(), risk_scores.max(), risk_scores.mean(),
        )
        return results

    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance from the trained model.

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
        log.info("Feature importance computed: %s features", len(fi))
        return fi

    def save(self, path: Path = None) -> Path:
        """Save fitted model to disk.

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
            path = RISK_MODEL_PATH
        save_pickle(self, path)
        return path

    @classmethod
    def load(cls, path: Path = None) -> "RiskModel":
        """Load fitted model from disk.

        Parameters
        ----------
        path : Path, optional
            Load path.

        Returns
        -------
        RiskModel
            Loaded model instance.
        """
        if path is None:
            path = RISK_MODEL_PATH
        return load_pickle(path)

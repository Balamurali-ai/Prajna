"""
Evaluation module for risk and hotspot models.

Uses TimeSeriesSplit for temporal cross-validation.
No random split, no leakage.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.model_selection import TimeSeriesSplit

from ml.configs.config import CFG, MODEL_METRICS_PATH
from ml.src.utils.logger import log
from ml.src.utils.helpers import compute_regression_metrics, save_json


def timeseries_cross_validation(
    model_class,
    X: pd.DataFrame,
    y: pd.Series,
    feature_columns: List[str],
    n_splits: int = None,
    gap: int = None,
) -> Dict:
    """Perform time-series cross-validation.

    Uses sklearn's TimeSeriesSplit with a gap between train/test.

    Parameters
    ----------
    model_class : class
        Model class with .fit() and .predict() methods.
    X : pd.DataFrame
        Feature matrix (must be in temporal order).
    y : pd.Series
        Target values.
    feature_columns : List[str]
        Feature names.
    n_splits : int, optional
        Number of CV folds.
    gap : int, optional
        Gap between train/test.

    Returns
    -------
    Dict
        CV results with per-fold and aggregate metrics.
    """
    if n_splits is None:
        n_splits = min(CFG.eval.n_splits, len(X) // 5)
    if gap is None:
        gap = CFG.eval.cv_gap

    tscv = TimeSeriesSplit(n_splits=n_splits, gap=gap)
    fold_metrics = []
    all_y_true = []
    all_y_pred = []

    for fold_idx, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = model_class()
        model.fit(X_train, y_train, feature_columns=feature_columns)
        y_pred = model.predict(X_test)

        metrics = compute_regression_metrics(y_test.values, y_pred)
        metrics["fold"] = fold_idx + 1
        metrics["train_size"] = len(train_idx)
        metrics["test_size"] = len(test_idx)
        fold_metrics.append(metrics)
        all_y_true.extend(y_test.tolist())
        all_y_pred.extend(y_pred.tolist())

        log.info(
            "CV Fold %d/%d: RMSE=%.4f, MAE=%.4f, R²=%.4f",
            fold_idx + 1, n_splits, metrics["RMSE"], metrics["MAE"], metrics["R2"],
        )

    # Aggregate metrics on all predictions
    overall_metrics = compute_regression_metrics(
        np.array(all_y_true), np.array(all_y_pred)
    )
    overall_metrics["n_splits"] = n_splits
    overall_metrics["total_samples"] = len(all_y_true)

    results = {
        "overall": overall_metrics,
        "per_fold": fold_metrics,
    }

    log.info(
        "CV complete: RMSE=%.4f, MAE=%.4f, R²=%.4f",
        overall_metrics["RMSE"], overall_metrics["MAE"], overall_metrics["R2"],
    )
    return results


def evaluate_risk_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict:
    """Evaluate risk model on test set.

    Parameters
    ----------
    model : RiskModel
        Fitted risk model.
    X_test : pd.DataFrame
        Test features.
    y_test : pd.Series
        Test target.

    Returns
    -------
    Dict
        Test set metrics.
    """
    y_pred = model.predict(X_test)
    metrics = compute_regression_metrics(y_test.values, y_pred)
    log.info(
        "Test evaluation: RMSE=%.4f, MAE=%.4f, R²=%.4f, MAPE=%.2f%%",
        metrics["RMSE"], metrics["MAE"], metrics["R2"], metrics["MAPE"],
    )
    return metrics


def evaluate_hotspot_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict:
    """Evaluate hotspot model on test set.

    Parameters
    ----------
    model : HotspotModel
        Fitted hotspot model.
    X_test : pd.DataFrame
        Test features.
    y_test : pd.Series
        Test target.

    Returns
    -------
    Dict
        Test set metrics.
    """
    y_pred = model.predict(X_test)
    metrics = compute_regression_metrics(y_test.values, y_pred)
    log.info(
        "Hotspot test: RMSE=%.4f, MAE=%.4f, R²=%.4f, MAPE=%.2f%%",
        metrics["RMSE"], metrics["MAE"], metrics["R2"], metrics["MAPE"],
    )
    return metrics


def save_model_metrics(metrics: Dict) -> None:
    """Save model evaluation metrics to JSON.

    Parameters
    ----------
    metrics : Dict
        Metrics dictionary.
    """
    save_json(metrics, MODEL_METRICS_PATH)
    log.info("Saved model metrics: %s", MODEL_METRICS_PATH)

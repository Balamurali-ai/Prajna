"""
Utility helper functions for the pipeline.
"""

import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from ml.src.utils.logger import log


def save_pickle(obj: Any, path: Path) -> None:
    """Serialize object to pickle file.

    Parameters
    ----------
    obj : Any
        Python object to serialize.
    path : Path
        Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    log.info("Saved pickle: %s (%.2f MB)", path, path.stat().st_size / 1e6)


def load_pickle(path: Path) -> Any:
    """Load serialized pickle file.

    Parameters
    ----------
    path : Path
        Source file path.

    Returns
    -------
    Any
        Deserialized object.
    """
    with open(path, "rb") as f:
        obj = pickle.load(f)
    log.info("Loaded pickle: %s", path)
    return obj


def save_json(data: Any, path: Path) -> None:
    """Save data as JSON.

    Parameters
    ----------
    data : Any
        JSON-serializable data.
    path : Path
        Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    class NpEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, (np.integer,)):
                return int(o)
            if isinstance(o, (np.floating,)):
                return float(o)
            if isinstance(o, (np.bool_,)):
                return bool(o)
            if isinstance(o, np.ndarray):
                return o.tolist()
            return super().default(o)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, cls=NpEncoder)
    log.info("Saved JSON: %s", path)


def load_json(path: Path) -> Any:
    """Load JSON file.

    Parameters
    ----------
    path : Path
        Source file path.

    Returns
    -------
    Any
        Deserialized data.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_regression_metrics(
    y_true: np.ndarray, y_pred: np.ndarray
) -> Dict[str, float]:
    """Compute regression metrics: RMSE, MAE, MAPE, R².

    Parameters
    ----------
    y_true : np.ndarray
        Ground truth values.
    y_pred : np.ndarray
        Predicted values.

    Returns
    -------
    Dict[str, float]
        Dictionary of metric_name -> value.
    """
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))

    # MAPE — handle zero actuals gracefully
    mask = y_true != 0
    if mask.sum() > 0:
        mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)
    else:
        mape = float("inf")

    return {
        "RMSE": round(rmse, 4),
        "MAE": round(mae, 4),
        "MAPE": round(mape, 4),
        "R2": round(r2, 4),
    }


def ensure_serializable(df: pd.DataFrame) -> pd.DataFrame:
    """Convert non-serializable dtypes (e.g. bool, categorical) to native types.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with safe dtypes for CSV/JSON export.
    """
    df = df.copy()
    for col in df.select_dtypes(include=["bool"]).columns:
        df[col] = df[col].astype(int)
    for col in df.select_dtypes(include=["category"]).columns:
        df[col] = df[col].astype(str)
    return df

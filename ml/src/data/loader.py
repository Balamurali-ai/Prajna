"""
Data loading module for the ET pipeline.

Loads the crime dataset from parquet or CSV, inspects metadata,
and returns a clean DataFrame ready for feature engineering.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional

from ml.configs.config import (
    CFG, DATASET_PARQUET, DATASET_CSV, FEATURE_DICT, RAW_DATA_DIR,
)
from ml.src.utils.logger import log


def load_dataset(use_parquet: bool = True) -> pd.DataFrame:
    """Load the crime dataset from parquet or CSV.

    Parameters
    ----------
    use_parquet : bool
        If True, load parquet (faster). Falls back to CSV if parquet fails.

    Returns
    -------
    pd.DataFrame
        Loaded dataset with all original columns.
    """
    if use_parquet and DATASET_PARQUET.exists():
        path = DATASET_PARQUET
        log.info("Loading dataset from parquet: %s", path)
        df = pd.read_parquet(path)
    elif DATASET_CSV.exists():
        path = DATASET_CSV
        log.info("Loading dataset from CSV: %s", path)
        df = pd.read_csv(path, low_memory=False)
    else:
        raise FileNotFoundError(
            f"Neither {DATASET_PARQUET} nor {DATASET_CSV} exists."
        )

    log.info("Loaded dataset: %s rows x %s cols", df.shape[0], df.shape[1])
    return df


def load_feature_dictionary() -> pd.DataFrame:
    """Load the feature dictionary CSV.

    Returns
    -------
    pd.DataFrame
        Feature dictionary with Column, Data_Source_Type, Description.
    """
    if not FEATURE_DICT.exists():
        log.warning("Feature dictionary not found at %s", FEATURE_DICT)
        return pd.DataFrame()
    fd = pd.read_csv(FEATURE_DICT)
    log.info("Loaded feature dictionary: %s entries", len(fd))
    return fd


def inspect_dataframe(df: pd.DataFrame) -> Dict:
    """Generate metadata summary for the dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    Dict
        Metadata dictionary: shape, dtypes, missing values, etc.
    """
    meta = {
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {c: str(dt) for c, dt in df.dtypes.items()},
        "missing_values": df.isna().sum().to_dict(),
        "missing_pct": (df.isna().sum() / len(df) * 100).round(2).to_dict(),
        "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
        "categorical_columns": list(df.select_dtypes(include=["object", "category"]).columns),
        "bool_columns": list(df.select_dtypes(include=["bool"]).columns),
    }
    log.info(
        "DataFrame: %s rows, %s cols, %s missing cells",
        meta["shape"][0],
        meta["shape"][1],
        sum(meta["missing_values"].values()),
    )
    return meta


def save_processed_data(df: pd.DataFrame, filename: str = "processed_dataset.parquet") -> Path:
    """Save processed DataFrame to the processed data directory.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save.
    filename : str
        Output filename.

    Returns
    -------
    Path
        Path to saved file.
    """
    path = CFG.ensure_dirs()
    out_path = RAW_DATA_DIR if "raw" in str(RAW_DATA_DIR) else PROCESSED_DATA_DIR / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    log.info("Saved processed data: %s (%s rows)", out_path, len(df))
    return out_path

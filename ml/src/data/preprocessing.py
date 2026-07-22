"""
Data preprocessing module.

Handles missing values, type conversions, date parsing,
and train/val/test temporal splitting.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
from sklearn.model_selection import TimeSeriesSplit

from ml.configs.config import CFG
from ml.src.utils.logger import log


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse Incident_Date column to datetime and extract temporal components.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with parsed Incident_Date and added temporal columns if missing.
    """
    df = df.copy()
    date_col = CFG.data.date_column

    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        # Fill missing temporal components from parsed date
        if CFG.data.year_column not in df.columns:
            df[CFG.data.year_column] = df[date_col].dt.year
        if CFG.data.month_column not in df.columns:
            df[CFG.data.month_column] = df[date_col].dt.month
        if CFG.data.quarter_column not in df.columns:
            df[CFG.data.quarter_column] = df[date_col].dt.quarter
        if CFG.data.week_column not in df.columns:
            df[CFG.data.week_column] = df[date_col].dt.isocalendar().week.astype(int)
    else:
        log.warning("Date column '%s' not found; skipping date parsing.", date_col)

    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values in the dataset.

    - Numeric columns: median fill
    - Categorical columns: mode fill
    - Boolean columns: False fill
    - Drop columns with >50% missing values

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame.
    """
    df = df.copy()
    n_total = len(df)

    # Drop columns with >50% missing
    high_missing = [c for c in df.columns if df[c].isna().sum() / n_total > 0.5]
    if high_missing:
        log.warning("Dropping columns with >50%% missing: %s", high_missing)
        df.drop(columns=high_missing, inplace=True)

    # Numeric columns — median fill
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if df[col].isna().sum() > 0:
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            log.debug("Filled %s missing values in %s with median=%.4f",
                       df[col].isna().sum(), col, median_val)

    # Categorical columns — mode fill
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    for col in cat_cols:
        if df[col].isna().sum() > 0:
            mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown"
            df[col].fillna(mode_val, inplace=True)
            log.debug("Filled missing %s with mode='%s'", col, mode_val)

    # Boolean columns — False fill
    bool_cols = df.select_dtypes(include=["bool"]).columns
    for col in bool_cols:
        df[col].fillna(False, inplace=True)

    total_missing = df.isna().sum().sum()
    log.info(
        "Missing value handling complete. Remaining missing cells: %s",
        total_missing,
    )
    return df


def filter_rows_without_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows without valid lat/lon for spatial operations.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.
    """
    lat_col = CFG.data.latitude_column
    lon_col = CFG.data.longitude_column
    before = len(df)
    df = df.dropna(subset=[lat_col, lon_col])
    df = df[(df[lat_col] != 0) & (df[lon_col] != 0)]
    after = len(df)
    if before - after > 0:
        log.info("Removed %s rows without valid coordinates", before - after)
    return df


def temporal_train_val_test_split(
    df: pd.DataFrame,
    year_col: str = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split DataFrame into train/val/test sets based on year.

    Uses strict temporal ordering — NO random shuffle, NO leakage.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame with Year column.
    year_col : str, optional
        Name of the year column.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        (train_df, val_df, test_df)
    """
    if year_col is None:
        year_col = CFG.data.year_column

    train_years = CFG.data.train_years
    val_years = CFG.data.val_years
    test_years = CFG.data.test_years

    train_df = df[df[year_col].isin(train_years)].copy()
    val_df = df[df[year_col].isin(val_years)].copy()
    test_df = df[df[year_col].isin(test_years)].copy()

    log.info(
        "Time split: Train %s (%s rows), Val %s (%s rows), Test %s (%s rows)",
        train_years, len(train_df), val_years, len(val_df), test_years, len(test_df),
    )
    return train_df, val_df, test_df


def aggregate_by_district_month(
    df: pd.DataFrame,
    include_spatial: bool = True,
) -> pd.DataFrame:
    """Aggregate crime data by District and Year/Month.

    This produces the unit of analysis for risk scoring and hotspot detection.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame with individual crime records.
    include_spatial : bool
        Whether to include spatial features (avg lat/lon).

    Returns
    -------
    pd.DataFrame
        Aggregated DataFrame with one row per district-month.
    """
    target = CFG.data.target_column
    district_col = CFG.data.district_column

    agg_dict = {
        target: "sum",
        "Sample_Weight": "sum",
    }

    if include_spatial:
        agg_dict[CFG.data.latitude_column] = "mean"
        agg_dict[CFG.data.longitude_column] = "mean"

    # Include risk-related columns if present
    for col in [
        "Risk_Index", "Crime_Rate_100k", "Is_Night", "Is_Weekend",
        "Is_Festival_Month", "Is_Office_Hour",
    ]:
        if col in df.columns and col not in agg_dict:
            agg_dict[col] = "mean"

    grouped = (
        df.groupby([district_col, CFG.data.state_column, CFG.data.year_column, CFG.data.month_column])
        .agg(agg_dict)
        .reset_index()
    )

    # Add quarter
    grouped[CFG.data.quarter_column] = ((grouped[CFG.data.month_column] - 1) // 3 + 1).astype(int)

    log.info(
        "Aggregated to district-month: %s rows (from %s)",
        len(grouped), len(df),
    )
    return grouped

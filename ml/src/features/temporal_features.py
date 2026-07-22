"""
Temporal feature engineering for crime time series.

Creates lag features, rolling statistics, EMA, seasonal features,
and growth/momentum indicators from district-month aggregated data.
"""

import pandas as pd
import numpy as np
from typing import List, Optional

from ml.configs.config import CFG
from ml.src.utils.logger import log


def create_lag_features(
    df: pd.DataFrame,
    target_col: str = None,
    group_cols: List[str] = None,
    max_lag: int = None,
) -> pd.DataFrame:
    """Create lagged target features for each district.

    Parameters
    ----------
    df : pd.DataFrame
        District-month aggregated DataFrame, sorted by district + year + month.
    target_col : str, optional
        Column to lag.
    group_cols : List[str], optional
        Columns to group by (e.g., District).
    max_lag : int, optional
        Maximum number of lags.

    Returns
    -------
    pd.DataFrame
        DataFrame with added lag columns.
    """
    df = df.copy()
    if target_col is None:
        target_col = CFG.data.target_column
    if group_cols is None:
        group_cols = [CFG.data.district_column]
    if max_lag is None:
        max_lag = CFG.features.max_lag_months

    df = df.sort_values(group_cols + [CFG.data.year_column, CFG.data.month_column])

    for lag in range(1, max_lag + 1):
        col_name = f"{target_col}_Lag_{lag}"
        df[col_name] = df.groupby(group_cols)[target_col].shift(lag)

    log.debug("Created %s lag features (max_lag=%s)", max_lag, max_lag)
    return df


def create_rolling_features(
    df: pd.DataFrame,
    target_col: str = None,
    group_cols: List[str] = None,
    windows: List[int] = None,
) -> pd.DataFrame:
    """Create rolling mean and standard deviation features.

    Parameters
    ----------
    df : pd.DataFrame
        District-month DataFrame, sorted per group.
    target_col : str, optional
        Column to compute rolling stats on.
    group_cols : List[str], optional
        Grouping columns.
    windows : List[int], optional
        Rolling window sizes.

    Returns
    -------
    pd.DataFrame
        DataFrame with rolling mean/std columns.
    """
    df = df.copy()
    if target_col is None:
        target_col = CFG.data.target_column
    if group_cols is None:
        group_cols = [CFG.data.district_column]
    if windows is None:
        windows = CFG.features.rolling_windows

    df = df.sort_values(group_cols + [CFG.data.year_column, CFG.data.month_column])

    for w in windows:
        rolling_mean = df.groupby(group_cols)[target_col].transform(
            lambda x: x.shift(1).rolling(window=w, min_periods=1).mean()
        )
        df[f"Rolling_Mean_{w}m"] = rolling_mean

        rolling_std = df.groupby(group_cols)[target_col].transform(
            lambda x: x.shift(1).rolling(window=w, min_periods=1).std()
        )
        df[f"Rolling_Std_{w}m"] = rolling_std.fillna(0)

    log.debug("Created rolling features for windows: %s", windows)
    return df


def create_ema_feature(
    df: pd.DataFrame,
    target_col: str = None,
    group_cols: List[str] = None,
    span: int = None,
) -> pd.DataFrame:
    """Create exponentially weighted moving average feature.

    Parameters
    ----------
    df : pd.DataFrame
        District-month DataFrame.
    target_col : str, optional
        Column for EMA calculation.
    group_cols : List[str], optional
        Grouping columns.
    span : int, optional
        EMA span parameter.

    Returns
    -------
    pd.DataFrame
        DataFrame with EMA column.
    """
    df = df.copy()
    if target_col is None:
        target_col = CFG.data.target_column
    if group_cols is None:
        group_cols = [CFG.data.district_column]
    if span is None:
        span = CFG.features.ema_span

    df = df.sort_values(group_cols + [CFG.data.year_column, CFG.data.month_column])

    def _ema(group):
        return group.shift(1).ewm(span=span, adjust=False).mean()

    df[f"EMA_{span}m"] = df.groupby(group_cols)[target_col].transform(_ema)

    log.debug("Created EMA feature with span=%s", span)
    return df


def create_seasonal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create seasonal / cyclical encoding features.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with Month and Quarter columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with sin/cos encoded seasonal features.
    """
    df = df.copy()

    if CFG.data.month_column in df.columns:
        df["Month_Sin"] = np.sin(2 * np.pi * df[CFG.data.month_column] / 12)
        df["Month_Cos"] = np.cos(2 * np.pi * df[CFG.data.month_column] / 12)

    if CFG.data.quarter_column in df.columns:
        df["Quarter_Sin"] = np.sin(2 * np.pi * df[CFG.data.quarter_column] / 4)
        df["Quarter_Cos"] = np.cos(2 * np.pi * df[CFG.data.quarter_column] / 4)

    log.debug("Created seasonal features (month sin/cos, quarter sin/cos)")
    return df


def create_growth_features(
    df: pd.DataFrame,
    target_col: str = None,
    group_cols: List[str] = None,
) -> pd.DataFrame:
    """Create growth rate, momentum, and acceleration features.

    Parameters
    ----------
    df : pd.DataFrame
        District-month DataFrame.
    target_col : str, optional
        Column for growth calculation.
    group_cols : List[str], optional
        Grouping columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with growth features.
    """
    df = df.copy()
    if target_col is None:
        target_col = CFG.data.target_column
    if group_cols is None:
        group_cols = [CFG.data.district_column]

    df = df.sort_values(group_cols + [CFG.data.year_column, CFG.data.month_column])

    # YoY growth (12-month lag)
    df["Crime_Growth"] = df.groupby(group_cols)[target_col].transform(
        lambda x: (x - x.shift(12)) / (x.shift(12) + 1)
    )
    df["Crime_Growth"] = df["Crime_Growth"].fillna(0)

    # Momentum: 3-month rolling growth
    df["Momentum"] = df.groupby(group_cols)["Crime_Growth"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )
    df["Momentum"] = df["Momentum"].fillna(0)

    # Acceleration: change in momentum
    df["Acceleration"] = df.groupby(group_cols)["Momentum"].transform(
        lambda x: x.diff()
    )
    df["Acceleration"] = df["Acceleration"].fillna(0)

    log.debug("Created growth features: Growth, Momentum, Acceleration")
    return df


def create_temporal_ratio_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create ratio features (weekend ratio, night ratio) if available.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with Is_Weekend, Is_Night, Is_Office_Hour boolean columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with additional ratio features.
    """
    df = df.copy()

    if "Is_Weekend" in df.columns:
        df["Weekend_Ratio"] = df["Is_Weekend"]
    else:
        df["Weekend_Ratio"] = 0.0

    if "Is_Night" in df.columns:
        df["Night_Crime_Ratio"] = df["Is_Night"]
    else:
        df["Night_Crime_Ratio"] = 0.0

    if "Is_Office_Hour" in df.columns:
        df["Office_Hour_Ratio"] = df["Is_Office_Hour"]
    else:
        df["Office_Hour_Ratio"] = 0.0

    log.debug("Created temporal ratio features")
    return df

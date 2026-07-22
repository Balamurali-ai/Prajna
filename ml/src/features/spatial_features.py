"""
Spatial feature engineering for crime data.

Creates H3 hexagon indices, neighborhood density features,
and spatial lag variables for hotspot detection and risk scoring.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple

from ml.configs.config import CFG
from ml.src.utils.logger import log


try:
    import h3
    HAS_H3 = True
except ImportError:
    HAS_H3 = False
    log.warning("h3 module not available. Install with: pip install h3")


def add_h3_index(
    df: pd.DataFrame,
    lat_col: str = None,
    lon_col: str = None,
    resolution: int = None,
) -> pd.DataFrame:
    """Add H3 hexagon index column for each coordinate pair.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with latitude and longitude columns.
    lat_col : str, optional
        Latitude column name.
    lon_col : str, optional
        Longitude column name.
    resolution : int, optional
        H3 resolution (higher = finer grid). Default 6.

    Returns
    -------
    pd.DataFrame
        DataFrame with added 'h3_index' column.
    """
    if not HAS_H3:
        log.warning("H3 not installed. Skipping h3_index creation.")
        df["h3_index"] = "NO_H3"
        return df

    df = df.copy()
    if lat_col is None:
        lat_col = CFG.data.latitude_column
    if lon_col is None:
        lon_col = CFG.data.longitude_column
    if resolution is None:
        resolution = CFG.features.h3_resolution

    df["h3_index"] = df.apply(
        lambda row: h3.latlng_to_cell(
            row[lat_col], row[lon_col], resolution
        )
        if pd.notna(row[lat_col]) and pd.notna(row[lon_col])
        else None,
        axis=1,
    )

    log.info("Added H3 index (res=%s): %s unique cells", resolution, df["h3_index"].nunique())
    return df


def compute_neighbor_crime_density(
    df: pd.DataFrame,
    district_col: str = None,
    target_col: str = None,
    year_col: str = None,
) -> pd.DataFrame:
    """Compute neighbor crime density using existing Neighbor_District_Risk column.

    If the dataset already contains Neighbor_District_Risk or Spatial_Lag,
    we use those directly. Otherwise create a simple proxy.

    Parameters
    ----------
    df : pd.DataFrame
        District-month DataFrame.
    district_col : str, optional
        District column name.
    target_col : str, optional
        Target column for aggregation.
    year_col : str, optional
        Year column.

    Returns
    -------
    pd.DataFrame
        DataFrame with neighbor density feature.
    """
    df = df.copy()
    if district_col is None:
        district_col = CFG.data.district_column
    if target_col is None:
        target_col = CFG.data.target_column
    if year_col is None:
        year_col = CFG.data.year_column

    if "Neighbor_District_Risk" in df.columns:
        df["Neighbor_Crime_Density"] = df["Neighbor_District_Risk"]
        log.info("Using existing Neighbor_District_Risk as neighbor density")
    elif "Spatial_Lag" in df.columns:
        df["Neighbor_Crime_Density"] = df["Spatial_Lag"]
        log.info("Using existing Spatial_Lag as neighbor density")
    else:
        log.warning("No spatial neighbor columns found; setting neighbor density to 0")
        df["Neighbor_Crime_Density"] = 0.0

    return df


def compute_population_normalized_crime(
    df: pd.DataFrame,
    target_col: str = None,
) -> pd.DataFrame:
    """Compute population-normalized crime rate.

    If Crime_Rate_100k already exists, use it. Otherwise compute from
    Population and Crime_Count_District.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with Population and Crime_Count_District columns.
    target_col : str, optional
        Crime count column.

    Returns
    -------
    pd.DataFrame
        DataFrame with Population_Normalized_Crime column.
    """
    df = df.copy()
    if target_col is None:
        target_col = CFG.data.target_column

    if "Crime_Rate_100k" in df.columns:
        df["Population_Normalized_Crime"] = df["Crime_Rate_100k"]
    elif "Population" in df.columns and target_col in df.columns:
        eps = 1e-6
        df["Population_Normalized_Crime"] = (
            df[target_col] / (df["Population"] + eps) * 100000
        )
    else:
        log.warning("Cannot compute population normalized crime; setting to 0")
        df["Population_Normalized_Crime"] = 0.0

    return df


def add_spatial_cluster_id(df: pd.DataFrame) -> pd.DataFrame:
    """Pass through or compute cluster ID for spatial grouping.

    If Cluster_ID already exists in the dataset, use it as-is.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with Cluster_ID column.
    """
    df = df.copy()
    if "Cluster_ID" not in df.columns:
        df["Cluster_ID"] = -1
    return df

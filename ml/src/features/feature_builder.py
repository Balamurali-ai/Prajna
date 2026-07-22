"""
Feature builder that orchestrates temporal and spatial feature engineering.

Combines all feature transformations into a single pipeline suitable
for both the risk model and hotspot model.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict

from ml.configs.config import CFG
from ml.src.utils.logger import log
from ml.src.features.temporal_features import (
    create_lag_features,
    create_rolling_features,
    create_ema_feature,
    create_seasonal_features,
    create_growth_features,
    create_temporal_ratio_features,
)
from ml.src.features.spatial_features import (
    add_h3_index,
    compute_neighbor_crime_density,
    compute_population_normalized_crime,
    add_spatial_cluster_id,
)
from ml.src.utils.helpers import ensure_serializable


def build_risk_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build all features for the risk scoring model.

    Operates on district-month aggregated data.

    Parameters
    ----------
    df : pd.DataFrame
        District-month DataFrame with at least District, Year, Month,
        Crime_Count_District columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with all risk model features.
    """
    log.info("Building risk model features...")
    df = df.copy()

    # Temporal features
    df = create_lag_features(df)
    df = create_rolling_features(df)
    df = create_ema_feature(df)
    df = create_seasonal_features(df)
    df = create_growth_features(df)
    df = create_temporal_ratio_features(df)

    # Spatial features
    df = compute_neighbor_crime_density(df)
    df = compute_population_normalized_crime(df)

    log.info("Risk feature building complete: %s columns", df.shape[1])
    return df


def build_hotspot_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build features for the hotspot detection model.

    Operates on individual crime records with lat/lon, adds H3 index,
    then aggregates to H3 cell-month level.

    Parameters
    ----------
    df : pd.DataFrame
        Individual crime records with Latitude, Longitude.

    Returns
    -------
    pd.DataFrame
        H3 cell-month aggregated DataFrame with lag/rolling features.
    """
    log.info("Building hotspot model features...")
    df = df.copy()

    # Add H3 index
    df = add_h3_index(df)

    # Aggregate to H3 cell-month
    h3_agg = (
        df.groupby(["h3_index", CFG.data.year_column, CFG.data.month_column])
        .agg(
            crime_count=(CFG.data.target_column, "sum"),
            latitude=(CFG.data.latitude_column, "mean"),
            longitude=(CFG.data.longitude_column, "mean"),
        )
        .reset_index()
    )

    log.info("H3 aggregated: %s cell-months", len(h3_agg))

    # Add temporal features per H3 cell
    h3_agg = create_lag_features(
        h3_agg, target_col="crime_count", group_cols=["h3_index"]
    )
    h3_agg = create_rolling_features(
        h3_agg, target_col="crime_count", group_cols=["h3_index"]
    )
    h3_agg = create_ema_feature(
        h3_agg, target_col="crime_count", group_cols=["h3_index"]
    )
    h3_agg = create_seasonal_features(h3_agg)
    h3_agg = create_growth_features(
        h3_agg, target_col="crime_count", group_cols=["h3_index"]
    )

    log.info("Hotspot feature building complete: %s columns", h3_agg.shape[1])
    return h3_agg


def get_feature_columns(df: pd.DataFrame, exclude_cols: List[str] = None) -> List[str]:
    """Identify feature columns for modelling, excluding identifiers and target.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with all potential features.
    exclude_cols : List[str], optional
        Additional columns to exclude.

    Returns
    -------
    List[str]
        List of feature column names.
    """
    default_exclude = [
        CFG.data.id_column,
        CFG.data.target_column,
        CFG.data.district_column,
        CFG.data.state_column,
        CFG.data.date_column,
        "Incident_ID",
        "Incident_Date",
        "h3_index",
        "Sample_Weight",
        "Official_Unit_Year_Total",
        "Data_Source",
        "Aggregate_Basis",
        "Coordinate_Type",
        "Police_Station_ID",
        "Administrative_Code",
        "Sub_Category",
        "Complaint_Channel",
        "Victim_Age_Group",
        "Victim_Gender",
        "Time_of_Day",
        "Day_of_Week",
        "Crime_Category",
    ]

    if exclude_cols:
        default_exclude.extend(exclude_cols)

    # Only numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    feature_cols = [c for c in numeric_cols if c not in default_exclude]

    # Remove columns with too many missing values
    feature_cols = [
        c for c in feature_cols if df[c].isna().sum() / len(df) < 0.5
    ]

    log.info("Selected %s feature columns for modelling", len(feature_cols))
    return feature_cols

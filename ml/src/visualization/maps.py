"""
Map-based visualizations for crime data.

Generates crime heat maps, hotspot maps, and neighbor density maps.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from ml.configs.config import CFG
from ml.src.utils.logger import log

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import seaborn as sns
    HAS_SNS = True
except ImportError:
    HAS_SNS = False


def crime_heatmap(
    df: pd.DataFrame,
    lat_col: str = None,
    lon_col: str = None,
    save_path: Path = None,
    title: str = "Crime Heat Map",
):
    """Generate a 2D histogram / heatmap of crime locations.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with latitude and longitude.
    lat_col : str, optional
        Latitude column.
    lon_col : str, optional
        Longitude column.
    save_path : Path, optional
        Path to save the figure.
    title : str
        Plot title.
    """
    if not HAS_MPL:
        log.warning("matplotlib not available.")
        return
    if lat_col is None:
        lat_col = CFG.data.latitude_column
    if lon_col is None:
        lon_col = CFG.data.longitude_column

    fig, ax = plt.subplots(figsize=(12, 10))
    heatmap, xedges, yedges = np.histogram2d(
        df[lat_col], df[lon_col], bins=80
    )
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    im = ax.imshow(heatmap.T, extent=extent, origin="lower",
                   cmap="hot", aspect="auto")
    plt.colorbar(im, ax=ax, label="Crime Density")
    ax.set_xlabel("Latitude")
    ax.set_ylabel("Longitude")
    ax.set_title(title)
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
        log.info("Saved crime heatmap: %s", save_path)
    plt.close()


def hotspot_map(
    hotspot_df: pd.DataFrame,
    background_df: pd.DataFrame = None,
    save_path: Path = None,
    title: str = "Crime Hotspots",
):
    """Plot hotspot locations on a scatter map.

    Parameters
    ----------
    hotspot_df : pd.DataFrame
        Hotspot rankings with latitude, longitude, Risk_Score.
    background_df : pd.DataFrame, optional
        Background crime points for context.
    save_path : Path, optional
        Path to save the figure.
    title : str
        Plot title.
    """
    if not HAS_MPL:
        return

    fig, ax = plt.subplots(figsize=(14, 10))

    if background_df is not None:
        ax.scatter(
            background_df[CFG.data.longitude_column],
            background_df[CFG.data.latitude_column],
            s=1, alpha=0.3, c="gray", label="All Crimes",
        )

    if "Risk_Score" in hotspot_df.columns:
        scatter = ax.scatter(
            hotspot_df["longitude"] if "longitude" in hotspot_df.columns else hotspot_df.get(CFG.data.longitude_column, 0),
            hotspot_df["latitude"] if "latitude" in hotspot_df.columns else hotspot_df.get(CFG.data.latitude_column, 0),
            s=hotspot_df["Risk_Score"] * 5,
            c=hotspot_df["Risk_Score"],
            cmap="Reds",
            alpha=0.7,
            edgecolors="black",
            linewidth=0.5,
        )
        plt.colorbar(scatter, ax=ax, label="Risk Score")
    else:
        ax.scatter(
            hotspot_df.get(CFG.data.longitude_column, 0),
            hotspot_df.get(CFG.data.latitude_column, 0),
            s=50, c="red", alpha=0.7, label="Hotspots",
        )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(title)
    ax.legend()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
        log.info("Saved hotspot map: %s", save_path)
    plt.close()


def neighbor_density_map(
    df: pd.DataFrame,
    save_path: Path = None,
):
    """Plot neighbor density influence.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with Neighbor_District_Risk or similar.
    save_path : Path, optional
        Path to save the figure.
    """
    if not HAS_MPL:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    col = None
    for c in ["Neighbor_District_Risk", "Spatial_Lag", "Neighbor_Crime_Density"]:
        if c in df.columns:
            col = c
            break
    if col is None:
        ax.text(0.5, 0.5, "No neighbor data available", ha="center", va="center")
    else:
        ax.scatter(
            df[CFG.data.target_column], df[col],
            alpha=0.5, s=10, c="steelblue",
        )
        ax.set_xlabel("Crime Count")
        ax.set_ylabel(col)
        ax.set_title(f"Neighbor Influence: {col} vs Crime Count")
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
    plt.close()

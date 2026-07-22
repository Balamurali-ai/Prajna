"""
Chart-based visualizations for model evaluation and analysis.

Generates risk distribution, feature importance, monthly trend,
prediction vs actual, residual, and top-20 risk area plots.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List

from ml.configs.config import (
    CFG, RISK_DISTRIBUTION_PLOT, FEATURE_IMPORTANCE_PLOT,
    MONTHLY_TREND_PLOT, PRED_VS_ACTUAL_PLOT, RESIDUAL_PLOT,
    TOP20_RISK_PLOT, CRIME_HEATMAP, HOTSPOT_MAP, NEIGHBOR_DENSITY_PLOT,
)
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


def risk_distribution_plot(
    risk_scores: pd.Series,
    save_path: Path = None,
    title: str = "Risk Score Distribution",
):
    """Plot distribution of risk scores.

    Parameters
    ----------
    risk_scores : pd.Series
        Risk score values (0–100).
    save_path : Path, optional
        Path to save the figure.
    title : str
        Plot title.
    """
    if not HAS_MPL:
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(risk_scores, bins=50, color="steelblue", edgecolor="black", alpha=0.7)
    ax.axvline(risk_scores.mean(), color="red", linestyle="--",
               label=f"Mean: {risk_scores.mean():.2f}")
    ax.set_xlabel("Risk Score")
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    ax.legend()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
    plt.close()


def feature_importance_plot(
    importance_df: pd.DataFrame,
    top_n: int = 20,
    save_path: Path = None,
    title: str = "Feature Importance (Gain)",
):
    """Plot top N features by importance.

    Parameters
    ----------
    importance_df : pd.DataFrame
        DataFrame with 'feature' and 'importance_pct' columns.
    top_n : int
        Number of top features to show.
    save_path : Path, optional
        Path to save the figure.
    title : str
        Plot title.
    """
    if not HAS_MPL:
        return
    top = importance_df.head(top_n).sort_values("importance_pct")
    fig, ax = plt.subplots(figsize=(12, max(6, top_n * 0.4)))
    ax.barh(range(len(top)), top["importance_pct"].values, color="coral", edgecolor="black")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["feature"].values)
    ax.set_xlabel("Importance (%)")
    ax.set_title(title)
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
    plt.close()


def monthly_trend_plot(
    df: pd.DataFrame,
    save_path: Path = None,
):
    """Plot monthly crime trend across years.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with Year, Month, Crime_Count_District.
    save_path : Path, optional
        Path to save the figure.
    """
    if not HAS_MPL:
        return
    target = CFG.data.target_column
    trend = df.groupby([CFG.data.year_column, CFG.data.month_column])[target].mean().reset_index()
    trend["date"] = pd.to_datetime(
        trend[CFG.data.year_column].astype(str) + "-" + trend[CFG.data.month_column].astype(str) + "-01"
    )
    trend = trend.sort_values("date")

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(trend["date"], trend[target], marker="o", linestyle="-", color="steelblue")
    ax.set_xlabel("Date")
    ax.set_ylabel(f"Avg {target}")
    ax.set_title("Monthly Crime Trend")
    ax.tick_params(axis="x", rotation=45)
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
    plt.close()


def pred_vs_actual_plot(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    save_path: Path = None,
    title: str = "Prediction vs Actual",
):
    """Scatter plot of predicted vs actual values.

    Parameters
    ----------
    y_true : np.ndarray
        Ground truth.
    y_pred : np.ndarray
        Predictions.
    save_path : Path, optional
        Path to save the figure.
    title : str
        Plot title.
    """
    if not HAS_MPL:
        return
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y_true, y_pred, alpha=0.5, s=10, c="steelblue")
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax.plot([min_val, max_val], [min_val, max_val], "r--", label="Perfect Prediction")
    ax.set_xlabel("Actual")
    ax.set_ylabel("Predicted")
    ax.set_title(title)
    ax.legend()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
    plt.close()


def residual_plot(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    save_path: Path = None,
):
    """Plot residuals (errors) vs predicted values.

    Parameters
    ----------
    y_true : np.ndarray
        Ground truth.
    y_pred : np.ndarray
        Predictions.
    save_path : Path, optional
        Path to save the figure.
    """
    if not HAS_MPL:
        return
    residuals = y_true - y_pred
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(y_pred, residuals, alpha=0.5, s=10, c="steelblue")
    ax.axhline(y=0, color="red", linestyle="--", linewidth=1)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Residual (Actual - Predicted)")
    ax.set_title("Residual Plot")
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
    plt.close()


def top20_risk_areas_plot(
    risk_df: pd.DataFrame,
    district_col: str = "District",
    score_col: str = "Risk_Score",
    save_path: Path = None,
):
    """Plot top 20 risk areas by district.

    Parameters
    ----------
    risk_df : pd.DataFrame
        DataFrame with district and risk score columns.
    district_col : str
        District column name.
    score_col : str
        Risk score column name.
    save_path : Path, optional
        Path to save the figure.
    """
    if not HAS_MPL:
        return
    top = (risk_df.groupby(district_col)[score_col].mean()
           .sort_values(ascending=False).head(20))
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(range(len(top)), top.values, color="tomato", edgecolor="black")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top.index)
    ax.set_xlabel(f"Mean {score_col}")
    ax.set_title(f"Top 20 {district_col}s by {score_col}")
    ax.invert_yaxis()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
    plt.close()


def generate_all_plots(
    df: pd.DataFrame,
    risk_scores: pd.Series = None,
    feature_importance: pd.DataFrame = None,
    y_true: np.ndarray = None,
    y_pred: np.ndarray = None,
    risk_predictions: pd.DataFrame = None,
):
    """Generate all standard visualization plots.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    risk_scores : pd.Series, optional
        Risk scores.
    feature_importance : pd.DataFrame, optional
        Feature importance.
    y_true : np.ndarray, optional
        Ground truth for pred vs actual.
    y_pred : np.ndarray, optional
        Predictions.
    risk_predictions : pd.DataFrame, optional
        Risk predictions with District and Risk_Score.
    """
    log.info("Generating all visualizations...")

    if risk_scores is not None:
        risk_distribution_plot(risk_scores, RISK_DISTRIBUTION_PLOT)

    if feature_importance is not None:
        feature_importance_plot(feature_importance, save_path=FEATURE_IMPORTANCE_PLOT)

    monthly_trend_plot(df, MONTHLY_TREND_PLOT)

    if y_true is not None and y_pred is not None:
        pred_vs_actual_plot(y_true, y_pred, PRED_VS_ACTUAL_PLOT)
        residual_plot(y_true, y_pred, RESIDUAL_PLOT)

    if risk_predictions is not None:
        top20_risk_areas_plot(risk_predictions, save_path=TOP20_RISK_PLOT)

    log.info("All visualizations generated.")

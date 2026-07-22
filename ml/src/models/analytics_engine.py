"""
Analytics Engine — Model 8.

Generates automatic analytical insights from crime data and model predictions:
top risk districts, crime trends, growth rates, seasonality, moving averages,
category distribution, station load, risk rankings, neighbor influence.

Outputs: analytics_report.json, analytics_summary.csv, dashboard_metrics.json
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from ml.configs.config import (
    CFG, ANALYTICS_REPORT_PATH, DASHBOARD_METRICS_PATH,
    ANALYTICS_SUMMARY_PATH, OUTPUTS_DIR,
)
from ml.src.utils.logger import log
from ml.src.utils.helpers import save_json


class AnalyticsEngine:
    """Generates dashboard-ready analytics from crime data and predictions.

    Operates on both original data and model outputs to produce
    structured analytical reports.
    """

    def __init__(self):
        self.report: Dict = {}
        self.dashboard_metrics: Dict = {}

    def compute_all(
        self,
        df: pd.DataFrame,
        risk_predictions: pd.DataFrame = None,
        hotspot_rankings: pd.DataFrame = None,
    ) -> Dict:
        """Compute all analytics: trends, distributions, rankings, etc.

        Parameters
        ----------
        df : pd.DataFrame
            Original crime dataset or aggregated data.
        risk_predictions : pd.DataFrame, optional
            Risk model predictions with District, Risk_Score, etc.
        hotspot_rankings : pd.DataFrame, optional
            Hotspot rankings with h3_index, Risk_Score, etc.

        Returns
        -------
        Dict
            Complete analytics report.
        """
        log.info("Computing full analytics engine...")
        self.report = {}

        self.report["top_risk_districts"] = self._top_risk_districts(df, risk_predictions)
        self.report["crime_trends"] = self._crime_trends(df)
        self.report["growth_rates"] = self._growth_rates(df)
        self.report["monthly_trends"] = self._monthly_trends(df)
        self.report["seasonality"] = self._seasonality(df)
        self.report["moving_averages"] = self._moving_averages(df)
        self.report["rolling_growth"] = self._rolling_growth(df)
        self.report["crime_category_distribution"] = self._crime_category_distribution(df)
        self.report["station_load"] = self._station_load(df)
        self.report["risk_rankings"] = self._risk_rankings(df, risk_predictions)
        self.report["hotspot_trends"] = self._hotspot_trends(hotspot_rankings)
        self.report["neighbor_influence"] = self._neighbor_influence(df)

        # Build dashboard metrics
        self.dashboard_metrics = self._build_dashboard_metrics(df, risk_predictions, hotspot_rankings)

        log.info("Analytics complete: %s report sections", len(self.report))
        return self.report

    def _top_risk_districts(
        self, df: pd.DataFrame, risk_pred: pd.DataFrame = None,
    ) -> List[Dict]:
        """Identify top risk districts from predictions or Risk_Index.

        Parameters
        ----------
        df : pd.DataFrame
            Input data.
        risk_pred : pd.DataFrame, optional
            Risk model predictions.

        Returns
        -------
        List[Dict]
            Top districts ranked by risk.
        """
        if risk_pred is not None and "Risk_Score" in risk_pred.columns:
            top = (
                risk_pred.groupby("District")["Risk_Score"]
                .mean()
                .sort_values(ascending=False)
                .head(20)
            )
        elif "Risk_Index" in df.columns:
            top = (
                df.groupby(CFG.data.district_column)["Risk_Index"]
                .mean()
                .sort_values(ascending=False)
                .head(20)
            )
        else:
            target = CFG.data.target_column
            top = (
                df.groupby(CFG.data.district_column)[target]
                .mean()
                .sort_values(ascending=False)
                .head(20)
            )
        return [
            {"district": d, "risk_score": round(float(s), 4)}
            for d, s in top.items()
        ]

    def _crime_trends(self, df: pd.DataFrame) -> Dict:
        """Compute overall crime trend direction per district.

        Returns
        -------
        Dict
            Trend analysis with direction, magnitude.
        """
        target = CFG.data.target_column
        results = {}
        if target not in df.columns:
            return {"error": "target column not found"}

        for district in df[CFG.data.district_column].unique():
            ddf = df[df[CFG.data.district_column] == district].sort_values(
                [CFG.data.year_column, CFG.data.month_column]
            )
            if len(ddf) < 2:
                continue
            recent = ddf[target].tail(3).mean()
            earlier = ddf[target].head(3).mean()
            change = ((recent - earlier) / (earlier + 1)) * 100
            results[district] = {
                "recent_avg": round(float(recent), 2),
                "earlier_avg": round(float(earlier), 2),
                "change_pct": round(float(change), 2),
                "direction": "increasing" if change > 5 else ("decreasing" if change < -5 else "stable"),
            }
        return results

    def _growth_rates(self, df: pd.DataFrame) -> Dict:
        """Report growth rate statistics per year.

        Returns
        -------
        Dict
            Yearly growth stats.
        """
        if "Growth_Rate" not in df.columns:
            return {"error": "Growth_Rate column not found"}
        return (
            df.groupby(CFG.data.year_column)["Growth_Rate"]
            .agg(["mean", "std", "min", "max"])
            .round(4)
            .to_dict()
        )

    def _monthly_trends(self, df: pd.DataFrame) -> Dict:
        """Compute average crime count per month across years.

        Returns
        -------
        Dict
            Monthly averages.
        """
        target = CFG.data.target_column
        if target not in df.columns:
            return {}
        monthly = df.groupby(CFG.data.month_column)[target].mean()
        return {
            int(m): round(float(v), 2) for m, v in monthly.items()
        }

    def _seasonality(self, df: pd.DataFrame) -> Dict:
        """Detect seasonal patterns by quarter.

        Returns
        -------
        Dict
            Quarterly averages and peak quarter.
        """
        target = CFG.data.target_column
        if target not in df.columns:
            return {}
        quarterly = df.groupby(CFG.data.quarter_column)[target].mean()
        result = {
            int(q): round(float(v), 2) for q, v in quarterly.items()
        }
        peak_q = quarterly.idxmax() if len(quarterly) > 0 else None
        result["peak_quarter"] = int(peak_q) if peak_q else None
        return result

    def _moving_averages(self, df: pd.DataFrame) -> Dict:
        """Compute 3-month and 6-month moving averages.

        Returns
        -------
        Dict
            Moving average summary.
        """
        target = CFG.data.target_column
        cols = {}
        for w in [3, 6]:
            col_name = f"Rolling_Mean_{w}m"
            if col_name in df.columns:
                cols[col_name] = {
                    "mean": round(float(df[col_name].mean()), 2),
                    "latest": round(float(df[col_name].dropna().iloc[-1]), 2) if len(df) > 0 else None,
                }
        return cols

    def _rolling_growth(self, df: pd.DataFrame) -> Dict:
        """Report rolling growth indicators.

        Returns
        -------
        Dict
            Rolling growth summary.
        """
        result = {}
        for col in ["Crime_Growth", "Momentum", "Acceleration"]:
            if col in df.columns:
                result[col] = {
                    "mean": round(float(df[col].mean()), 4),
                    "std": round(float(df[col].std()), 4),
                    "latest": round(float(df[col].dropna().iloc[-1]), 4) if len(df) > 0 else None,
                }
        return result

    def _crime_category_distribution(self, df: pd.DataFrame) -> Dict:
        """Compute crime category distribution.

        Returns
        -------
        Dict
            Category counts and percentages.
        """
        if "Crime_Category" not in df.columns:
            return {}
        counts = df["Crime_Category"].value_counts()
        total = counts.sum()
        return {
            str(cat): {
                "count": int(cnt),
                "pct": round(float(cnt / total * 100), 2),
            }
            for cat, cnt in counts.items()
        }

    def _station_load(self, df: pd.DataFrame) -> Dict:
        """Compute police station load statistics.

        Returns
        -------
        Dict
            Station load summary.
        """
        if "Police_Station_ID" not in df.columns:
            return {"note": "Police_Station_ID not available"}
        target = CFG.data.target_column
        station_counts = df.groupby("Police_Station_ID")[target].sum() if target in df.columns else df.groupby("Police_Station_ID").size()
        return {
            "total_stations": int(station_counts.count()),
            "mean_load": round(float(station_counts.mean()), 2),
            "max_load": round(float(station_counts.max()), 2),
            "min_load": round(float(station_counts.min()), 2),
        }

    def _risk_rankings(self, df: pd.DataFrame, risk_pred: pd.DataFrame = None) -> List[Dict]:
        """Rank districts by risk score.

        Parameters
        ----------
        df : pd.DataFrame
            Input data.
        risk_pred : pd.DataFrame, optional
            Risk predictions.

        Returns
        -------
        List[Dict]
            Full risk ranking.
        """
        if risk_pred is not None and "Risk_Score" in risk_pred.columns:
            ranking = (
                risk_pred.groupby("District")["Risk_Score"]
                .mean()
                .sort_values(ascending=False)
            )
        elif "Risk_Index" in df.columns:
            ranking = (
                df.groupby(CFG.data.district_column)["Risk_Index"]
                .mean()
                .sort_values(ascending=False)
            )
        else:
            return []
        return [
            {"rank": i + 1, "district": d, "score": round(float(s), 4)}
            for i, (d, s) in enumerate(ranking.items())
        ]

    def _hotspot_trends(self, hotspot_df: pd.DataFrame = None) -> Dict:
        """Analyze hotspot trends.

        Parameters
        ----------
        hotspot_df : pd.DataFrame, optional
            Hotspot rankings.

        Returns
        -------
        Dict
            Hotspot summary.
        """
        if hotspot_df is None or len(hotspot_df) == 0:
            return {"note": "No hotspot data available"}
        result = {
            "total_hotspots": len(hotspot_df),
            "mean_risk_score": round(float(hotspot_df["Risk_Score"].mean()), 2),
            "max_risk_score": round(float(hotspot_df["Risk_Score"].max()), 2),
            "top_hotspot": str(hotspot_df.iloc[0].get("h3_index", "N/A")),
        }
        return result

    def _neighbor_influence(self, df: pd.DataFrame) -> Dict:
        """Analyze neighbor influence on district crime.

        Returns
        -------
        Dict
            Neighbor influence analysis.
        """
        result = {}
        for col in ["Neighbor_District_Risk", "Spatial_Lag", "Neighbor_Crime_Density"]:
            if col in df.columns:
                corr = df[[CFG.data.target_column, col]].corr().iloc[0, 1]
                result[col] = {
                    "correlation_with_crime": round(float(corr), 4),
                    "mean": round(float(df[col].mean()), 4),
                }
        return result

    def _build_dashboard_metrics(
        self, df: pd.DataFrame, risk_pred: pd.DataFrame = None, hotspot_df: pd.DataFrame = None,
    ) -> Dict:
        """Build concise dashboard metrics for real-time display.

        Parameters
        ----------
        df : pd.DataFrame
            Input data.
        risk_pred : pd.DataFrame, optional
            Risk predictions.
        hotspot_df : pd.DataFrame, optional
            Hotspot rankings.

        Returns
        -------
        Dict
            Dashboard-ready metrics.
        """
        metrics = {}

        # Total crime
        target = CFG.data.target_column
        if target in df.columns:
            metrics["total_crime_count"] = int(df[target].sum())
            metrics["avg_monthly_crime"] = round(float(df[target].mean()), 2)

        # Districts
        metrics["total_districts"] = int(df[CFG.data.district_column].nunique())

        # Years
        if CFG.data.year_column in df.columns:
            metrics["years_covered"] = sorted(df[CFG.data.year_column].unique().tolist())

        # Top risk
        if risk_pred is not None and len(risk_pred) > 0 and "Risk_Score" in risk_pred.columns:
            metrics["top_risk_district"] = str(
                risk_pred.loc[risk_pred["Risk_Score"].idxmax(), "District"]
            )
            metrics["top_risk_score"] = round(float(risk_pred["Risk_Score"].max()), 2)

        # Hotspots
        if hotspot_df is not None and len(hotspot_df) > 0:
            metrics["hotspot_count"] = len(hotspot_df)
            if "Risk_Score" in hotspot_df.columns:
                metrics["avg_hotspot_risk"] = round(float(hotspot_df["Risk_Score"].mean()), 2)

        # Crime categories
        if "Crime_Category" in df.columns:
            metrics["crime_categories"] = int(df["Crime_Category"].nunique())
            top_cat = df["Crime_Category"].value_counts().index[0]
            metrics["top_category"] = str(top_cat)

        return metrics

    def save_reports(self) -> None:
        """Save analytics report and dashboard metrics to JSON files."""
        save_json(self.report, ANALYTICS_REPORT_PATH)
        save_json(self.dashboard_metrics, DASHBOARD_METRICS_PATH)

        # Also save a flat CSV summary
        if self.report:
            rows = []
            for section, data in self.report.items():
                if isinstance(data, list):
                    for item in data[:5]:  # top 5 per section
                        if isinstance(item, dict):
                            item["section"] = section
                            rows.append(item)
                elif isinstance(data, dict):
                    flat = {"section": section}
                    for k, v in list(data.items())[:10]:
                        flat[k] = str(v)[:100]
                    rows.append(flat)
            if rows:
                summary_df = pd.DataFrame(rows)
                summary_df.to_csv(ANALYTICS_SUMMARY_PATH, index=False)
                log.info("Saved analytics summary: %s", ANALYTICS_SUMMARY_PATH)

        log.info("Analytics reports saved to %s", OUTPUTS_DIR)

"""
SHAP Analysis — Model 6.

Global and local model explainability using SHAP values.
Generates waterfall, summary, and dependence plots.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ml.configs.config import (
    CFG, SHAP_DIR, FEATURE_IMPORTANCE_PATH, SHAP_VALUES_PATH,
    EXPLANATION_JSON_PATH, SHAP_SUMMARY_PLOT, FIGURES_DIR,
)
from ml.src.utils.logger import log
from ml.src.utils.helpers import save_json

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    log.warning("shap not installed. Install with: pip install shap")


class ShapAnalyzer:
    """SHAP-based model explainability.

    Computes global and local SHAP values, generates plots,
    and exports feature importance, explanations, and value files.
    """

    def __init__(self, model, X_background: pd.DataFrame, feature_names: List[str]):
        """Initialize with a fitted model and background data.

        Parameters
        ----------
        model : Any
            Fitted model with .predict() method.
        X_background : pd.DataFrame
            Background dataset for SHAP explainer.
        feature_names : List[str]
            Feature column names.
        """
        self.model = model
        self.feature_names = feature_names
        self.X_background = X_background
        self.explainer = None
        self.shap_values = None

    def fit(self) -> "ShapAnalyzer":
        """Create SHAP explainer and compute SHAP values on background.

        Uses TreeExplainer for tree-based models (LightGBM, XGBoost, etc.).

        Returns
        -------
        ShapAnalyzer
            Self with fitted explainer.
        """
        if not HAS_SHAP:
            log.warning("SHAP not available. Skipping.")
            return self

        log.info("Fitting SHAP TreeExplainer...")
        self.explainer = shap.TreeExplainer(
            self.model,
            feature_perturbation="interventional",
            data=self.X_background.values,
        )

        # Compute SHAP values on background
        self.shap_values = self.explainer.shap_values(self.X_background)
        log.info("SHAP values computed: shape %s", self.shap_values.shape)
        return self

    def compute_shap_values(self, X: pd.DataFrame) -> np.ndarray:
        """Compute SHAP values for a specific dataset.

        Parameters
        ----------
        X : pd.DataFrame
            Dataset to explain.

        Returns
        -------
        np.ndarray
            SHAP values array.
        """
        if not HAS_SHAP or self.explainer is None:
            return np.zeros((len(X), len(self.feature_names)))
        return self.explainer.shap_values(X)

    def global_importance(self) -> pd.DataFrame:
        """Compute global feature importance from mean absolute SHAP values.

        Returns
        -------
        pd.DataFrame
            Global feature importance sorted by magnitude.
        """
        if self.shap_values is None:
            return pd.DataFrame({"feature": self.feature_names, "importance": 0.0})

        mean_abs = np.abs(self.shap_values).mean(axis=0)
        fi = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": mean_abs,
        })
        fi = fi.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
        fi["importance_pct"] = (
            fi["mean_abs_shap"] / fi["mean_abs_shap"].sum() * 100
        ).round(2)
        return fi

    def local_explanation(self, X_row: pd.DataFrame, row_idx: int = 0) -> Dict:
        """Create local explanation for a single prediction.

        Parameters
        ----------
        X_row : pd.DataFrame
            Single row or small DataFrame to explain.
        row_idx : int
            Index of the row to explain.

        Returns
        -------
        Dict
            Local explanation with top positive/negative features.
        """
        if self.shap_values is None or not HAS_SHAP:
            return {"error": "SHAP not available"}

        sv = self.shap_values[row_idx]
        feat_vals = self.X_background.iloc[row_idx][self.feature_names].values

        pos_idx = np.argsort(sv)[::-1]
        neg_idx = np.argsort(sv)

        top_positive = [
            {"feature": self.feature_names[i], "shap_value": round(float(sv[i]), 4),
             "feature_value": round(float(feat_vals[i]), 4)}
            for i in pos_idx[:5] if sv[i] > 0
        ]
        top_negative = [
            {"feature": self.feature_names[i], "shap_value": round(float(sv[i]), 4),
             "feature_value": round(float(feat_vals[i]), 4)}
            for i in neg_idx[:5] if sv[i] < 0
        ]

        return {
            "row_index": int(row_idx),
            "top_positive_features": top_positive,
            "top_negative_features": top_negative,
            "base_value": round(float(self.explainer.expected_value), 4) if self.explainer is not None else 0.0,
        }

    def summary_plot(self, save_path: Path = None):
        """Generate SHAP summary plot (beeswarm).

        Parameters
        ----------
        save_path : Path, optional
            Path to save the figure.
        """
        if not HAS_SHAP or self.shap_values is None:
            log.warning("SHAP not available for summary plot.")
            return

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        shap.summary_plot(
            self.shap_values,
            self.X_background[self.feature_names],
            feature_names=self.feature_names,
            show=False,
            max_display=CFG.shap.max_display_features,
        )
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
            log.info("Saved SHAP summary plot: %s", save_path)
        plt.close()

    def waterfall_plot(self, row_idx: int = 0, save_path: Path = None):
        """Generate SHAP waterfall plot for a single prediction.

        Parameters
        ----------
        row_idx : int
            Index of the row to explain.
        save_path : Path, optional
            Path to save the figure.
        """
        if not HAS_SHAP or self.explainer is None:
            return
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        sv = self.shap_values[row_idx]
        expected = self.explainer.expected_value
        row_data = self.X_background.iloc[row_idx: row_idx + 1][self.feature_names]

        shap.waterfall_plot(
            expected,
            sv,
            features=row_data.values[0],
            feature_names=self.feature_names,
            max_display=CFG.shap.max_display_features,
            show=False,
        )
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
        plt.close()

    def dependence_plot(self, feature: str, save_path: Path = None):
        """Generate SHAP dependence plot for a specific feature.

        Parameters
        ----------
        feature : str
            Feature name to plot.
        save_path : Path, optional
            Path to save the figure.
        """
        if not HAS_SHAP or self.shap_values is None:
            return
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        shap.dependence_plot(
            feature,
            self.shap_values,
            self.X_background[self.feature_names],
            show=False,
        )
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
        plt.close()

    def export(self, output_dir: Path = None) -> Dict:
        """Export all SHAP outputs: importance CSV, values parquet, explanation JSON.

        Parameters
        ----------
        output_dir : Path, optional
            Output directory.

        Returns
        -------
        Dict
            Paths to exported files.
        """
        if output_dir is None:
            output_dir = SHAP_DIR

        output_dir.mkdir(parents=True, exist_ok=True)

        # Feature importance
        fi = self.global_importance()
        fi_path = FEATURE_IMPORTANCE_PATH
        fi.to_csv(fi_path, index=False)
        log.info("Saved feature importance: %s", fi_path)

        # SHAP values as parquet
        if self.shap_values is not None:
            sv_df = pd.DataFrame(
                self.shap_values, columns=self.feature_names
            )
            sv_df.to_parquet(SHAP_VALUES_PATH, index=False)
            log.info("Saved SHAP values: %s", SHAP_VALUES_PATH)

        # Explanation JSON
        explanation = {
            "method": "TreeExplainer",
            "feature_count": len(self.feature_names),
            "background_samples": len(self.X_background),
            "global_importance": fi.to_dict(orient="records"),
            "sample_local_explanation": self.local_explanation(self.X_background, row_idx=0),
        }
        save_json(explanation, EXPLANATION_JSON_PATH)

        # Generate plots
        self.summary_plot(SHAP_SUMMARY_PLOT)

        return {
            "feature_importance": str(fi_path),
            "shap_values": str(SHAP_VALUES_PATH),
            "explanation": str(EXPLANATION_JSON_PATH),
            "summary_plot": str(SHAP_SUMMARY_PLOT),
        }

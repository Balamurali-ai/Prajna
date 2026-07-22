# Geospatial Crime Pattern Intelligence

**ET AI Hackathon 2026 — Production-Grade ML Pipeline**

A complete, production-quality ML pipeline for crime pattern analysis using
the ET crime dataset. Four integrated modules:

1. **Risk Scoring** (Model 1) — District-level crime risk scores (0–100)
2. **Hotspot Detection** (Model 2) — H3 hexagon-based crime prediction
3. **Explainability** (Model 6) — SHAP-based global/local explanations
4. **Analytics Engine** (Model 8) — Automated dashboard-ready insights

---

## Quick Start

```bash
cd project/
pip install -r requirements.txt
python train.py
python predict.py
```

## Project Structure

```
project/
├── configs/
│   └── config.py              # All hyperparameters & paths
├── data/                      # Dataset (linked from parent)
├── models/
│   ├── risk/risk_model.pkl    # Trained risk model
│   └── hotspot/hotspot_model.pkl  # Trained hotspot model
├── outputs/
│   ├── predictions/
│   │   ├── predictions.csv    # Risk predictions
│   │   ├── hotspot_rankings.csv
│   │   └── hotspots.geojson
│   ├── reports/
│   ├── shap/
│   │   ├── shap_values.parquet
│   │   └── explanation.json
│   └── figures/               # All visualizations
├── src/
│   ├── data/
│   │   ├── loader.py          # Dataset loading
│   │   └── preprocessing.py   # Cleaning, missing values, splits
│   ├── features/
│   │   ├── temporal_features.py  # Lag, rolling, EMA, seasonal
│   │   ├── spatial_features.py   # H3, neighbor density
│   │   └── feature_builder.py    # Feature orchestration
│   ├── models/
│   │   ├── risk_model.py      # LightGBM risk regressor
│   │   ├── hotspot_model.py   # H3 + LightGBM hotspot detector
│   │   └── analytics_engine.py   # Automated analytics
│   ├── explainability/
│   │   └── shap_analysis.py   # SHAP values & plots
│   ├── evaluation/
│   │   └── evaluate.py        # TimeSeriesSplit CV & metrics
│   ├── visualization/
│   │   ├── charts.py          # Risk, importance, trend plots
│   │   └── maps.py            # Heat maps & hotspot maps
│   ├── utils/
│   │   ├── logger.py          # Logging configuration
│   │   └── helpers.py         # Serialization, metrics, utilities
│   └── pipeline.py            # Pipeline orchestrator
├── train.py                   # Train entry point
├── predict.py                 # Predict entry point
├── requirements.txt
└── README.md
```

## Modules

### Model 1 — Risk Scoring
- LightGBM Regressor predicting `Crime_Count_District`
- Features: historical counts, rolling mean/std, EMA, seasonal encoding,
  growth/momentum/acceleration, weekend/night ratios, neighbor density
- Outputs: Risk Score (0–100), Priority Rank, Confidence

### Model 2 — Hotspot Detection
- H3 spatial indexing (configurable resolution)
- LightGBM predicts crime count per H3 cell per month
- Hotspots determined by ranking predictions (no classifier)
- Outputs: CSV rankings + GeoJSON for mapping

### Model 6 — Explainability
- SHAP TreeExplainer
- Global importance, local explanations
- Waterfall, summary, dependence plots
- Exports: `feature_importance.csv`, `shap_values.parquet`, `explanation.json`

### Model 8 — Analytics Engine
- Top risk districts, crime trends, growth rates
- Monthly/seasonal patterns, moving averages
- Crime category distribution, station load
- Neighbor influence analysis
- Outputs: `analytics_report.json`, `dashboard_metrics.json`

## Validation

- **TimeSeriesSplit** — no random shuffle, no leakage
- Training: 2021–2024 | Validation: 2025 | Test: 2026
- CV gap = 1 to prevent leakage between folds

## Metrics

All models use regression metrics:
- RMSE, MAE, MAPE, R²
- No classification metrics used

## Outputs

| File | Description |
|------|-------------|
| `models/risk_model.pkl` | Serialized Risk model |
| `models/hotspot_model.pkl` | Serialized Hotspot model |
| `outputs/predictions.csv` | Risk scores + predictions |
| `outputs/hotspot_rankings.csv` | H3 hotspot rankings |
| `outputs/dashboard_metrics.json` | Dashboard-ready metrics |
| `outputs/analytics_report.json` | Full analytics report |
| `outputs/feature_importance.csv` | SHAP + model importance |
| `outputs/model_metrics.json` | CV + test metrics |
| `outputs/shap/shap_values.parquet` | SHAP values |
| `outputs/shap/explanation.json` | Local explanations |
| `outputs/figures/*.png` | All visualizations |
| `FINAL_REPORT.md` | Complete pipeline report |

## Configuration

All parameters in `project/configs/config.py`:
- Data split years
- H3 resolution
- Model hyperparameters (LightGBM)
- SHAP settings
- Output paths

## Dependencies

- Python 3.8+
- lightgbm, numpy, pandas, scikit-learn
- pyarrow (parquet), h3 (spatial), shap (explainability)
- matplotlib, seaborn (visualization)

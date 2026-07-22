# FINAL REPORT — Geospatial Crime Pattern Intelligence

## ET AI Hackathon 2026

---

## 1. Dataset Summary
- Total rows: 52856
- Total columns: 52
- Years covered: 2021-2026
- Source: crime_dataset_v2.parquet

## 2. Missing Values
- Missing values handled: median fill (numeric), mode fill (categorical)
- Columns with >50% missing dropped automatically

## 3. Feature Engineering
- Temporal features: lag features, rolling mean/std (3m, 6m, 12m), EMA
- Seasonal features: Month/Quarter sin-cos encoding
- Growth features: growth rate, momentum, acceleration
- Ratio features: weekend ratio, night crime ratio
- Spatial features: neighbor crime density, population-normalized crime
- H3 spatial indexing for hotspot detection (configurable resolution)

## 4. Selected Features
- Total features selected: 40

## 5. Models Used
- **Risk Model**: LightGBM Regressor (crime intensity prediction)
- **Hotspot Model**: H3 spatial indexing + LightGBM Regressor
- **Explainability**: SHAP TreeExplainer
- **Analytics Engine**: Automated trend/pattern analysis

## 6. Hyperparameters
- Risk Model: LR=0.05, max_depth=7, num_leaves=31, subsample=0.8, colsample=0.8
- Hotspot Model: LR=0.05, max_depth=6, num_leaves=31, subsample=0.8
- H3 resolution: 6 (configurable)
- Early stopping rounds: 50

## 7. Cross Validation Results
- TimeSeriesSplit CV results available in model_metrics.json

## 8. Evaluation Metrics (Test Set)
- RMSE: 194421.6297
- MAE: 55037.5612
- R2: 0.646
- MAPE: 11556.851%

## 9. Feature Importance
- Top features from LightGBM gain importance
- SHAP-based global importance (mean |SHAP|)
- Full details in outputs/feature_importance.csv

## 10. SHAP Insights
- Method: TreeExplainer (interventional perturbation)
- Global importance + local explanations generated
- Summary plot: outputs/figures/shap_summary.png
- SHAP values: outputs/shap/shap_values.parquet
- Explanation JSON: outputs/shap/explanation.json

## 11. Top Risk Areas
- District-level risk scores (0-100) generated
- Priority ranking with confidence estimates
- See outputs/predictions.csv for full results

## 12. Top Hotspots
- H3 cell-level crime predictions
- Rankings with normalized risk scores
- GeoJSON export for mapping
- See outputs/hotspot_rankings.csv and outputs/predictions/hotspots.geojson

## 13. Error Analysis
- Residual plots available in outputs/figures/
- Prediction vs Actual scatter plot
- Residual distribution analysis

## 14. Limitations
- Dataset uses synthetic coordinates (real polygon-constrained)
- Population data from Census 2011 (aged ~15 years)
- H3 hotspot model requires h3 library
- SHAP analysis requires shap library
- No real-time prediction (batch inference only)

## 15. Production Readiness
- Modular Python with docstrings and type hints
- Configuration-driven (project/configs/config.py)
- Logging throughout (project/src/utils/logger.py)
- All models serialized via pickle
- All outputs in structured formats (CSV, JSON, GeoJSON, Parquet, PNG)
- Temporal train/val/test split - no leakage

## 16. Future Improvements
- Integrate real-time streaming prediction
- Add external covariates (weather, economic indicators)
- Deploy as REST API with FastAPI
- Add model drift monitoring
- Support for additional spatial resolutions
- Add ensemble methods (stacking, blending)
- Dashboard integration with real maps (Mapbox, Leaflet)

---
*Report generated automatically by ET Pipeline*
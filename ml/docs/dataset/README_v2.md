# EdgeGuard Geospatial Crime Pattern Intelligence — Dataset (Version 2)

ET AI Hackathon 2026 · Research-grade upgrade of Version 1.

> Version 2 does not regenerate the project — it is a genuine improvement
> layer on top of V1's honest, cited foundation (see the original README.md
> for everything that carries over unchanged: what's Official vs Derived vs
> Synthetic at the state-total level, the sampling/weighting design, and the
> core ethics/privacy position).

## What actually changed, and why it's a real improvement (not cosmetic)

| Area | Version 1 | Version 2 | Verifiable? |
|---|---|---|---|
| Coordinates | Uniform draw inside a hand-drawn rectangle | Rejection-sampled inside a **real polygon** (GADM-derived, via `geohacker/india` on GitHub — a source explicitly sanctioned by your own Rule 2) | Yes — `viz_delhi_real_polygon_map.png` shows the actual shape; `validation_report_v2.txt` spot-checks 2,000 points against the polygon (98.6% pass; the 1.4% edge cases are documented, not hidden) |
| Delhi district split | Population only | 4-factor documented allocation: population (55%), density (20%), commercial activity (15%), capital-city effect (10%) — see `ALLOCATION_WEIGHTS` | Yes — formula is in `official_reference_v2.py`, fully inspectable |
| Delhi district character | Identical distributions across all 11 districts | Each district has a documented `category_boost` and `office_hour_bias` (e.g. New Delhi skews toward Fake Investment Scam/Loan Fraud with a 1.6x office-hour bias; North East Delhi skews toward SIM Swap/Loan Fraud with a lower office-hour bias) | Yes — `DELHI_DISTRICT_PROFILE` in `official_reference_v2.py`, and `viz_crime_distribution_v2.png` shows the resulting mix difference |
| Neighbor/spatial features | "Neighbor" = other Delhi districts averaged, no real adjacency | Real adjacency graph built from **polygon `.touches()`/`.intersects()`** — confirmed correct: the model independently discovered that Delhi's real neighbours are Haryana and Uttar Pradesh, purely from geometry | Yes — printed during `feature_engineering_v2.py` run, reproducible |
| Temporal detail | Month + basic hour mixture | + Quarter, Week, Is_Weekend, Is_Office_Hour, Is_Night, Is_Festival_Month, festival-month loss bump | Yes — all boolean flags derivable from `Incident_Date`/hour |
| ML features | Risk_Index, Trend, Growth, Neighbor_District_Risk | + Spatial_Lag, Local_Moran_I_Proxy (documented simplification), Cluster_ID (KMeans, Delhi only), Distance_to_District_HQ_km (real polygon centroid), Risk_Percentile, Risk_Rank, Trend_Score, Anomaly_Score, Historical_Growth, Expected_Growth | Yes — every formula documented in `feature_dictionary_v2.csv` |

## What did NOT improve, and why (honesty over completeness)

Per your Step 4 instruction — *"If polygons cannot be obtained, stop and
explain why"* — here is exactly where that applies:

1. **No official district-level polygons exist for India outside this GADM
   snapshot.** We searched (Rule 2 priority order: NIC/Survey of India/OGD
   first). We *did* find a public India GIS aggregator page listing
   official-sourced parquet/shapefile boundaries (LGD/Survey of India/Bhuvan/
   DataMeet), but its actual download endpoints were not reachable from this
   sandbox (network egress restricted to package registries + GitHub). The
   GADM-derived GeoJSON on GitHub *was* reachable and *is* real polygon data,
   so we used it — but it is a ~2009 snapshot, not the current official
   boundary set. This is a documented compromise, not a silent one.
2. **Delhi's 11 districts still do not have real individual polygons** in
   this GADM snapshot (it only has one combined "Delhi" shape at this
   admin level). We clipped our hand-drawn cardinal rectangles to the *real*
   Delhi outer boundary — genuinely better than V1 (no more points spilling
   into Haryana/UP), but still an approximation internally.
   `Coordinate_Type = "Polygon_Clipped_Estimate"` on every such row makes
   this impossible to mistake for an official district survey.
3. **Telangana and Ladakh** reuse their pre-split parent's undivided GADM
   polygon (Andhra Pradesh and Jammu & Kashmir respectively), because this
   snapshot predates their creation (2014 and 2019). Flagged
   `Coordinate_Type = "Polygon_Approximate"`.
4. **District-level socioeconomic covariates** (internet penetration,
   digital payment adoption, bank branch density, road density, police
   station counts) requested in Step 1: we found no state-wise TRAI/NPCI
   table with clean, decomposable numbers reachable in this environment
   (TRAI's own PDF reports group multiple states into "telecom circles" that
   don't cleanly map to individual states — e.g. the Bihar circle includes
   Jharkhand). Rather than force a fabricated number, we used only a
   **qualitative, capped tier** (`Digital_Adoption_Tier`: high/mid/low,
   ±15% max influence) built from cross-corroborated secondary sources, and
   labelled it as such everywhere. Bank branches, road density, and police
   station counts remain entirely unsourced and are either omitted or
   marked as synthetic placeholders (`Distance_to_Nearest_Police_Station_km`).

## Files (Version 2)

- `crime_dataset_v2.csv`, `crime_dataset_v2.parquet` — 52,856 rows, 56 columns
- `metadata_v2.json`, `feature_dictionary_v2.csv`, `validation_report_v2.txt`
- `unit_year_aggregates_v2.csv` — the underlying (State/District/Year) aggregate table before incident-level expansion, useful for auditing the allocation model directly
- `viz_delhi_real_polygon_map.png` — proof-of-work: real polygons + sampled points
- `viz_district_ranking_v2.png`, `viz_monthly_trends_v2.png`, `viz_crime_distribution_v2.png`, `viz_moran_scatter_v2.png`, `viz_delhi_clusters_v2.png`, `viz_risk_distribution_v2.png`, `viz_correlation_matrix_v2.png`
- `research_addendum_v2.md` — assumption register, allocation-model math, bias/ethics notes for everything new in V2
- `code/` — all generation code (`build_geometry.py`, `official_reference_v2.py`, `generate_dataset_v2.py`, `feature_engineering_v2.py`, `validate_v2.py`, `save_outputs_v2.py`, `visualize_v2.py`)

## Formula reference (Step 2/6 documentation, consolidated)

```
Delhi District Allocation:
  Score_d = 0.55*PopShare_d + 0.20*DensityShare_d + 0.15*CommercialShare_d + 0.10*CapitalCityShare_d
  District_Total_d = round(State_Total * Score_d / sum(Score))

Risk_Index (per unit-year):
  rate_norm     = min(Crime_Rate_100k / 50, 1.0)
  growth_term   = clip(Growth_Rate, 0, 2.0)
  neighbor_norm = Neighbor_District_Risk(real adjacency) / max(Crime_Count_District)
  Risk_Index    = clip(0.5*rate_norm + 0.3*growth_term + 0.2*neighbor_norm, 0, 1)

Spatial_Lag_i       = mean(Crime_Rate_100k_j) for j geometrically adjacent to i
Local_Moran_I_Proxy = z_i * mean(z_j for j adjacent), z = standardised Crime_Rate_100k
Anomaly_Score       = |z-score of Growth_Rate| within the unit's own time series
Trend_Score          = min-max normalised Trend_Last_3_Years, computed within each Year
Risk_Percentile/Rank = percentile rank / rank of Risk_Index within each Year
Distance_to_District_HQ_km = haversine(incident point, polygon centroid of its unit)
```

## Still true from Version 1 (unchanged, restated for completeness)

- Every incident row is `Data_Source = Synthetic_Record_From_Official_Distribution`.
- Only NCRB state/UT totals (2021–2023) are `Aggregate_Basis = Official`;
  2024–2026 remain trend-projected `Derived`.
- `Sample_Weight` reconstructs official/derived totals exactly (re-verified
  in `validation_report_v2.txt`: max reconciliation error 0.0000).
- This dataset must never be presented as containing real incidents.

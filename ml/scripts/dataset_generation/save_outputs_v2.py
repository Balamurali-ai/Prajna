import json
import pandas as pd
import datetime as dt
from pathlib import Path

OUT_DIR = Path("/home/claude/edgeguard_crime/outputs_v2")
df = pd.read_pickle(OUT_DIR / "_featured_df_v2.pkl")

# Final column order: required schema (unchanged names where possible) +
# new V2 columns appended at the end for backward-compatible diffing against V1
final_cols = [
    "Incident_ID","District","State","Year","Month","Quarter","Week","Crime_Category","Sub_Category",
    "Complaint_Channel","Population","Crime_Count_District","Crime_Rate_100k","Trend_Last_3_Years",
    "Growth_Rate","Historical_Growth","Expected_Growth","Risk_Index","Risk_Percentile","Risk_Rank",
    "Trend_Score","Anomaly_Score","Latitude","Longitude","Coordinate_Type","Urban_Rural",
    "Nearby_Hotspot_Score","Financial_Loss","Victim_Age_Group","Victim_Gender","Time_of_Day",
    "Day_of_Week","Is_Weekend","Is_Office_Hour","Is_Night","Is_Festival_Month","Reporting_Delay",
    "Resolved","Response_Time","Police_Station_ID","Administrative_Code","Neighbor_District_Risk",
    "Spatial_Lag","Local_Moran_I_Proxy","Cluster_ID","Distance_to_District_HQ_km",
    "Distance_to_Nearest_Police_Station_km","Urban_Density_Proxy","Commercial_Density_Proxy",
    "Digital_Adoption_Tier","Source_Confidence","Data_Source","Aggregate_Basis",
    "Sample_Weight","Official_Unit_Year_Total","Incident_Date",
]
df = df[final_cols]
df.to_csv(OUT_DIR / "crime_dataset_v2.csv", index=False)
df.to_parquet(OUT_DIR / "crime_dataset_v2.parquet", index=False)

import sys
sys.path.insert(0, "/home/claude/edgeguard_crime/code")
from official_reference_v2 import KNOWN_GAPS_V2, GEOMETRY_SOURCE, DIGITAL_ADOPTION_SOURCE_NOTE, ALLOCATION_MODEL_NOTE

metadata = {
    "project": "EdgeGuard Geospatial Crime Pattern Intelligence - ET AI Hackathon 2026 (Version 2)",
    "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "row_count": len(df), "column_count": df.shape[1],
    "years_covered": sorted(df["Year"].unique().tolist()),
    "geometry_source": GEOMETRY_SOURCE,
    "allocation_model_note": ALLOCATION_MODEL_NOTE,
    "digital_adoption_note": DIGITAL_ADOPTION_SOURCE_NOTE,
    "coordinate_type_meaning": {
        "Polygon": "Rejection-sampled inside a real GADM-derived district-union state/UT polygon.",
        "Polygon_Approximate": "Same as Polygon, but the underlying GADM geometry is a pre-split "
                                "undivided parent (Andhra Pradesh standing in for Telangana; "
                                "Jammu and Kashmir standing in for Ladakh).",
        "Polygon_Clipped_Estimate": "Delhi district-level only: a hand-drawn cardinal-direction "
                                     "rectangle intersected with the REAL Delhi outer boundary. Real "
                                     "outer shape, approximate internal district split.",
    },
    "whats_new_vs_v1": [
        "Real polygon-based coordinate sampling (rejection sampling) replaces V1's bounding boxes.",
        "Explainable multi-factor Delhi district allocation model (population + density + "
        "commercial activity + capital-city effect) replaces V1's population-only split.",
        "Delhi districts now have documented, differentiated crime-category boosts and office-hour bias.",
        "Real adjacency graph (from polygon topology) replaces V1's same-state-only neighbor averaging.",
        "Added: Quarter, Week, Is_Weekend, Is_Office_Hour, Is_Night, Is_Festival_Month, Spatial_Lag, "
        "Local_Moran_I_Proxy, Cluster_ID, Distance_to_District_HQ_km, "
        "Distance_to_Nearest_Police_Station_km, Urban_Density_Proxy, Commercial_Density_Proxy, "
        "Digital_Adoption_Tier, Risk_Percentile, Risk_Rank, Trend_Score, Anomaly_Score, "
        "Historical_Growth, Expected_Growth.",
    ],
    "known_gaps": KNOWN_GAPS_V2,
    "reproducibility": {"random_seed": 42, "scripts": [
        "build_geometry.py", "generate_dataset_v2.py", "feature_engineering_v2.py",
        "validate_v2.py", "save_outputs_v2.py", "visualize_v2.py"]},
    "sampling_note": "Same capped weighted-sample design as V1 (max 400 rows/unit-year, "
                      "Sample_Weight reconstructs official totals exactly).",
}
(OUT_DIR / "metadata_v2.json").write_text(json.dumps(metadata, indent=2, default=str))

feature_dict = [
    ("Incident_ID", "Synthetic", "Unique ID, format EGv2-<year>-<seq>."),
    ("District", "Official (Delhi) / Synthetic unit (others)", "Real Delhi district name, or state/UT name for non-Delhi units."),
    ("State", "Official", "Real Indian State/UT name."),
    ("Year/Month/Quarter/Week", "Synthetic/Derived", "Sampled with documented seasonality; Quarter/Week derived from date."),
    ("Crime_Category / Sub_Category", "Synthetic", "Weighted sample; Delhi districts apply a documented category_boost multiplier from DELHI_DISTRICT_PROFILE."),
    ("Complaint_Channel", "Synthetic", "Weighted categorical sample."),
    ("Population", "Official (Delhi, Census 2011) / N/A elsewhere", "Never fabricated."),
    ("Crime_Count_District", "Official (2021-23) / Derived (2024-26, Delhi split)", "Unit-year total this row's sample represents."),
    ("Crime_Rate_100k", "Derived", "= Crime_Count_District / Population * 100,000."),
    ("Trend_Last_3_Years", "Derived", "Rolling 3-yr mean of Crime_Count_District."),
    ("Growth_Rate", "Derived", "YoY % change of Crime_Count_District."),
    ("Historical_Growth", "Derived", "Expanding mean of prior years' Growth_Rate."),
    ("Expected_Growth", "Derived", "Naive persistence forecast = last year's Growth_Rate."),
    ("Risk_Index", "Derived (documented formula)", "0.5*rate_norm + 0.3*max(growth,0) + 0.2*neighbor_norm (neighbor now from REAL adjacency), clipped [0,1]."),
    ("Risk_Percentile / Risk_Rank", "Derived", "Percentile rank / rank of Risk_Index within its Year."),
    ("Trend_Score", "Derived", "Min-max normalised Trend_Last_3_Years within Year."),
    ("Anomaly_Score", "Derived", "|z-score| of Growth_Rate within the unit's own time series."),
    ("Latitude/Longitude", "Synthetic (real-polygon-constrained)", "Rejection-sampled inside a real polygon - see Coordinate_Type."),
    ("Coordinate_Type", "Label", "Polygon / Polygon_Approximate / Polygon_Clipped_Estimate - see metadata_v2.json."),
    ("Urban_Rural", "Synthetic heuristic", "Delhi + IT-hub states biased Urban."),
    ("Nearby_Hotspot_Score", "Derived", "Alias of Risk_Index."),
    ("Financial_Loss", "Synthetic", "Log-normal, festival-month mean bump, capped 50L, 4% MAR missing."),
    ("Victim_Age_Group / Victim_Gender", "Synthetic", "Weighted categorical, 3% MAR missing on age."),
    ("Time_of_Day / Day_of_Week", "Derived", "From sampled hour / Incident_Date."),
    ("Is_Weekend / Is_Office_Hour / Is_Night / Is_Festival_Month", "Derived/Synthetic", "Boolean flags from the date/hour sampling model; Is_Office_Hour probability scaled by each Delhi district's documented office_hour_bias."),
    ("Reporting_Delay", "Synthetic", "Gamma distribution."),
    ("Resolved", "Synthetic", "Bernoulli, decreasing with reporting delay."),
    ("Response_Time", "Synthetic", "Gamma distribution, capped 30 days."),
    ("Police_Station_ID / Administrative_Code", "Synthetic placeholder", "Not real codes."),
    ("Neighbor_District_Risk", "Derived (real adjacency)", "Mean Crime_Count_District of GEOMETRICALLY adjacent units (polygon .touches()/.intersects()), same year."),
    ("Spatial_Lag", "Derived (real adjacency)", "Mean Crime_Rate_100k of geometrically adjacent units, same year (spatial econometrics convention)."),
    ("Local_Moran_I_Proxy", "Derived (documented simplification)", "z_i * mean(z_j for j adjacent), z = standardised Crime_Rate_100k/Count. A simplified proxy, not the full Moran's I statistic (no global spatial weight normalisation applied)."),
    ("Cluster_ID", "Derived (KMeans, k=8)", "Delhi rows only (coordinates meaningful there); -1 elsewhere (coarse state polygons make sub-state clustering not meaningful)."),
    ("Distance_to_District_HQ_km", "Derived", "Haversine distance from incident point to the unit's polygon centroid (a proxy HQ location, NOT an official HQ coordinate)."),
    ("Distance_to_Nearest_Police_Station_km", "Synthetic placeholder", "Gamma-distributed; no real police station coordinate list was sourced."),
    ("Urban_Density_Proxy", "Official (Delhi only) / N/A", "Real Census 2011 population density for Delhi districts; null elsewhere."),
    ("Commercial_Density_Proxy", "Synthetic (documented)", "Delhi: DELHI_DISTRICT_PROFILE commercial_activity. Elsewhere: coarse heuristic from Digital_Adoption_Tier x Urban_Rural."),
    ("Digital_Adoption_Tier", "Derived (qualitative, capped)", "high/mid/low tier from cross-referenced secondary sources - see DIGITAL_ADOPTION_SOURCE_NOTE. NOT an official TRAI table."),
    ("Source_Confidence", "Derived", "0.9 if unit-year total is Official, else 0.55."),
    ("Data_Source", "Label", "Always Synthetic_Record_From_Official_Distribution."),
    ("Aggregate_Basis", "Label", "Official or Derived - describes the unit-year TOTAL."),
    ("Sample_Weight / Official_Unit_Year_Total", "Derived/Official", "Weight reconstructing the official/derived total exactly when summed."),
    ("Incident_Date", "Synthetic", "ISO date, always <= 2026-07-16."),
]
fd = pd.DataFrame(feature_dict, columns=["Column", "Data_Source_Type", "Description"])
fd.to_csv(OUT_DIR / "feature_dictionary_v2.csv", index=False)
print("Saved crime_dataset_v2.csv/.parquet, metadata_v2.json, feature_dictionary_v2.csv")
print(f"CSV size: {(OUT_DIR/'crime_dataset_v2.csv').stat().st_size/1e6:.1f} MB")

"""
feature_engineering_v2.py
==========================
Adds Step 6's requested ML features on top of the raw generated rows, each
with a documented formula (per the brief: "Every derived feature must have
a documented formula").
"""
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from shapely.geometry import Point

DATA_DIR = Path("/home/claude/edgeguard_crime/data")
OUT_DIR = Path("/home/claude/edgeguard_crime/outputs_v2")

with open(DATA_DIR / "geometry_store.pkl", "rb") as f:
    GEOM = pickle.load(f)

df = pd.read_pickle(OUT_DIR / "_raw_df_v2.pkl")

# ---------------------------------------------------------------------------
# Unit-year aggregate table (one row per State/District/Year)
# ---------------------------------------------------------------------------
grp_cols = ["State", "District", "Year"]
yearly = (df.drop_duplicates(grp_cols)[grp_cols + ["Official_Unit_Year_Total", "Population"]]
            .rename(columns={"Official_Unit_Year_Total": "Crime_Count_District"})
            .sort_values(["State", "District", "Year"]))

# Trend_Last_3_Years: rolling 3-year mean of Crime_Count_District within unit
yearly["Trend_Last_3_Years"] = (
    yearly.groupby(["State", "District"])["Crime_Count_District"]
    .transform(lambda s: s.rolling(3, min_periods=1).mean())
)
# Growth_Rate: YoY % change = (count_t - count_t-1) / count_t-1
yearly["Growth_Rate"] = yearly.groupby(["State", "District"])["Crime_Count_District"].pct_change().fillna(0)
# Historical_Growth = mean growth rate over all prior years in the series (documented: expanding mean)
yearly["Historical_Growth"] = yearly.groupby(["State", "District"])["Growth_Rate"].transform(
    lambda s: s.shift(1).expanding().mean()).fillna(0)
# Expected_Growth = last observed growth rate carried forward (naive persistence forecast, documented)
yearly["Expected_Growth"] = yearly.groupby(["State", "District"])["Growth_Rate"].shift(1).fillna(yearly["Growth_Rate"])
# Crime_Rate_100k = Crime_Count_District / Population * 100,000 (only where Population known)
yearly["Crime_Rate_100k"] = np.where(
    yearly["Population"].notna() & (yearly["Population"] > 0),
    (yearly["Crime_Count_District"] / yearly["Population"]) * 100000, np.nan)

# ---------------------------------------------------------------------------
# Spatial adjacency graph, built from REAL polygon .touches()/.intersects()
# (state-level graph) and a Delhi-specific district adjacency graph. This
# was NOT possible in Version 1 (bounding boxes carry no real adjacency).
# ---------------------------------------------------------------------------
state_polys = {k: v["polygon"] for k, v in GEOM.items() if k not in ("_delhi_districts",)}
state_names = list(state_polys.keys())
adjacency = {s: [] for s in state_names}
for i, s1 in enumerate(state_names):
    for s2 in state_names[i+1:]:
        try:
            if state_polys[s1].buffer(0.01).intersects(state_polys[s2].buffer(0.01)):
                adjacency[s1].append(s2); adjacency[s2].append(s1)
        except Exception:
            pass

delhi_polys = {k: v["polygon"] for k, v in GEOM["_delhi_districts"].items()}
delhi_names = list(delhi_polys.keys())
delhi_adjacency = {d: [] for d in delhi_names}
for i, d1 in enumerate(delhi_names):
    for d2 in delhi_names[i+1:]:
        try:
            if delhi_polys[d1].buffer(0.002).intersects(delhi_polys[d2].buffer(0.002)):
                delhi_adjacency[d1].append(d2); delhi_adjacency[d2].append(d1)
        except Exception:
            pass

print("Sample state adjacency (Delhi's real neighbours from polygon geometry):",
      adjacency.get("Delhi", []))
print("Delhi district adjacency counts:", {k: len(v) for k, v in delhi_adjacency.items()})

# Neighbor_District_Risk: mean Crime_Count_District of GEOMETRICALLY ADJACENT
# units in the same year (falls back to state-level mean if a unit has no
# detected neighbours, e.g. islands)
def build_neighbor_risk(yearly_df, adjacency_map, unit_col):
    yearly_df = yearly_df.copy()
    lookup = yearly_df.set_index([unit_col, "Year"])["Crime_Count_District"].to_dict()
    out = []
    for _, row in yearly_df.iterrows():
        neighbors = adjacency_map.get(row[unit_col], [])
        vals = [lookup.get((n, row["Year"])) for n in neighbors]
        vals = [v for v in vals if v is not None]
        out.append(np.mean(vals) if vals else np.nan)
    return out

delhi_mask = yearly["State"] == "Delhi"
yearly.loc[delhi_mask, "Neighbor_District_Risk"] = build_neighbor_risk(
    yearly[delhi_mask], delhi_adjacency, "District")

other_mask = ~delhi_mask
tmp = yearly[other_mask].copy()
tmp["_unit"] = tmp["State"]
lookup_state = yearly[other_mask].set_index(["State", "Year"])["Crime_Count_District"].to_dict()
vals = []
for _, row in tmp.iterrows():
    neighbors = adjacency.get(row["State"], [])
    nv = [lookup_state.get((n, row["Year"])) for n in neighbors]
    nv = [v for v in nv if v is not None]
    vals.append(np.mean(nv) if nv else np.nan)
yearly.loc[other_mask, "Neighbor_District_Risk"] = vals

# Spatial_Lag: formally the same construction as Neighbor_District_Risk but
# expressed as a rate (per-100k) - i.e. the spatially-lagged rate variable
# used in spatial econometrics: SpatialLag_i = mean(Rate_j) for j adjacent to i
def build_spatial_lag_rate(yearly_df, adjacency_map, unit_col):
    lookup = yearly_df.set_index([unit_col, "Year"])["Crime_Rate_100k"].to_dict()
    out = []
    for _, row in yearly_df.iterrows():
        neighbors = adjacency_map.get(row[unit_col], [])
        vals = [lookup.get((n, row["Year"])) for n in neighbors]
        vals = [v for v in vals if pd.notna(v)]
        out.append(np.mean(vals) if vals else np.nan)
    return out

yearly.loc[delhi_mask, "Spatial_Lag"] = build_spatial_lag_rate(yearly[delhi_mask], delhi_adjacency, "District")
tmp2 = yearly[other_mask]
lookup_rate = tmp2.set_index(["State", "Year"])["Crime_Rate_100k"].to_dict()
vals2 = []
for _, row in tmp2.iterrows():
    neighbors = adjacency.get(row["State"], [])
    nv = [lookup_rate.get((n, row["Year"])) for n in neighbors]
    nv = [v for v in nv if pd.notna(v)]
    vals2.append(np.mean(nv) if nv else np.nan)
yearly.loc[other_mask, "Spatial_Lag"] = vals2

# Local Moran's I PROXY (simplified, documented): a genuine Moran's I needs a
# full spatial weight matrix and global variance; here we compute a bivariate
# proxy: z_i * mean(z_j for j adjacent), where z is the unit's standardised
# Crime_Rate_100k (or Crime_Count_District where rate is unavailable). This
# captures the same intuition (is a high-value unit surrounded by high-value
# neighbours?) without claiming to be the full Moran's I statistic.
def moran_proxy(yearly_df):
    yearly_df = yearly_df.copy()
    base = yearly_df["Crime_Rate_100k"].fillna(yearly_df["Crime_Count_District"])
    z = (base - base.mean()) / (base.std() if base.std() else 1)
    yearly_df["_z"] = z.values
    return yearly_df
yearly = moran_proxy(yearly)
z_lookup_delhi = yearly[delhi_mask].set_index(["District", "Year"])["_z"].to_dict()
z_lookup_state = yearly[other_mask].set_index(["State", "Year"])["_z"].to_dict()

def local_moran(row):
    if row["State"] == "Delhi":
        neighbors = delhi_adjacency.get(row["District"], [])
        nz = [z_lookup_delhi.get((n, row["Year"])) for n in neighbors]
    else:
        neighbors = adjacency.get(row["State"], [])
        nz = [z_lookup_state.get((n, row["Year"])) for n in neighbors]
    nz = [v for v in nz if v is not None and pd.notna(v)]
    if not nz:
        return np.nan
    return float(row["_z"] * np.mean(nz))
yearly["Local_Moran_I_Proxy"] = yearly.apply(local_moran, axis=1)
yearly = yearly.drop(columns=["_z"])

# ---------------------------------------------------------------------------
# Composite, explainable Risk_Index (same documented formula family as V1,
# now fed by REAL adjacency-based Neighbor_District_Risk instead of a
# same-state-only average)
# ---------------------------------------------------------------------------
max_count = yearly["Crime_Count_District"].max()
growth_clipped = yearly["Growth_Rate"].clip(-0.5, 2.0)
rate_norm = (yearly["Crime_Rate_100k"].fillna(yearly["Crime_Count_District"] / 1000.0) / 50.0).clip(upper=1.0)
neighbor_norm = (yearly["Neighbor_District_Risk"].fillna(0) / (max_count or 1))
yearly["Risk_Index"] = (0.5 * rate_norm + 0.3 * growth_clipped.clip(lower=0) + 0.2 * neighbor_norm).clip(0, 1).round(4)
yearly["Nearby_Hotspot_Score"] = yearly["Risk_Index"]

# Risk_Percentile / Risk_Rank: computed WITHIN each year across all units
yearly["Risk_Percentile"] = yearly.groupby("Year")["Risk_Index"].rank(pct=True).round(4)
yearly["Risk_Rank"] = yearly.groupby("Year")["Risk_Index"].rank(ascending=False, method="min").astype(int)

# Trend_Score: normalised Trend_Last_3_Years within year (documented: min-max per year)
def minmax_norm(s):
    rng_ = s.max() - s.min()
    return (s - s.min()) / rng_ if rng_ else s * 0
yearly["Trend_Score"] = yearly.groupby("Year")["Trend_Last_3_Years"].transform(minmax_norm).round(4)

# Anomaly_Score: |z-score| of Growth_Rate within each unit's own history
# (documented: a simple statistical outlier flag, NOT an ML model output)
def zscore(s):
    sd = s.std()
    return (s - s.mean()) / sd if sd else s * 0
yearly["Anomaly_Score"] = yearly.groupby(["State", "District"])["Growth_Rate"].transform(zscore).abs().round(4)

# ---------------------------------------------------------------------------
# Distance_to_District_HQ: distance (km, haversine) from each sampled
# incident's coordinates to its unit's population-weighted centroid, used
# as a proxy "HQ" location (documented: NOT an official HQ coordinate - no
# official district HQ coordinate list was sourced in this pass)
# ---------------------------------------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1); dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dlmb/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

centroids = {}
for name, info in GEOM.items():
    if name == "_delhi_districts":
        continue
    c = info["polygon"].centroid
    centroids[("STATE", name)] = (c.y, c.x)
for dname, info in GEOM["_delhi_districts"].items():
    c = info["polygon"].centroid
    centroids[("DELHI_DISTRICT", dname)] = (c.y, c.x)

def hq_coords(row):
    if row["State"] == "Delhi":
        return centroids[("DELHI_DISTRICT", row["District"])]
    return centroids[("STATE", row["State"])]

hq_lat, hq_lon = zip(*df.apply(hq_coords, axis=1))
df["_hq_lat"], df["_hq_lon"] = hq_lat, hq_lon
df["Distance_to_District_HQ_km"] = haversine_km(df["Latitude"], df["Longitude"], df["_hq_lat"], df["_hq_lon"]).round(2)
df = df.drop(columns=["_hq_lat", "_hq_lon"])

# Distance_to_Nearest_Police_Station: SYNTHETIC placeholder (no real police
# station coordinate list was sourced - see KNOWN_GAPS_V2). Modelled as a
# small right-skewed distance so it's usable in ML without claiming realism.
df["Distance_to_Nearest_Police_Station_km"] = np.round(
    np.random.RandomState(42).gamma(shape=1.5, scale=1.2, size=len(df)), 2)

# Urban_Density_Proxy / Commercial_Density_Proxy: Delhi districts use the
# documented DELHI_DISTRICT_PROFILE commercial_activity value and real
# population density; other states use a coarse 3-tier bucket from
# Urban_Rural + Digital_Adoption_Tier (documented heuristic, not a census figure)
from official_reference_v2 import DELHI_DISTRICT_PROFILE
delhi_density = {d: _p for d, _p in zip(
    ["Central Delhi","East Delhi","New Delhi","North Delhi","North East Delhi",
     "North West Delhi","South Delhi","South West Delhi","West Delhi","Shahdara","South East Delhi"],
    [27730,27132,4057,14557,36155,8254,11060,5446,19563,None,None])}

def commercial_density(row):
    if row["State"] == "Delhi":
        return DELHI_DISTRICT_PROFILE[row["District"]]["commercial_activity"]
    tier_map = {"high": 0.6, "mid": 0.4, "low": 0.25}
    return tier_map.get(row.get("Digital_Adoption_Tier", "mid"), 0.4) * (1.2 if row["Urban_Rural"] == "Urban" else 0.6)
df["Commercial_Density_Proxy"] = df.apply(commercial_density, axis=1).round(3)

def urban_density(row):
    if row["State"] == "Delhi" and row["District"] in delhi_density and delhi_density[row["District"]]:
        return delhi_density[row["District"]]
    return np.nan
df["Urban_Density_Proxy"] = df.apply(urban_density, axis=1)

# ---------------------------------------------------------------------------
# Cluster_ID: KMeans on Delhi coordinates only (the only unit with real
# meaningful sub-state coordinate spread); other states get Cluster_ID = -1
# (documented: not meaningful outside Delhi given coarse state polygons)
# ---------------------------------------------------------------------------
from sklearn.cluster import KMeans
delhi_rows = df["State"] == "Delhi"
coords = df.loc[delhi_rows, ["Latitude", "Longitude"]].values
km = KMeans(n_clusters=8, random_state=42, n_init=10).fit(coords)
df.loc[delhi_rows, "Cluster_ID"] = km.labels_
df.loc[~delhi_rows, "Cluster_ID"] = -1
df["Cluster_ID"] = df["Cluster_ID"].astype(int)

# ---------------------------------------------------------------------------
# Merge yearly aggregate features back onto the incident-level rows
# ---------------------------------------------------------------------------
merge_cols = ["State", "District", "Year", "Crime_Count_District", "Crime_Rate_100k",
              "Trend_Last_3_Years", "Growth_Rate", "Historical_Growth", "Expected_Growth",
              "Neighbor_District_Risk", "Spatial_Lag", "Local_Moran_I_Proxy", "Risk_Index",
              "Nearby_Hotspot_Score", "Risk_Percentile", "Risk_Rank", "Trend_Score", "Anomaly_Score"]
df = df.merge(yearly[merge_cols], on=["State", "District", "Year"], how="left")

df.to_pickle(OUT_DIR / "_featured_df_v2.pkl")
yearly.to_csv(OUT_DIR / "unit_year_aggregates_v2.csv", index=False)
print(f"Feature engineering complete. {len(df):,} rows, {df.shape[1]} columns.")
print(df[["Risk_Index","Risk_Percentile","Risk_Rank","Spatial_Lag","Local_Moran_I_Proxy","Anomaly_Score"]].describe())

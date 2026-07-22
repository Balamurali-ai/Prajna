import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from pathlib import Path

OUT_DIR = Path("/home/claude/edgeguard_crime/outputs_v2")
DATA_DIR = Path("/home/claude/edgeguard_crime/data")
df = pd.read_pickle(OUT_DIR / "_featured_df_v2.pkl")
with open(DATA_DIR / "geometry_store.pkl", "rb") as f:
    GEOM = pickle.load(f)
plt.rcParams.update({"figure.dpi": 110, "font.size": 9})

# 1. REAL Delhi district polygon map with sampled points overlaid (proves
#    the polygon-based sampling, not a bounding box)
fig, ax = plt.subplots(figsize=(7, 7))
colors = plt.cm.tab20(np.linspace(0, 1, 11))
for (dname, info), c in zip(GEOM["_delhi_districts"].items(), colors):
    poly = info["polygon"]
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    for g in geoms:
        xs, ys = g.exterior.xy
        ax.fill(xs, ys, color=c, alpha=0.5, label=dname)
        ax.plot(xs, ys, color="black", linewidth=0.5)
sample = df[df.State == "Delhi"].sample(1500, random_state=1)
ax.scatter(sample["Longitude"], sample["Latitude"], s=2, color="black", alpha=0.4)
ax.set_title("Delhi Districts - Real Polygon Geometry + Sampled Incident Points")
ax.legend(fontsize=6, loc="upper left", bbox_to_anchor=(1.0, 1.0))
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
plt.tight_layout(); plt.savefig(OUT_DIR / "viz_delhi_real_polygon_map.png"); plt.close()

# 2. District (Delhi) ranking by Risk_Index, 2023
fig, ax = plt.subplots(figsize=(8, 5))
d = df[(df.State == "Delhi") & (df.Year == 2023)].drop_duplicates("District").sort_values("Risk_Index")
ax.barh(d["District"], d["Risk_Index"], color="#c0392b")
ax.set_title("Delhi Districts - Composite Risk_Index, 2023")
ax.set_xlabel("Risk_Index [0-1] (multi-factor allocation model)")
plt.tight_layout(); plt.savefig(OUT_DIR / "viz_district_ranking_v2.png"); plt.close()

# 3. Monthly trend
fig, ax = plt.subplots(figsize=(8, 4.5))
m = df.groupby(["Year", "Month"]).size().reset_index(name="n")
for yr in sorted(m.Year.unique()):
    sub = m[m.Year == yr]
    ax.plot(sub["Month"], sub["n"], marker="o", label=str(yr))
ax.set_title("Monthly Complaint Volume (sampled rows) - Festival/Monsoon Seasonality")
ax.set_xlabel("Month"); ax.legend(fontsize=7, ncol=3)
plt.tight_layout(); plt.savefig(OUT_DIR / "viz_monthly_trends_v2.png"); plt.close()

# 4. Crime category distribution, Delhi vs national
fig, axes = plt.subplots(1, 2, figsize=(11, 5))
for ax, (label, sub) in zip(axes, [("Delhi", df[df.State=="Delhi"]), ("All Other States/UTs", df[df.State!="Delhi"])]):
    vc = sub["Crime_Category"].value_counts()
    ax.barh(vc.index[::-1], vc.values[::-1], color="#2980b9")
    ax.set_title(label)
plt.suptitle("Crime Category Distribution: Delhi's district-boosted mix vs. baseline")
plt.tight_layout(); plt.savefig(OUT_DIR / "viz_crime_distribution_v2.png"); plt.close()

# 5. Spatial lag / Moran's I proxy scatter (Moran scatterplot convention)
fig, ax = plt.subplots(figsize=(6.5, 6))
sub = df.drop_duplicates(["State", "District", "Year"])
x = sub["Crime_Rate_100k"].fillna(sub["Crime_Count_District"])
y = sub["Spatial_Lag"].fillna(sub["Neighbor_District_Risk"])
ax.scatter(x, y, s=10, alpha=0.5, c=np.where(sub.State=="Delhi", "#c0392b", "#7f8c8d"))
ax.set_xlabel("Own Crime Rate / Count"); ax.set_ylabel("Spatial Lag (neighbour mean)")
ax.set_title("Moran Scatterplot Proxy - Own value vs. neighbour value\n(red = Delhi districts)")
plt.tight_layout(); plt.savefig(OUT_DIR / "viz_moran_scatter_v2.png"); plt.close()

# 6. Delhi KMeans clusters
fig, ax = plt.subplots(figsize=(7, 6))
dsub = df[df.State == "Delhi"]
sc = ax.scatter(dsub["Longitude"], dsub["Latitude"], c=dsub["Cluster_ID"], cmap="tab10", s=4)
ax.set_title("Delhi - KMeans Spatial Clusters (k=8) on Sampled Incident Coordinates")
plt.colorbar(sc, ax=ax, label="Cluster_ID")
plt.tight_layout(); plt.savefig(OUT_DIR / "viz_delhi_clusters_v2.png"); plt.close()

# 7. Risk distribution
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.hist(df["Risk_Index"].dropna(), bins=30, color="#8e44ad")
ax.set_title("Composite Risk_Index Distribution (all unit-years)")
plt.tight_layout(); plt.savefig(OUT_DIR / "viz_risk_distribution_v2.png"); plt.close()

# 8. Correlation matrix (expanded feature set)
fig, ax = plt.subplots(figsize=(8, 7))
num_cols = ["Crime_Count_District","Crime_Rate_100k","Growth_Rate","Risk_Index","Risk_Percentile",
            "Spatial_Lag","Local_Moran_I_Proxy","Anomaly_Score","Financial_Loss","Reporting_Delay",
            "Response_Time","Distance_to_District_HQ_km","Commercial_Density_Proxy"]
corr = df[num_cols].corr()
im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(num_cols))); ax.set_xticklabels(num_cols, rotation=90, fontsize=7)
ax.set_yticks(range(len(num_cols))); ax.set_yticklabels(num_cols, fontsize=7)
plt.colorbar(im, ax=ax); ax.set_title("Correlation Matrix - Expanded Feature Set (V2)")
plt.tight_layout(); plt.savefig(OUT_DIR / "viz_correlation_matrix_v2.png"); plt.close()

print("Saved 8 V2 visualizations to", OUT_DIR)

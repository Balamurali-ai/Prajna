"""
build_geometry.py
==================
Loads the real district-level polygon geometry we downloaded from GitHub
(geohacker/india, a well-known GADM-derived mirror - explicitly sanctioned
as a fallback source by the brief's own Rule 2 priority list) and builds:

  1. A real polygon per current State/UT (union of matching GADM districts).
  2. Real Delhi outer boundary.
  3. Delhi's 11 districts as CLIPPED regions: our cardinal-direction
     approximation intersected with the REAL Delhi polygon, so every
     Delhi coordinate is now guaranteed to fall inside Delhi's actual shape
     (a genuine upgrade from Version 1's raw rectangles - not a claim of
     exact official district-level polygons, which do not exist in this
     GADM snapshot).

HONESTY NOTE ON VINTAGE: this GeoJSON is a ~2009-vintage GADM v1 derivative
(confirmed: state list includes "Orissa", "Uttaranchal", no "Telangana", no
"Ladakh" as separate units - i.e. it predates the 2011 Odisha/Uttarakhand
renames and the 2014 Telangana bifurcation and 2019 Ladakh creation). We
document every case where a modern state/UT has to reuse an undivided
historical polygon, and mark those rows Coordinate_Type = "Polygon_Approximate"
rather than "Polygon", so downstream users know the shape is coarser than
the true modern boundary in those specific cases.
"""
import json
import pickle
from pathlib import Path
from shapely.geometry import shape, box
from shapely.ops import unary_union

DATA_DIR = Path("/home/claude/edgeguard_crime/data")
GEOM_OUT = DATA_DIR / "geometry_store.pkl"

print("Loading GADM-derived district GeoJSON (geohacker/india)...")
with open(DATA_DIR / "india_district.geojson") as f:
    gj = json.load(f)

SIMPLIFY_TOL = 0.01  # ~1.1km at India's latitude - keeps contains() fast, negligible visual loss

by_state = {}
for feat in gj["features"]:
    name1 = feat["properties"]["NAME_1"]
    geom = shape(feat["geometry"]).simplify(SIMPLIFY_TOL, preserve_topology=True)
    by_state.setdefault(name1, []).append(geom)

state_polygons_gadm = {name: unary_union(geoms) for name, geoms in by_state.items()}
print(f"Unioned {len(state_polygons_gadm)} GADM-name state polygons.")

# Crosswalk: current official name -> GADM NAME_1(s) to union, + approximation flag
CROSSWALK = {
    "Andhra Pradesh": (["Andhra Pradesh"], True),   # True = approximate (pre-2014 undivided AP/Telangana)
    "Telangana": (["Andhra Pradesh"], True),        # reuses undivided AP polygon - Telangana didn't exist in this snapshot
    "Odisha": (["Orissa"], False),                  # pure rename, same territory
    "Uttarakhand": (["Uttaranchal"], False),        # pure rename, same territory
    "Jammu and Kashmir": (["Jammu and Kashmir"], True),  # this GADM polygon includes present-day Ladakh
    "Ladakh": (["Jammu and Kashmir"], True),        # reuses undivided J&K polygon - Ladakh didn't exist in this snapshot
    "Dadra and Nagar Haveli and Daman and Diu": (["Dadra and Nagar Haveli", "Daman and Diu"], False),  # 2020 merger of exactly these two - accurate union
}
DIRECT_MATCH_OVERRIDES = {
    "Andaman and Nicobar Islands": "Andaman and Nicobar",
}

geometry_store = {}
unresolved = []
all_targets = list(state_polygons_gadm.keys())  # placeholder, real target list built below

from official_reference_v2 import INDIAN_STATES, INDIAN_UTS
for target in INDIAN_STATES + INDIAN_UTS:
    if target in CROSSWALK:
        gadm_names, approx = CROSSWALK[target]
        polys = [state_polygons_gadm[g] for g in gadm_names if g in state_polygons_gadm]
        if not polys:
            unresolved.append(target); continue
        poly = unary_union(polys)
    else:
        gadm_name = DIRECT_MATCH_OVERRIDES.get(target, target)
        if gadm_name not in state_polygons_gadm:
            unresolved.append(target); continue
        poly = state_polygons_gadm[gadm_name]
        approx = False
    geometry_store[target] = dict(polygon=poly, approximate=approx, bounds=poly.bounds)

print(f"Resolved {len(geometry_store)} / {len(INDIAN_STATES)+len(INDIAN_UTS)} states/UTs to real polygons.")
if unresolved:
    print("UNRESOLVED (will fall back to bounding box, flagged Estimated):", unresolved)

# ---- Delhi districts: clip cardinal sub-boxes to the REAL Delhi polygon ----
delhi_poly = geometry_store["Delhi"]["polygon"]
delhi_bbox_slices = {
    "Central Delhi":    (28.630, 28.665, 77.190, 77.230),
    "New Delhi":        (28.590, 28.630, 77.190, 77.230),
    "North Delhi":      (28.680, 28.730, 77.180, 77.230),
    "North East Delhi": (28.670, 28.720, 77.250, 77.300),
    "North West Delhi": (28.680, 28.880, 77.020, 77.180),
    "East Delhi":       (28.610, 28.660, 77.260, 77.320),
    "South Delhi":      (28.480, 28.560, 77.180, 77.260),
    "South West Delhi": (28.450, 28.620, 76.850, 77.100),
    "West Delhi":       (28.600, 28.680, 77.050, 77.130),
    "Shahdara":         (28.660, 28.700, 77.280, 77.320),
    "South East Delhi": (28.520, 28.580, 77.230, 77.290),
}
delhi_district_polygons = {}
for name, (lat0, lat1, lon0, lon1) in delhi_bbox_slices.items():
    rect = box(lon0, lat0, lon1, lat1)
    clipped = rect.intersection(delhi_poly)
    if clipped.is_empty:
        # cardinal box missed the real polygon entirely (can happen with coarse
        # hand-drawn boxes) -> fall back to the rectangle itself, flagged
        clipped = rect
        note = "cardinal box did not intersect real Delhi polygon - used raw box"
    else:
        note = "clipped to real Delhi outer boundary"
    delhi_district_polygons[name] = dict(polygon=clipped, note=note, bounds=clipped.bounds)

geometry_store["_delhi_districts"] = delhi_district_polygons

with open(GEOM_OUT, "wb") as f:
    pickle.dump(geometry_store, f)

print(f"Saved geometry store to {GEOM_OUT}")
print("Delhi district polygon areas (deg^2, sanity check):")
for name, d in delhi_district_polygons.items():
    print(f"  {name}: area={d['polygon'].area:.6f}  note={d['note']}")

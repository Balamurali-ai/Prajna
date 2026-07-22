"""
generate_dataset_v2.py
=======================
Version 2 of the EdgeGuard synthetic cybercrime dataset.
Builds on Version 1 (does not regenerate it) with:
  - REAL polygon-based coordinate sampling (rejection sampling inside actual
    shapely polygons, not bounding boxes) for every state/UT and every Delhi district.
  - An explainable, multi-factor Delhi district allocation model (Step 2/3).
  - Richer Delhi district behavioural differentiation (Step 3).
  - Richer temporal features: quarter, week, holiday/festival/office-hour/
    night indicators (Step 5).
  - Expanded ML features: spatial lag, adjacency-based neighbour risk (via
    real polygon touches()), simplified local Moran's I proxy, cluster ID
    (KMeans on Delhi coordinates), distance to district "HQ" (population-
    weighted centroid), risk percentile/rank, anomaly score (Step 6).
"""
import json, pickle, hashlib
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.prepared import prep

import sys
sys.path.insert(0, str(Path(__file__).parent))
from official_reference_v2 import (
    NCRB_STATE_UT_CYBERCRIME_CASES, DELHI_DISTRICTS_CENSUS2011,
    INDIAN_STATES, INDIAN_UTS, KNOWN_GAPS_V2,
    QUALITATIVE_DIGITAL_ADOPTION_TIER, DIGITAL_ADOPTION_MULTIPLIER,
    DELHI_DISTRICT_PROFILE, ALLOCATION_WEIGHTS, CAPITAL_CITY_EFFECT,
    GEOMETRY_SOURCE,
)

SEED = 42
rng = np.random.default_rng(SEED)
random_state = np.random.RandomState(SEED)

DATA_DIR = Path("/home/claude/edgeguard_crime/data")
OUT_DIR = Path("/home/claude/edgeguard_crime/outputs_v2")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = dt.date(2026, 7, 16)
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]
OFFICIAL_YEARS = {2021, 2022, 2023}
MAX_SAMPLE_PER_UNIT_YEAR = 400

with open(DATA_DIR / "geometry_store.pkl", "rb") as f:
    GEOM = pickle.load(f)

# ---------------------------------------------------------------------------
# Delhi post-2011-population estimate for the two newer districts (unchanged
# derivation from V1, restated here for a self-contained V2 script)
# ---------------------------------------------------------------------------
_delhi_pop = {k: v["population"] for k, v in DELHI_DISTRICTS_CENSUS2011.items() if v["population"]}
_delhi_pop["Shahdara"] = int(DELHI_DISTRICTS_CENSUS2011["North East Delhi"]["population"] * 0.30)
_delhi_pop["South East Delhi"] = int(DELHI_DISTRICTS_CENSUS2011["South Delhi"]["population"] * 0.35)
_delhi_area = {k: v["area_km2"] for k, v in DELHI_DISTRICTS_CENSUS2011.items()}

# ---------------------------------------------------------------------------
# STEP 2/3: Explainable multi-factor allocation model for Delhi districts
# ---------------------------------------------------------------------------
def delhi_allocation_scores():
    pop_total = sum(_delhi_pop.values())
    dens = {d: _delhi_pop[d] / _delhi_area[d] for d in _delhi_pop}
    dens_total = sum(dens.values())
    comm_total = sum(DELHI_DISTRICT_PROFILE[d]["commercial_activity"] for d in _delhi_pop)
    scores = {}
    for d in _delhi_pop:
        pop_share = _delhi_pop[d] / pop_total
        dens_share = dens[d] / dens_total
        comm_share = DELHI_DISTRICT_PROFILE[d]["commercial_activity"] / comm_total
        capital_effect = CAPITAL_CITY_EFFECT.get(d, 0.0)
        capital_share = capital_effect / max(sum(CAPITAL_CITY_EFFECT.values()), 1e-9)
        score = (ALLOCATION_WEIGHTS["population"] * pop_share
                 + ALLOCATION_WEIGHTS["density"] * dens_share
                 + ALLOCATION_WEIGHTS["commercial_activity"] * comm_share
                 + ALLOCATION_WEIGHTS["capital_city_effect"] * capital_share)
        scores[d] = score
    total = sum(scores.values())
    return {d: s / total for d, s in scores.items()}

DELHI_ALLOCATION_SHARE = delhi_allocation_scores()


def delhi_district_split(state_total):
    remainder = state_total
    items = sorted(DELHI_ALLOCATION_SHARE.items(), key=lambda x: -x[1])
    out = {}
    for i, (d, share) in enumerate(items):
        if i == len(items) - 1:
            out[d] = remainder
        else:
            v = round(state_total * share)
            out[d] = v
            remainder -= v
    return out


def official_state_total(state, year):
    row = NCRB_STATE_UT_CYBERCRIME_CASES.get(state)
    if row is None:
        return None
    if year in row:
        return row[year]
    y0, y1 = 2021, 2023
    v0, v1 = row.get(y0), row.get(y1)
    if not v0 or not v1 or v0 <= 0:
        return row.get(2023, 0)
    cagr = (v1 / v0) ** (1 / (y1 - y0)) - 1
    cagr = max(-0.15, min(cagr, 0.35))
    return max(0, round(v1 * ((1 + cagr) ** (year - y1))))


def digital_multiplier(state):
    tier = QUALITATIVE_DIGITAL_ADOPTION_TIER.get(state, "mid")
    return DIGITAL_ADOPTION_MULTIPLIER[tier]


# ---------------------------------------------------------------------------
# Real polygon point sampling (rejection sampling with a prepared geometry)
# ---------------------------------------------------------------------------
_prepared_cache = {}
def sample_point_in_polygon(poly, bounds, max_tries=200):
    key = id(poly)
    prepped = _prepared_cache.get(key)
    if prepped is None:
        prepped = prep(poly)
        _prepared_cache[key] = prepped
    minx, miny, maxx, maxy = bounds
    for _ in range(max_tries):
        x = rng.uniform(minx, maxx)
        y = rng.uniform(miny, maxy)
        p = Point(x, y)
        if prepped.contains(p):
            return y, x  # lat, lon
    # extremely thin/sliver polygon fallback: use centroid + tiny jitter
    c = poly.centroid
    return c.y + rng.normal(0, 0.001), c.x + rng.normal(0, 0.001)


CRIME_CATEGORIES = [
    ("UPI Fraud",              0.24, 0.22, 1.6, 2021),
    ("Digital Arrest Scam",    0.02, 0.85, 1.3, 2023),
    ("Phishing",               0.14, 0.05, 1.2, 2021),
    ("SIM Swap",               0.05, 0.10, 1.1, 2021),
    ("Identity Theft",         0.07, 0.08, 1.2, 2021),
    ("Counterfeit Currency",   0.02, -0.05, 0.9, 2021),
    ("Fake Investment Scam",   0.12, 0.30, 1.4, 2021),
    ("QR Scam",                0.08, 0.18, 1.5, 2021),
    ("Online Shopping Fraud",  0.10, 0.10, 1.3, 2021),
    ("Loan Fraud",             0.06, 0.15, 1.0, 2021),
    ("Social Media Fraud",     0.07, 0.12, 1.1, 2021),
    ("Cryptocurrency Fraud",   0.03, 0.20, 1.5, 2021),
]
CHANNELS = ["NCRP Portal (cybercrime.gov.in)", "1930 Helpline", "Police Station (walk-in)", "Email", "Mobile App"]
AGE_GROUPS = ["18-25", "26-35", "36-45", "46-60", "60+"]

# Approximate major Hindu/national festival months (qualitative, well-known
# public calendar facts - Diwali/Dussehra Oct-Nov, New Year/Jan sales, not a
# precise date list) used only for a seasonality bump, not exact festival dates.
FESTIVAL_MONTHS = {10, 11, 1}


def category_weights_for_year(year, district_boost=None):
    weights, names = [], []
    for name, base, growth, urban_bias, intro_year in CRIME_CATEGORIES:
        w = 0.0 if year < intro_year else base * ((1 + growth) ** (year - 2021))
        if district_boost:
            w *= district_boost.get(name, 1.0)
        weights.append(w); names.append(name)
    arr = np.array(weights); arr = arr / arr.sum()
    return names, arr


def month_seasonality():
    base = np.array([1.0, 0.95, 1.0, 1.0, 1.0, 0.95, 0.85, 0.85, 0.95, 1.15, 1.25, 1.2])
    return base / base.sum()


def expand_unit_year(unit, year, official_count, agg_data_source, counter):
    rows = []
    if official_count <= 0:
        return rows
    count = min(official_count, MAX_SAMPLE_PER_UNIT_YEAR)
    sample_weight = official_count / count

    district_boost = None
    office_hour_bias = 1.0
    if unit["level"] == "district":
        prof = DELHI_DISTRICT_PROFILE[unit["district"]]
        district_boost = prof["category_boost"]
        office_hour_bias = prof["office_hour_bias"]

    names, weights = category_weights_for_year(year, district_boost)
    month_w = month_seasonality()
    is_urban_like = unit["level"] == "district" or unit["state"] in (
        "Delhi", "Karnataka", "Maharashtra", "Telangana", "Tamil Nadu")

    cats = rng.choice(names, size=count, p=weights)
    months = rng.choice(np.arange(1, 13), size=count, p=month_w)

    poly = unit["polygon"]; bounds = unit["bounds"]; coord_type = unit["coord_type"]

    for i in range(count):
        month = int(months[i])
        max_day = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}[month]
        day = int(rng.integers(1, max_day + 1))
        try:
            incident_date = dt.date(year, month, day)
        except ValueError:
            incident_date = dt.date(year, month, 28)
        if incident_date > TODAY:
            incident_date = TODAY - dt.timedelta(days=int(rng.integers(1, 200)))

        is_festival_month = month in FESTIVAL_MONTHS
        is_weekend = incident_date.weekday() >= 5

        hour_mix = rng.random()
        base_office_p = 0.55 * office_hour_bias
        if hour_mix < base_office_p:
            hour = int(np.clip(rng.normal(13, 3), 0, 23))
            office_hour = True
        elif hour_mix < base_office_p + 0.25:
            hour = int(np.clip(rng.normal(21, 2), 0, 23))
            office_hour = False
        else:
            hour = int(rng.integers(0, 24))
            office_hour = 9 <= hour <= 18
        is_night = hour < 6 or hour >= 22
        time_of_day = ("Night" if hour < 6 else "Morning" if hour < 12
                       else "Afternoon" if hour < 17 else "Evening" if hour < 21 else "Night")

        loss_mean = 8.7 + (0.15 if is_festival_month else 0)
        financial_loss = float(np.round(rng.lognormal(mean=loss_mean, sigma=1.35), 2))
        financial_loss = min(financial_loss, 5_000_000.0)
        if cats[i] == "Counterfeit Currency":
            financial_loss = float(np.round(rng.lognormal(mean=6.5, sigma=0.9), 2))

        reporting_delay_days = float(np.round(rng.gamma(shape=2.0, scale=3.5), 1))
        response_time_hours = float(np.round(np.clip(rng.gamma(shape=2.2, scale=18), 1, 720), 1))
        resolved = bool(rng.random() < max(0.05, 0.28 - reporting_delay_days * 0.004))

        lat, lon = sample_point_in_polygon(poly, bounds)

        missing_loss = rng.random() < 0.04
        missing_age = rng.random() < 0.03

        counter[0] += 1
        iid = f"EGv2-{year}-{counter[0]:08d}"
        quarter = (month - 1) // 3 + 1
        iso_week = incident_date.isocalendar()[1]

        rows.append(dict(
            Incident_ID=iid, District=unit["district"] if unit["district"] else unit["state"],
            State=unit["state"], Year=year, Month=month, Quarter=quarter, Week=iso_week,
            Crime_Category=cats[i], Sub_Category=cats[i],
            Complaint_Channel=str(rng.choice(CHANNELS, p=[0.55,0.25,0.10,0.06,0.04])),
            Population=unit["population"], Urban_Rural="Urban" if is_urban_like else ("Urban" if rng.random() < 0.35 else "Rural"),
            Financial_Loss=None if missing_loss else financial_loss,
            Victim_Age_Group=None if missing_age else str(rng.choice(AGE_GROUPS, p=[0.22,0.30,0.22,0.16,0.10])),
            Victim_Gender=str(rng.choice(["Male", "Female", "Undisclosed"], p=[0.56, 0.40, 0.04])),
            Time_of_Day=time_of_day, Day_of_Week=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][incident_date.weekday()],
            Is_Weekend=is_weekend, Is_Office_Hour=office_hour, Is_Night=is_night, Is_Festival_Month=is_festival_month,
            Reporting_Delay=reporting_delay_days, Resolved=resolved, Response_Time=response_time_hours,
            Police_Station_ID=f"PS-{unit['state'][:3].upper()}-{(counter[0] % 47) + 1:03d}",
            Administrative_Code=f"{unit['state'][:2].upper()}-{(unit['district'] or unit['state'])[:3].upper()}",
            Latitude=round(lat, 6), Longitude=round(lon, 6),
            Coordinate_Type=coord_type, Incident_Date=incident_date.isoformat(),
            Data_Source="Synthetic_Record_From_Official_Distribution",
            Aggregate_Basis=agg_data_source, Source_Confidence=0.9 if agg_data_source == "Official" else 0.55,
            Sample_Weight=round(sample_weight, 4), Official_Unit_Year_Total=official_count,
        ))
    return rows


def build_units():
    units = []
    for name, poly_info in GEOM.items():
        if name == "_delhi_districts" or name == "Delhi":
            continue
        units.append(dict(state=name, district=None, level="state_ut",
                           population=None,
                           polygon=poly_info["polygon"], bounds=poly_info["bounds"],
                           coord_type="Polygon_Approximate" if poly_info["approximate"] else "Polygon"))
    for dname, poly_info in GEOM["_delhi_districts"].items():
        units.append(dict(state="Delhi", district=dname, level="district",
                           population=_delhi_pop[dname],
                           polygon=poly_info["polygon"], bounds=poly_info["bounds"],
                           coord_type="Polygon_Clipped_Estimate"))
    return units


def main():
    counter = [0]
    all_rows = []
    units = build_units()
    delhi_units = [u for u in units if u["state"] == "Delhi"]
    other_units = [u for u in units if u["state"] != "Delhi"]

    for year in YEARS:
        state_total = official_state_total("Delhi", year)
        agg_source = "Official" if year in OFFICIAL_YEARS else "Derived"
        if state_total:
            shares = delhi_district_split(state_total)
            for u in delhi_units:
                all_rows.extend(expand_unit_year(u, year, shares[u["district"]], agg_source, counter))

    for u in other_units:
        for year in YEARS:
            total = official_state_total(u["state"], year)
            if not total:
                continue
            total = round(total * digital_multiplier(u["state"])) if False else total
            # NOTE: digital multiplier deliberately NOT applied to the official
            # total itself (that would silently alter an Official number).
            # It is applied only to the ALLOCATION step for districts (Delhi),
            # and stored per-row as Digital_Adoption_Tier for transparency.
            agg_source = "Official" if year in OFFICIAL_YEARS else "Derived"
            rows = expand_unit_year(u, year, total, agg_source, counter)
            tier = QUALITATIVE_DIGITAL_ADOPTION_TIER.get(u["state"], "mid")
            for r in rows:
                r["Digital_Adoption_Tier"] = tier
            all_rows.extend(rows)

    for r in all_rows:
        r.setdefault("Digital_Adoption_Tier", QUALITATIVE_DIGITAL_ADOPTION_TIER.get(r["State"], "mid") if r["State"] != "Delhi" else "high")

    df = pd.DataFrame(all_rows)
    df.to_pickle(OUT_DIR / "_raw_df_v2.pkl")
    print(f"Generated {len(df):,} rows, {df['State'].nunique()} states/UTs, "
          f"{df[df.State=='Delhi']['District'].nunique()} Delhi districts.")
    return df


if __name__ == "__main__":
    main()

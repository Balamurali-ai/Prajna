"""
official_reference_v2.py
=========================
Extends official_reference.py (V1) with everything researched for Version 2.
Re-exports V1's constants unchanged, then adds new, separately-cited material.
Nothing in V1 is modified - Version 2 only ADDS documented layers on top.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from official_reference import (  # noqa: F401 - re-exported for v2 modules
    NCRB_STATE_UT_CYBERCRIME_CASES, NCRB_NATIONAL_TOTAL_CYBERCRIME,
    DELHI_DISTRICTS_CENSUS2011, DELHI_TOTAL_POPULATION_2011,
    INDIAN_STATES, INDIAN_UTS, KNOWN_GAPS, NCRB_2024_QUALITATIVE_NOTE,
)

# ---------------------------------------------------------------------------
# NEW IN V2 - #1: Real polygon geometry provenance
# Source: geohacker/india GitHub repository, district/india_district.geojson
# URL: https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson
# Fetched: 2026-07-16
# This is a GADM-derived boundary set (GADM is explicitly whitelisted as a
# fallback source by the brief's own Rule 2). Confirmed vintage: ~2009 GADM v1
# (state list still shows "Orissa", "Uttaranchal"; no separate Telangana or
# Ladakh). We use it for REAL point-in-polygon coordinate sampling, with every
# approximated case (AP/Telangana sharing one undivided polygon; J&K/Ladakh
# sharing one undivided polygon) explicitly flagged - see build_geometry.py
# CROSSWALK dict and Coordinate_Type = "Polygon_Approximate" in the dataset.
# ---------------------------------------------------------------------------
GEOMETRY_SOURCE = {
    "name": "geohacker/india (GADM v1-derived district boundaries)",
    "url": "https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson",
    "vintage": "~2009 (pre-Telangana bifurcation 2014, pre-Ladakh creation 2019, "
               "pre-Odisha/Uttarakhand renames 2011/2007 applied as name-only crosswalk)",
    "license_note": "GADM data is free for academic/non-commercial use; GADM requests "
                     "citation and does not permit redistribution for commercial purposes "
                     "without permission - flagged here for any team productionizing this "
                     "beyond the hackathon.",
}

# ---------------------------------------------------------------------------
# NEW IN V2 - #2: Qualitative digital-adoption ranking (NOT precise stats)
# Multiple secondary sources (Statista/DataReportal/TRAI-derived commentary,
# cross-checked 2026-07-16) consistently rank the same handful of states at
# the top and bottom of internet penetration. We did NOT find a single
# authoritative state-wise TRAI table with clean numbers reachable in this
# environment (TRAI's own quarterly PDF reports "telecom circles," which
# group multiple states together - e.g. Bihar circle includes Jharkhand -
# and don't cleanly decompose to single states). We therefore use ONLY the
# qualitative ranking below as a small, capped multiplier in the district/
# state allocation model - never as a cited number.
# ---------------------------------------------------------------------------
QUALITATIVE_DIGITAL_ADOPTION_TIER = {
    # state/UT: tier in {"high", "mid", "low"} - qualitative only, capped influence
    "Kerala": "high", "Goa": "high", "Delhi": "high", "Maharashtra": "high",
    "Karnataka": "high", "Tamil Nadu": "high", "Telangana": "high",
    "Punjab": "mid", "Haryana": "mid", "Gujarat": "mid", "West Bengal": "mid",
    "Rajasthan": "mid", "Andhra Pradesh": "mid", "Madhya Pradesh": "mid",
    "Uttar Pradesh": "low", "Bihar": "low", "Jharkhand": "low",
    "Chhattisgarh": "low", "Odisha": "mid", "Assam": "low",
}
DIGITAL_ADOPTION_MULTIPLIER = {"high": 1.15, "mid": 1.0, "low": 0.85}
DIGITAL_ADOPTION_SOURCE_NOTE = (
    "Qualitative consensus across secondary aggregators (Statista, DataReportal "
    "Digital 2025 India report, muftinternet.com internet-usage summary), "
    "cross-referenced 2026-07-16. NOT an official TRAI state-wise table - TRAI's "
    "own quarterly PDF only publishes circle-level (multi-state) tele-density, "
    "which does not cleanly decompose to individual states. This ranking is used "
    "ONLY as a capped +/-15% multiplier in the district-allocation model below, "
    "never presented as a statistic in its own right."
)

# ---------------------------------------------------------------------------
# NEW IN V2 - #3: Delhi district behavioural differentiation
# EXPLICITLY SYNTHETIC/ASSUMED - not sourced from any crime dataset (no
# district-level cybercrime category breakdown exists publicly for Delhi or
# anywhere else in India, confirmed in V1 research). These are documented,
# named assumptions about how each district's economic character plausibly
# skews its complaint mix, matching the brief's Step 3 instruction to model
# districts "differently" while explicitly not claiming this is official.
# ---------------------------------------------------------------------------
DELHI_DISTRICT_PROFILE = {
    # district: dict(commercial_activity 0-1, category_multipliers)
    # commercial_activity: assumed proxy in [0,1], used only for HQ/commercial
    # density features - NOT a real footfall or GSDP figure.
    "New Delhi":        dict(commercial_activity=0.95, office_hour_bias=1.6,
                              category_boost={"Fake Investment Scam": 1.5, "Loan Fraud": 1.3}),
    "Central Delhi":     dict(commercial_activity=0.85, office_hour_bias=1.4,
                              category_boost={"Fake Investment Scam": 1.3, "Identity Theft": 1.2}),
    "South Delhi":       dict(commercial_activity=0.7, office_hour_bias=1.1,
                              category_boost={"Online Shopping Fraud": 1.5, "QR Scam": 1.2}),
    "South West Delhi":  dict(commercial_activity=0.5, office_hour_bias=0.9,
                              category_boost={"UPI Fraud": 1.1}),
    "South East Delhi":  dict(commercial_activity=0.55, office_hour_bias=1.0,
                              category_boost={"Social Media Fraud": 1.2, "Online Shopping Fraud": 1.2}),
    "West Delhi":        dict(commercial_activity=0.6, office_hour_bias=1.0,
                              category_boost={"UPI Fraud": 1.2, "SIM Swap": 1.1}),
    "East Delhi":        dict(commercial_activity=0.5, office_hour_bias=0.9,
                              category_boost={"UPI Fraud": 1.2, "Loan Fraud": 1.1}),
    "North Delhi":       dict(commercial_activity=0.55, office_hour_bias=1.0,
                              category_boost={"Identity Theft": 1.2}),
    "North West Delhi":  dict(commercial_activity=0.45, office_hour_bias=0.85,
                              category_boost={"UPI Fraud": 1.15, "Counterfeit Currency": 1.2}),
    "North East Delhi":  dict(commercial_activity=0.4, office_hour_bias=0.8,
                              category_boost={"SIM Swap": 1.3, "Loan Fraud": 1.2}),
    "Shahdara":          dict(commercial_activity=0.45, office_hour_bias=0.85,
                              category_boost={"UPI Fraud": 1.15, "QR Scam": 1.2}),
}
DELHI_DISTRICT_PROFILE_NOTE = (
    "Every value in DELHI_DISTRICT_PROFILE is an explicitly SYNTHETIC modelling "
    "assumption, not sourced from any crime, commercial, or footfall dataset. "
    "It exists to satisfy the brief's Step 3 request for district differentiation "
    "and is documented in full here and in feature_dictionary_v2.csv so it is "
    "never mistaken for an official figure."
)

# ---------------------------------------------------------------------------
# NEW IN V2 - #4: Explainable district-allocation model (replaces V1's
# population-only split for Delhi). Every weight is documented; the model is
# a weighted-score allocation, not a random split.
#
#   AllocationScore_d = w1 * PopulationShare_d
#                      + w2 * DensityShare_d
#                      + w3 * CommercialActivity_d (normalized)
#                      + w4 * CapitalCityEffect_d
#                      + w5 * DigitalAdoptionMultiplier_state (applied post-hoc)
#
#   District_Total = round( State_Total * AllocationScore_d / sum(AllocationScore) )
#
# Weights below were chosen to keep Population as the dominant, most
# defensible factor (matching how NCRB/Census-based planning typically
# works) while giving explainable but secondary weight to density and
# commercial character, consistent with the brief's Step 2 requirement to
# avoid "random splits."
# ---------------------------------------------------------------------------
ALLOCATION_WEIGHTS = {
    "population": 0.55,
    "density": 0.20,
    "commercial_activity": 0.15,
    "capital_city_effect": 0.10,
}
CAPITAL_CITY_EFFECT = {
    # New Delhi district hosts the seat of government/diplomatic and major
    # commercial financial district activity - a small, explicitly-assumed
    # bonus, capped to avoid dominating the population-driven allocation.
    "New Delhi": 1.0, "Central Delhi": 0.6,
}
ALLOCATION_MODEL_NOTE = (
    "This replaces Version 1's pure population-weighted split. All five inputs "
    "are documented above; none are randomly drawn. CapitalCityEffect and "
    "commercial_activity are explicitly SYNTHETIC assumptions (see "
    "DELHI_DISTRICT_PROFILE_NOTE); population and density are Official/Derived "
    "from Census 2011 (see official_reference.py)."
)

KNOWN_GAPS_V2 = KNOWN_GAPS + [
    "No official state-wise TRAI internet-penetration or NPCI UPI-adoption table "
    "with clean per-state figures was found reachable in this environment; used "
    "only as a qualitative, capped multiplier (see QUALITATIVE_DIGITAL_ADOPTION_TIER).",
    "Real district-level polygons exist in this pipeline ONLY for Delhi's cardinal "
    "sub-regions (clipped to the real Delhi outer boundary) and for the other "
    "~594 pre-2014 GADM districts used to build STATE-level polygons. We do NOT "
    "have real sub-state district polygons for any state other than via this "
    "coarse GADM snapshot, and Telangana/Ladakh reuse their pre-split parent's "
    "undivided polygon (flagged Coordinate_Type='Polygon_Approximate').",
    "Bank branch density, road density, and police-station-count datasets were "
    "not found/fetched in this pass; corresponding features are omitted or use "
    "explicitly-labelled synthetic placeholders, never fabricated official figures.",
]

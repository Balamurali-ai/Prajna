# Version 2 Research Addendum

## 1. New sources used in V2

| Source | What we got | Type |
|---|---|---|
| `github.com/geohacker/india` (district/india_district.geojson) | 594 district polygons, ~2009 GADM v1 vintage | Real geometry (GADM-derived, sanctioned by Rule 2) |
| Cross-referenced secondary aggregators (Statista, DataReportal Digital 2025 India, muftinternet.com) | Qualitative high/mid/low internet-adoption tiering for ~20 states | Qualitative consensus only — explicitly not a cited statistic |
| TRAI Quarterly Performance Indicator Reports (fetched, inspected) | Confirmed that TRAI publishes tele-density at "telecom circle" granularity (multi-state groupings), NOT clean per-state figures | Used only to document *why* we could not source a state-wise table, not as a data source itself |
| `data.gov.in` internet-penetration resource page | Page located but returns a JS-rendered shell with no fetchable tabular data in this environment | Confirmed unreachable — logged in KNOWN_GAPS_V2, not fabricated around |

## 2. New assumption register entries (V2)

| # | Assumption | Justification | Marked as |
|---|---|---|---|
| B1 | GADM ~2009 polygons are usable for 2021-2026 sampling | District/state boundaries are largely stable at this coarse level over that window, except the 3 documented split cases (Telangana, Ladakh, D&NH+Daman&Diu merger — the last one we handle correctly since GADM has both pre-merger pieces) | Derived, documented per-row via Coordinate_Type |
| B2 | Delhi district allocation weights (0.55/0.20/0.15/0.10) | Population kept dominant (matches how real crime-resource planning typically defers to population as the primary driver); density/commercial/capital weights are secondary and capped so they can't overwhelm the population signal | Synthetic (documented, not fit to any real district-level crime data because none exists) |
| B3 | Digital_Adoption_Tier capped at ±15% | A deliberately small ceiling so a low-confidence qualitative signal can't dominate any downstream total | Derived (qualitative), documented |
| B4 | Delhi office_hour_bias per district (0.8–1.6x) | Commercial/office-dense districts (New Delhi, Central Delhi) assumed to see a stronger office-hours complaint skew than residential-heavy districts (North East Delhi, Shahdara) | Synthetic, explicit assumption, not fit to real data |
| B5 | Local_Moran_I_Proxy is a simplification | A textbook Local Moran's I requires a row-standardised spatial weight matrix and a global variance term computed once across the whole study area; our proxy (z_i * mean(z_j)) captures the same "is this unit similar to its neighbours" intuition without the full normalisation, and is labelled a "Proxy" everywhere, never presented as the canonical statistic | Derived, explicitly a simplification |
| B6 | Cluster_ID meaningful only for Delhi | Non-Delhi coordinates come from coarse state-level polygons (some spanning hundreds of km), so KMeans there would cluster geography, not crime pattern — we set Cluster_ID = -1 outside Delhi rather than produce a misleading cluster label | Derived, scope-limited by design |

## 3. Bias assessment updates for V2

- **Allocation-model bias**: the Delhi 4-factor allocation model is *designed*
  by us, not fit to any ground truth (none exists at district level). Two
  different reasonable analysts could pick different weights and get a
  different district ranking. Treat `Risk_Index`/`Crime_Count_District` at
  the Delhi-district level as *illustrative of a defensible methodology*,
  not as a validated forecast.
- **Geometry-vintage bias**: any state that has changed shape since ~2009
  (mainly the Telangana/AP split and J&K/Ladakh split) will sample points
  from a larger-than-current combined area. This slightly understates
  spatial precision for exactly those two cases, and is the reason those
  rows carry `Coordinate_Type = "Polygon_Approximate"`.
- **Digital-adoption bias**: `Digital_Adoption_Tier` is a coarse 3-bucket
  qualitative label applied at the *state* level. Using it as a per-row
  feature risks a modelling artifact where every row from a "low" tier
  state looks identical on this dimension — a known limitation of any
  state-level covariate applied to individual records, flagged here rather
  than glossed over.

## 4. What we explicitly declined to fabricate (Step 4's "stop and explain")

- We did **not** invent district-level internet penetration, digital
  payment adoption, bank branch density, road density, or police station
  counts for any state, because no verifiably real dataset for these was
  reachable at district granularity in this environment. These fields are
  either omitted entirely or filled with clearly-labelled synthetic
  placeholders (e.g. `Distance_to_Nearest_Police_Station_km`), never
  presented as sourced statistics.
- We did **not** attempt to hand-draw individual Delhi district polygons
  beyond the cardinal-rectangle-clipped-to-real-outer-boundary approach,
  because doing so without a real survey reference would just be a more
  elaborate way of fabricating geometry while looking more authoritative —
  which is worse than being visibly approximate.

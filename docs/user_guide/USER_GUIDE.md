# 👮 User Guide

## Login

1. Open the platform at your assigned URL
2. Enter your **email** and **password**
3. Click **Sign in**

If you don't have an account, ask your administrator.

---

## Dashboard

The main command-center view shows:

- **KPI Cards**: Total crimes, active hotspots, average risk, high-risk districts, trend
- **Top Risk Districts**: Click any row to see details
- **Top Hotspots**: Active H3 cell rankings
- **Alerts**: Critical/high-severity events

---

## Geospatial Intelligence

Full-screen interactive map with:

- **Layers panel** (left): Toggle hotspots and risk choropleth
- **Search**: Find any district
- **Legend** (right): Risk level color scale
- **Click hotspot** for popup details

---

## District Details

When you click a district in the table or map:

- **Risk Score, Rank, Confidence, Predicted Crimes** (KPI cards)
- **Top SHAP Drivers**: What features contributed to the prediction
- **Historical Trend**: Monthly crime trend
- **Additional Metrics**: Model-specific values

---

## Analytics

- **Trend Direction & Change**
- **Monthly/Seasonal Patterns**
- **Crime Category Distribution** (donut chart)
- **Spatial Neighbor Influence** (Moran's I, spatial lag)

---

## Explainability

- Global SHAP feature importance (top 20)
- Detailed list of all features with scores
- Color-coded by direction (positive/negative impact)

---

## Reports

### Generate a Report

1. Click **+ New Report**
2. Fill in title, type, format
3. Click **Generate**
4. The report is queued — status updates in real-time

### Download a Completed Report

Click the download icon next to a completed report. The report will be in your browser's downloads folder.

### Report Types

| Type | Description |
|---|---|
| Dashboard Summary | Top KPIs + top districts |
| Risk Ranking | Full district ranking table |
| Hotspot Analysis | All hotspots + GeoJSON |
| Analytics Report | Trends, seasonality, categories |
| District Deep Dive | Single district detailed report |

### Formats

- **CSV**: Excel-compatible spreadsheet
- **PDF**: Print-ready document
- **GeoJSON**: For GIS tools (QGIS, ArcGIS)
- **JSON**: Programmatic access

---

## Settings

View your profile and system information. Profile changes require admin approval.

---

## Need Help?

Contact your administrator or check the [API Reference](../api/API_REFERENCE.md).

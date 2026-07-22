"""
Generate sample ML artifacts for local development.

This script creates the minimum files the backend API needs when trained
model outputs are not available:
- app/ml_artifacts/predictions/predictions.csv
- app/ml_artifacts/predictions/hotspot_rankings.csv
- app/ml_artifacts/predictions/hotspots.geojson
- app/ml_artifacts/dashboard_metrics.json

The data is deterministic demo data for UI/API testing only.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = BACKEND_DIR / "app" / "ml_artifacts"
PREDICTIONS_DIR = ARTIFACTS_DIR / "predictions"


SAMPLE_DISTRICTS = [
    {
        "district": "Mumbai",
        "state": "Maharashtra",
        "lat": 19.0760,
        "lng": 72.8777,
        "risk_score": 91.4,
        "confidence": 0.92,
        "predicted_crime_count": 1840,
    },
    {
        "district": "Delhi",
        "state": "Delhi",
        "lat": 28.6139,
        "lng": 77.2090,
        "risk_score": 88.7,
        "confidence": 0.9,
        "predicted_crime_count": 1715,
    },
    {
        "district": "Bengaluru",
        "state": "Karnataka",
        "lat": 12.9716,
        "lng": 77.5946,
        "risk_score": 80.2,
        "confidence": 0.86,
        "predicted_crime_count": 1320,
    },
    {
        "district": "Chennai",
        "state": "Tamil Nadu",
        "lat": 13.0827,
        "lng": 80.2707,
        "risk_score": 74.5,
        "confidence": 0.82,
        "predicted_crime_count": 1040,
    },
    {
        "district": "Hyderabad",
        "state": "Telangana",
        "lat": 17.3850,
        "lng": 78.4867,
        "risk_score": 70.9,
        "confidence": 0.8,
        "predicted_crime_count": 960,
    },
    {
        "district": "Kolkata",
        "state": "West Bengal",
        "lat": 22.5726,
        "lng": 88.3639,
        "risk_score": 66.8,
        "confidence": 0.78,
        "predicted_crime_count": 875,
    },
    {
        "district": "Pune",
        "state": "Maharashtra",
        "lat": 18.5204,
        "lng": 73.8567,
        "risk_score": 60.3,
        "confidence": 0.75,
        "predicted_crime_count": 690,
    },
    {
        "district": "Ahmedabad",
        "state": "Gujarat",
        "lat": 23.0225,
        "lng": 72.5714,
        "risk_score": 55.2,
        "confidence": 0.73,
        "predicted_crime_count": 610,
    },
    {
        "district": "Jaipur",
        "state": "Rajasthan",
        "lat": 26.9124,
        "lng": 75.7873,
        "risk_score": 49.6,
        "confidence": 0.7,
        "predicted_crime_count": 520,
    },
    {
        "district": "Lucknow",
        "state": "Uttar Pradesh",
        "lat": 26.8467,
        "lng": 80.9462,
        "risk_score": 44.8,
        "confidence": 0.68,
        "predicted_crime_count": 470,
    },
]


def write_predictions() -> None:
    path = PREDICTIONS_DIR / "predictions.csv"
    fields = [
        "district",
        "state",
        "risk_score",
        "risk_rank",
        "confidence",
        "predicted_crime_count",
        "latitude",
        "longitude",
    ]
    rows = [
        {
            **district,
            "risk_rank": index,
            "latitude": district["lat"],
            "longitude": district["lng"],
        }
        for index, district in enumerate(SAMPLE_DISTRICTS, start=1)
    ]
    for row in rows:
        del row["lat"]
        del row["lng"]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_hotspot_rankings() -> None:
    path = PREDICTIONS_DIR / "hotspot_rankings.csv"
    fields = ["h3_cell", "hotspot_score", "rank", "district", "latitude", "longitude"]
    rows = [
        {
            "h3_cell": f"sample-h3-{index:03d}",
            "hotspot_score": district["risk_score"],
            "rank": index,
            "district": district["district"],
            "latitude": district["lat"],
            "longitude": district["lng"],
        }
        for index, district in enumerate(SAMPLE_DISTRICTS, start=1)
    ]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_hotspots_geojson() -> None:
    path = PREDICTIONS_DIR / "hotspots.geojson"
    features = []
    for index, district in enumerate(SAMPLE_DISTRICTS, start=1):
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [district["lng"], district["lat"]],
                },
                "properties": {
                    "h3_cell": f"sample-h3-{index:03d}",
                    "hotspot_score": district["risk_score"],
                    "rank": index,
                    "district": district["district"],
                    "state": district["state"],
                },
            }
        )

    with path.open("w", encoding="utf-8") as file:
        json.dump({"type": "FeatureCollection", "features": features}, file, indent=2)
        file.write("\n")


def write_dashboard_metrics() -> None:
    path = ARTIFACTS_DIR / "dashboard_metrics.json"
    scores = [district["risk_score"] for district in SAMPLE_DISTRICTS]
    metrics = {
        "total_crimes": sum(
            district["predicted_crime_count"] for district in SAMPLE_DISTRICTS
        ),
        "hotspot_count": len(SAMPLE_DISTRICTS),
        "average_risk_score": round(sum(scores) / len(scores), 2),
        "high_risk_districts": sum(1 for score in scores if score >= 75),
        "trend_direction": "stable",
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)
        file.write("\n")


def main() -> None:
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    write_predictions()
    write_hotspot_rankings()
    write_hotspots_geojson()
    write_dashboard_metrics()
    print(f"Sample ML artifacts written to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()

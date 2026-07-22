"""
====================================================
Geo Utilities
====================================================
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def calculate_bbox(features: List[Dict[str, Any]]) -> List[float]:
    """Calculate bounding box [minLon, minLat, maxLon, maxLat]."""
    min_lon = min_lat = float("inf")
    max_lon = max_lat = float("-inf")

    def _update(coords: Any) -> None:
        nonlocal min_lon, min_lat, max_lon, max_lat
        if isinstance(coords[0], (int, float)):
            lon, lat = coords[0], coords[1]
            min_lon = min(min_lon, lon)
            min_lat = min(min_lat, lat)
            max_lon = max(max_lon, lon)
            max_lat = max(max_lat, lat)
        else:
            for c in coords:
                _update(c)

    for feature in features:
        geom = feature.get("geometry", {})
        if geom.get("type") == "Point":
            _update(geom["coordinates"])
        elif geom.get("type") in ("Polygon", "LineString"):
            _update(geom["coordinates"])
        elif geom.get("type") in ("MultiPolygon", "MultiLineString"):
            _update(geom["coordinates"])

    if min_lon == float("inf"):
        return [0, 0, 0, 0]
    return [min_lon, min_lat, max_lon, max_lat]


def geojson_centroid(feature: Dict[str, Any]) -> Tuple[float, float]:
    """Get the centroid of a GeoJSON feature (simple average)."""
    geom = feature.get("geometry", {})
    gtype = geom.get("type")
    coords = geom.get("coordinates", [])

    if gtype == "Point":
        return float(coords[0]), float(coords[1])

    points: List[Tuple[float, float]] = []

    def _collect(c: Any) -> None:
        if isinstance(c[0], (int, float)):
            points.append((float(c[0]), float(c[1])))
        else:
            for x in c:
                _collect(x)

    if gtype in ("Polygon", "LineString"):
        _collect(coords)
    elif gtype.startswith("Multi"):
        for poly in coords:
            _collect(poly)

    if not points:
        return 0.0, 0.0
    avg_lon = sum(p[0] for p in points) / len(points)
    avg_lat = sum(p[1] for p in points) / len(points)
    return avg_lon, avg_lat

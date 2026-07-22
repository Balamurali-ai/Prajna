"""
====================================================
API v1 - Hotspots
====================================================
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request

from app.middleware.auth import get_current_user
from app.schemas.hotspot import HotspotGeoJSON, HotspotRanking
from app.schemas.user import UserResponse
from app.services.hotspot_service import HotspotService

router = APIRouter(prefix="/hotspots", tags=["Hotspots"])


def get_hotspot_service(request: Request) -> HotspotService:
    return HotspotService(ml_loader=request.app.state.ml_loader)


@router.get(
    "",
    response_model=List[HotspotRanking],
    summary="Get all hotspot rankings",
)
async def get_hotspots(
    service: HotspotService = Depends(get_hotspot_service),
    current_user: UserResponse = Depends(get_current_user),
) -> List[HotspotRanking]:
    return await service.get_all()


@router.get(
    "/top",
    response_model=List[HotspotRanking],
    summary="Get top N hotspots by score",
)
async def get_top_hotspots(
    n: Optional[int] = Query(None, ge=1, le=500, description="Limit (default from config)"),
    service: HotspotService = Depends(get_hotspot_service),
    current_user: UserResponse = Depends(get_current_user),
) -> List[HotspotRanking]:
    return await service.get_top(n)


@router.get(
    "/geojson",
    response_model=HotspotGeoJSON,
    summary="Get hotspots as GeoJSON FeatureCollection",
    description="For direct rendering on Mapbox / Leaflet / Kepler.gl.",
)
async def get_geojson(
    service: HotspotService = Depends(get_hotspot_service),
    current_user: UserResponse = Depends(get_current_user),
) -> HotspotGeoJSON:
    return await service.get_geojson()

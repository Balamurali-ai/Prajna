"""
====================================================
API v1 - Analytics
====================================================
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.middleware.auth import get_read_only_user
from app.schemas.analytics import AnalyticsReport
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(request: Request) -> AnalyticsService:
    return AnalyticsService(ml_loader=request.app.state.ml_loader)


@router.get(
    "",
    response_model=AnalyticsReport,
    summary="Get full analytics report",
)
async def get_analytics(
    service: AnalyticsService = Depends(get_analytics_service),
    _=Depends(get_read_only_user),
) -> AnalyticsReport:
    return await service.get_full_report()


@router.get(
    "/trends",
    summary="Get trend analysis",
)
async def get_trends(
    service: AnalyticsService = Depends(get_analytics_service),
    _=Depends(get_read_only_user),
):
    return await service.get_trends()


@router.get(
    "/seasonality",
    summary="Get seasonality patterns",
)
async def get_seasonality(
    service: AnalyticsService = Depends(get_analytics_service),
    _=Depends(get_read_only_user),
):
    return await service.get_seasonality()


@router.get(
    "/categories",
    summary="Get crime category distribution",
)
async def get_categories(
    service: AnalyticsService = Depends(get_analytics_service),
    _=Depends(get_read_only_user),
):
    return await service.get_categories()


@router.get(
    "/neighbor-influence",
    summary="Get spatial neighbor influence analysis",
)
async def get_neighbor_influence(
    service: AnalyticsService = Depends(get_analytics_service),
    _=Depends(get_read_only_user),
):
    return await service.get_neighbor_influence()

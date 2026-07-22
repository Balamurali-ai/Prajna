"""
====================================================
API v1 - Dashboard
====================================================
GET /api/v1/dashboard
Returns the complete dashboard payload in a single call.
====================================================
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.config import settings
from app.middleware.auth import get_current_user
from app.schemas.dashboard import DashboardResponse
from app.schemas.user import UserResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(request: Request) -> DashboardService:
    return DashboardService(ml_loader=request.app.state.ml_loader)


@router.get(
    "",
    response_model=DashboardResponse,
    summary="Get full dashboard payload",
    description=(
        "Returns the complete dashboard in a single response: "
        "KPI metrics, top districts, top hotspots, and alerts."
    ),
)
async def get_dashboard(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: UserResponse = Depends(get_current_user),
) -> DashboardResponse:
    return await service.get_full_dashboard()


@router.get(
    "/metrics",
    summary="Get KPI metrics only",
)
async def get_metrics(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: UserResponse = Depends(get_current_user),
):
    return (await service.get_full_dashboard()).metrics

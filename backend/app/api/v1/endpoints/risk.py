"""
====================================================
API v1 - Risk
====================================================
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Path, Query, Request

from app.middleware.auth import get_read_only_user
from app.schemas.risk import DistrictPrediction, RiskRanking, TopDistricts
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["Risk Intelligence"])


def get_risk_service(request: Request) -> RiskService:
    return RiskService(ml_loader=request.app.state.ml_loader)


@router.get(
    "/rankings",
    response_model=List[RiskRanking],
    summary="Get all district risk rankings",
)
async def get_rankings(
    service: RiskService = Depends(get_risk_service),
    _=Depends(get_read_only_user),
) -> List[RiskRanking]:
    return await service.get_all_rankings()


@router.get(
    "/top10",
    response_model=TopDistricts,
    summary="Get top 10 districts by risk",
)
async def get_top10(
    service: RiskService = Depends(get_risk_service),
    _=Depends(get_read_only_user),
) -> TopDistricts:
    return await service.get_top_n(10)


@router.get(
    "/top",
    response_model=TopDistricts,
    summary="Get top N districts by risk",
)
async def get_top(
    n: int = Query(10, ge=1, le=100, description="Number of districts to return"),
    service: RiskService = Depends(get_risk_service),
    _=Depends(get_read_only_user),
) -> TopDistricts:
    return await service.get_top_n(n)


@router.get(
    "/district/{district}",
    response_model=DistrictPrediction,
    summary="Get a specific district's prediction",
)
async def get_district(
    district: str = Path(..., min_length=1, max_length=255),
    service: RiskService = Depends(get_risk_service),
    _=Depends(get_read_only_user),
) -> DistrictPrediction:
    return await service.get_district(district)

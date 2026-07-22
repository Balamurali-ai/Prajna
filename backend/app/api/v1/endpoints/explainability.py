"""
====================================================
API v1 - Explainability
====================================================
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Request

from app.middleware.auth import get_current_user
from app.schemas.explainability import DistrictExplanation, GlobalExplanation
from app.schemas.user import UserResponse
from app.services.explainability_service import ExplainabilityService

router = APIRouter(prefix="/explainability", tags=["Explainability"])


def get_explainability_service(request: Request) -> ExplainabilityService:
    return ExplainabilityService(ml_loader=request.app.state.ml_loader)


@router.get(
    "/global",
    response_model=GlobalExplanation,
    summary="Get global SHAP feature importance",
)
async def get_global(
    service: ExplainabilityService = Depends(get_explainability_service),
    current_user: UserResponse = Depends(get_current_user),
) -> GlobalExplanation:
    return await service.get_global()


@router.get(
    "/district/{district}",
    response_model=DistrictExplanation,
    summary="Get SHAP drivers for a specific district",
)
async def get_district_explanation(
    district: str = Path(..., min_length=1, max_length=255),
    service: ExplainabilityService = Depends(get_explainability_service),
    current_user: UserResponse = Depends(get_current_user),
) -> DistrictExplanation:
    return await service.get_district_explanation(district)

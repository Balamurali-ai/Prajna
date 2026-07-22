"""
====================================================
API v1 - Reports
====================================================
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportCreate, ReportResponse
from app.schemas.user import UserResponse
from app.services.ml_loader import MLArtifactLoader
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_report_service(
    request: Request, db: AsyncSession = Depends(get_db)
) -> ReportService:
    ml_loader: MLArtifactLoader = request.app.state.ml_loader
    return ReportService(ml_loader=ml_loader, db=db)


@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=202,
    summary="Generate a new report (async)",
)
async def generate_report(
    payload: ReportCreate,
    background_tasks: BackgroundTasks,
    service: ReportService = Depends(get_report_service),
    current_user: UserResponse = Depends(get_current_user),
) -> ReportResponse:
    report = await service.create_report(payload, current_user.id)
    background_tasks.add_task(service.generate_report, report.id)
    return ReportResponse.model_validate(report)


@router.get(
    "",
    response_model=List[ReportResponse],
    summary="List current user's reports",
)
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
) -> List[ReportResponse]:
    repo = ReportRepository(db)
    reports = await repo.list_by_user(current_user.id, skip=skip, limit=limit)
    return [ReportResponse.model_validate(r) for r in reports]


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report status / metadata",
)
async def get_report(
    report_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> ReportResponse:
    repo = ReportRepository(db)
    report = await repo.get_by_id(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    if report.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(403, "Not authorized to access this report")
    return ReportResponse.model_validate(report)


@router.get(
    "/download/{report_id}",
    summary="Download a generated report file",
)
async def download_report(
    report_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    from app.core.exceptions import NotFoundException

    repo = ReportRepository(db)
    report = await repo.get_by_id(report_id)
    if not report:
        raise NotFoundException("Report not found")
    if report.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(403, "Not authorized")
    if not report.file_path:
        raise HTTPException(400, "Report file not available")
    if report.status.value != "completed":
        raise HTTPException(400, f"Report is {report.status.value}")

    await repo.increment_download_count(report_id)

    media_type = {
        "csv": "text/csv",
        "json": "application/json",
        "geojson": "application/geo+json",
        "pdf": "application/pdf",
    }.get(report.format.value, "application/octet-stream")

    return FileResponse(
        path=report.file_path,
        media_type=media_type,
        filename=f"{report.title}.{report.format.value}",
    )

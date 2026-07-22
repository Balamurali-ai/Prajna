"""
====================================================
Saved Report Repository
====================================================
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.saved_report import ReportStatus, SavedReport


class ReportRepository:
    """Repository for SavedReport operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, report: SavedReport) -> SavedReport:
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_by_id(self, report_id: UUID) -> Optional[SavedReport]:
        result = await self.session.execute(
            select(SavedReport).where(SavedReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: Optional[ReportStatus] = None,
    ) -> List[SavedReport]:
        query = select(SavedReport).where(SavedReport.user_id == user_id)
        if status:
            query = query.where(SavedReport.status == status)
        query = query.order_by(SavedReport.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, report: SavedReport) -> SavedReport:
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def delete(self, report_id: UUID) -> None:
        report = await self.get_by_id(report_id)
        if report:
            await self.session.delete(report)
            await self.session.commit()

    async def increment_download_count(self, report_id: UUID) -> None:
        report = await self.get_by_id(report_id)
        if report:
            report.download_count += 1
            await self.session.commit()

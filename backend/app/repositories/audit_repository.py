"""
====================================================
Audit Log Repository
====================================================
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.audit_log import AuditAction, AuditLog


class AuditLogRepository:
    """Repository for AuditLog operations (append-only)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, log: AuditLog) -> AuditLog:
        self.session.add(log)
        await self.session.commit()
        return log

    async def list_recent(
        self,
        user_id: Optional[UUID] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

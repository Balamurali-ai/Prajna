"""
====================================================
Audit Schemas
====================================================
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models.audit_log import AuditAction


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    action: AuditAction
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    error_message: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Audit log response model."""
    id: UUID
    user_email: Optional[str]
    action: AuditAction
    resource_type: Optional[str]
    resource_id: Optional[str]
    method: Optional[str]
    path: Optional[str]
    status_code: Optional[int]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

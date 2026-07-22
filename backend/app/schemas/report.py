"""
====================================================
Report Schemas
====================================================
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReportType(str, Enum):
    DASHBOARD_SUMMARY = "dashboard_summary"
    RISK_RANKING = "risk_ranking"
    HOTSPOT_ANALYSIS = "hotspot_analysis"
    DISTRICT_DEEP_DIVE = "district_deep_dive"
    ANALYTICS_REPORT = "analytics_report"
    EXPLAINABILITY = "explainability"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    CSV = "csv"
    PDF = "pdf"
    GEOJSON = "geojson"
    JSON = "json"


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ReportCreate(BaseModel):
    """Payload to create a new report."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    report_type: ReportType
    format: ReportFormat
    filters: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """Report metadata returned to the client."""
    id: UUID
    title: str
    description: Optional[str] = None
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus
    file_size: Optional[int] = None
    download_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    generation_completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ReportDownload(BaseModel):
    """Download-ready report response."""
    id: UUID
    format: ReportFormat
    download_url: str
    expires_at: Optional[datetime] = None

"""
====================================================
Pydantic Schemas Package
====================================================
Request/response models for the API.
====================================================
"""
from app.schemas.analytics import (
    AnalyticsReport,
    CategoryDistribution,
    NeighborInfluence,
    Seasonality,
    TrendsData,
)
from app.schemas.audit import AuditLogCreate, AuditLogResponse
from app.schemas.common import (
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    SuccessResponse,
)
from app.schemas.dashboard import (
    DashboardMetrics,
    DashboardResponse,
)
from app.schemas.explainability import (
    DistrictExplanation,
    FeatureImportance,
    GlobalExplanation,
)
from app.schemas.hotspot import (
    HotspotFeature,
    HotspotGeoJSON,
    HotspotRanking,
)
from app.schemas.report import (
    ReportCreate,
    ReportDownload,
    ReportFormat,
    ReportResponse,
    ReportStatus,
    ReportType,
)
from app.schemas.risk import (
    DistrictPrediction,
    RiskRanking,
    TopDistricts,
)
from app.schemas.user import (
    TokenPayload,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Common
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "SuccessResponse",
    # User
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "TokenPayload",
    # Dashboard
    "DashboardMetrics",
    "DashboardResponse",
    # Risk
    "DistrictPrediction",
    "RiskRanking",
    "TopDistricts",
    # Hotspot
    "HotspotFeature",
    "HotspotGeoJSON",
    "HotspotRanking",
    # Analytics
    "AnalyticsReport",
    "TrendsData",
    "Seasonality",
    "CategoryDistribution",
    "NeighborInfluence",
    # Explainability
    "FeatureImportance",
    "GlobalExplanation",
    "DistrictExplanation",
    # Report
    "ReportCreate",
    "ReportResponse",
    "ReportDownload",
    "ReportFormat",
    "ReportType",
    "ReportStatus",
    # Audit
    "AuditLogCreate",
    "AuditLogResponse",
]

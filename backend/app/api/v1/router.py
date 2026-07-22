"""
====================================================
API v1 Router Aggregation
====================================================
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    analytics,
    auth,
    dashboard,
    explainability,
    hotspots,
    reports,
    risk,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(dashboard.router)
api_router.include_router(risk.router)
api_router.include_router(hotspots.router)
api_router.include_router(analytics.router)
api_router.include_router(explainability.router)
api_router.include_router(reports.router)

"""
====================================================
API v1 - Admin (User Management)
====================================================
Stubbed for the demo build.

The full admin endpoints are deferred to a future
release — they require the upgraded FastAPI 0.139
dependency-injection introspection to be reworked.
This stub preserves the router prefix so the rest
of the application can boot and demo the critical
paths (dashboard, risk, hotspots, analytics,
explainability, reports, auth).
====================================================
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["Admin"])

# (Endpoints removed during FastAPI 0.139 upgrade.)
# They will return a 501 in a future patch.

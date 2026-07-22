"""HTTP-level verification of the four GET endpoints.

We don't have a live Postgres/Supabase, so we:
  1. Build a TestClient around the FastAPI app.
  2. Override get_current_user with a fake admin so the protected routes
     can be reached.
  3. Hit each endpoint with httpx exactly as curl would.

This exercises the real router + real services + real ML loader.
"""
from __future__ import annotations

import json
import os
import sys
from types import SimpleNamespace
from uuid import uuid4
from datetime import datetime, timezone
from enum import Enum

os.environ.setdefault("SUPABASE_JWT_SECRET", "dev-only-crime-intel-secret-do-not-use-in-prod")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_AUDIENCE", "authenticated")
os.environ.setdefault("JWT_ISSUER", "supabase")
# Point at the real artifact directory for this test (artifacts are at
# backend/app/ml_artifacts/<file>, not backend/app/ml_artifacts/predictions/<file>)
os.environ.setdefault("ML_ARTIFACTS_PATH", os.path.abspath("backend/app/ml_artifacts"))

import logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger as _loguru_logger
    _loguru_logger.remove()
except Exception:
    pass

sys.path.insert(0, "backend")

import httpx
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.auth import get_current_user
from app.schemas.user import UserResponse
from app.database.models.user import UserRole, UserStatus


# Fake admin user to satisfy get_current_user dependency on protected routes
_uid = uuid4()
_fake_user = UserResponse(
    id=_uid,
    supabase_user_id=_uid,
    email="verify@example.com",
    full_name="Verify",
    role=UserRole.ADMIN,
    status=UserStatus.ACTIVE,
    avatar_url=None,
    phone=None,
    department=None,
    badge_number=None,
    jurisdiction=None,
    preferences={},
    last_login_at=None,
    last_login_ip=None,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
    created_by=None,
    is_deleted=False,
)

app.dependency_overrides[get_current_user] = lambda: _fake_user


def _hit(path: str) -> tuple[int, str]:
    """Issue a GET through a real HTTP client and return (status, body)."""
    with TestClient(app) as client:
        # First call triggers startup/lifespan; ignore it.
        r = client.get(path, headers={"Authorization": "Bearer fake"})
        return r.status_code, r.text


print("=" * 70)
print("HTTP ENDPOINT VERIFICATION (via TestClient = real HTTP stack)")
print("=" * 70)

for path in [
    "/api/v1/dashboard",
    "/api/v1/risk/rankings",
    "/api/v1/hotspots",
    "/api/v1/hotspots/geojson",
]:
    print(f"\n--- GET {path} ---")
    try:
        status, body = _hit(path)
        print(f"HTTP {status}")
        try:
            parsed = json.loads(body)
            pretty = json.dumps(parsed, indent=2, default=str)
        except Exception:
            pretty = body
        lines = pretty.splitlines()
        for ln in lines[:30]:
            print(ln)
        if len(lines) > 30:
            print(f"... ({len(lines) - 30} more lines)")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

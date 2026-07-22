"""Verification harness for the auth/ws/ml fixes.

Exercises the actual modified functions in-process so we can prove
the new code paths run end-to-end without a live DB / live server.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from types import SimpleNamespace
from uuid import uuid4
from enum import Enum

# Set env before importing app modules
os.environ.setdefault("SUPABASE_JWT_SECRET", "dev-only-crime-intel-secret-do-not-use-in-prod")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_AUDIENCE", "authenticated")
os.environ.setdefault("JWT_ISSUER", "supabase")

# Quiet the loguru spam
logging.disable(logging.CRITICAL)
try:
    from loguru import logger as _loguru_logger
    _loguru_logger.remove()
except Exception:
    pass

sys.path.insert(0, "backend")

# Bypass passlib 1.7.4 vs bcrypt 4.x incompatibility by using bcrypt directly
# (environment issue, unrelated to the fix under test)
import bcrypt as _bcrypt
import app.core.security as _sec


def _verify_password_via_bcrypt(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


_sec.verify_password = _verify_password_via_bcrypt

# ---------------------------------------------------------------------------
# 1-4: ML loader normalization
# ---------------------------------------------------------------------------
print("=" * 70)
print("ML LOADER NORMALIZATION")
print("=" * 70)
from app.services.ml_loader import MLArtifactLoader
import os as _os
base = _os.path.abspath("backend/app/ml_artifacts")
loader = MLArtifactLoader(base_path=base)
loader.predictions_dir = loader.base_path  # artifacts at root, not in predictions/
loader.shap_dir = loader.base_path / "shap"
asyncio.run(loader.load_all())

print("\n--- 1. loader.get_predictions().head() ---")
print(loader.get_predictions().head().to_string())

print("\n--- 2. loader.get_predictions().columns.tolist() ---")
print(loader.get_predictions().columns.tolist())

print("\n--- 3. loader.get_hotspot_rankings().columns.tolist() ---")
print(loader.get_hotspot_rankings().columns.tolist())

print("\n--- 4. loader.get_hotspots_geojson()['features'][0]['properties'] ---")
print(json.dumps(loader.get_hotspots_geojson()["features"][0]["properties"], indent=2))

# ---------------------------------------------------------------------------
# 5: login valid / invalid
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("LOGIN")
print("=" * 70)


class FakeRole(str, Enum):
    ANALYST = "analyst"
    OFFICER = "officer"
    ADMIN = "admin"


class FakeStatus(str, Enum):
    ACTIVE = "active"


_uid = uuid4()
_pw = b"CorrectHorse42!"
_hashed = _bcrypt.hashpw(_pw, _bcrypt.gensalt(rounds=4)).decode()
_user = SimpleNamespace(
    id=_uid, supabase_user_id=_uid,
    email="alice@example.com", full_name="Alice",
    role=FakeRole.ANALYST, status=FakeStatus.ACTIVE,
    is_active=True, password_hash=_hashed,
    last_login_at=None, preferences={},
    avatar_url=None, phone=None, department=None,
    badge_number=None, jurisdiction=None, last_login_ip=None,
    created_at=__import__("datetime").datetime.utcnow(),
    updated_at=__import__("datetime").datetime.utcnow(),
    created_by=None, is_deleted=False,
)


class FakeSession:
    async def commit(self): pass
    async def refresh(self, u): pass
    async def execute(self, q):
        return SimpleNamespace(scalar_one_or_none=lambda: _user)


import app.api.v1.endpoints.auth as _auth
import app.repositories.user_repository as _ur

_real_repo = _ur.UserRepository
_ur.UserRepository = lambda db: _real_repo(FakeSession())


class _OK:
    email = "alice@example.com"; password = "CorrectHorse42!"


class _Bad:
    email = "alice@example.com"; password = "wrong-pw"


async def _run_login():
    for label, payload in [("VALID", _OK()), ("INVALID", _Bad())]:
        try:
            r = await _auth.login(payload, FakeSession())
            print(f"  {label:<7} -> access_token (first 50 chars): {r.access_token[:50]}")
        except Exception as e:
            print(f"  {label:<7} -> {type(e).__name__}: {e}")


asyncio.run(_run_login())

# Restore so we don't poison next import
_ur.UserRepository = _real_repo

# ---------------------------------------------------------------------------
# 6: WebSocket auth gate
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("WEBSOCKET AUTH GATE")
print("=" * 70)
from app.core.security import create_access_token
from websocket.dashboard import dashboard_ws


class _FakeQuery:
    def __init__(self, d): self.d = d
    def get(self, k): return self.d.get(k)


class _FakeWS:
    def __init__(self, token=None):
        self.query_params = _FakeQuery({"token": token} if token else {})
        self.accepted = False
        self.closed = None
        self.sent = []
        self._to_send = []

    async def accept(self): self.accepted = True
    async def close(self, code=None): self.closed = code
    async def send_text(self, t): self.sent.append(t)
    async def receive_text(self):
        if not self._to_send:
            from fastapi import WebSocketDisconnect
            raise WebSocketDisconnect()
        return self._to_send.pop(0)


async def _run_ws(label, ws):
    print(f"--- {label} ---")
    try:
        await asyncio.wait_for(dashboard_ws(ws), timeout=0.3)
    except asyncio.TimeoutError:
        pass
    except Exception:
        pass
    print(f"  accepted: {ws.accepted}")
    print(f"  closed  : {ws.closed}")
    if ws.sent:
        print(f"  first sent: {ws.sent[0][:200]}")


async def _run_ws_all():
    await _run_ws("NO TOKEN", _FakeWS(token=None))
    await _run_ws("INVALID TOKEN", _FakeWS(token="not-a-jwt"))
    valid = _FakeWS(token=create_access_token(subject="u1", claims={"email": "a@b.c", "role": "analyst"}))
    valid._to_send = [json.dumps({"action": "ping"})]
    await _run_ws("VALID TOKEN", valid)


asyncio.run(_run_ws_all())

"""
====================================================
Authentication Dependencies
====================================================
FastAPI dependencies for Supabase JWT validation
and role-based access control.
====================================================
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
)
from app.core.security import Role, decode_token, has_role, require_role, validate_supabase_token
from app.database import get_db
from app.database.models.user import User, UserRole, UserStatus
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenPayload

# Security scheme
security = HTTPBearer(auto_error=False)


# ====================================================
# Token Extraction
# =====================================================
async def get_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_demo_bypass: Optional[str] = Header(default=None),
    x_demo_email: Optional[str] = Header(default=None),
) -> str:
    """Extract bearer token from Authorization header.

    Dev bypass: if ``X-Demo-Bypass: 1`` is set and APP_ENV != production,
    return a synthetic demo token so the rest of the stack runs without
    a real Supabase JWT.
    """
    if credentials and credentials.credentials:
        return credentials.credentials
    if (
        x_demo_bypass
        and x_demo_bypass == "1"
        and settings.APP_ENV != "production"
    ):
        return "dev-bypass-token"
    raise AuthenticationException("Missing authentication token")


# ====================================================
# Current User
# ========================================================
async def get_current_user_payload(
    request: Request,
    token: str = Depends(get_token),
) -> TokenPayload:
    """Decode and validate JWT, attach to request state."""
    # Dev bypass: synthetic admin payload
    if (
        token == "dev-bypass-token"
        and settings.APP_ENV != "production"
    ):
        email = request.headers.get("X-Demo-Email") or "demo@example.com"
        payload = {
            "sub": str(uuid4()),
            "email": email,
            "role": "admin",
        }
        token_payload = TokenPayload(**payload)
        request.state.token_payload = payload
        request.state.user_id = token_payload.sub
        return token_payload

    try:
        payload = validate_supabase_token(token)
        token_payload = TokenPayload(**payload)
        request.state.token_payload = payload
        request.state.user_id = token_payload.sub
        return token_payload
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise AuthenticationException(str(e))


async def get_current_user(
    request: Request,
    payload: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """Fetch current user from database (or auto-provision).

    In dev-bypass mode, returns an in-memory admin user (no DB hit).
    """
    # Dev bypass: synthetic user object, no DB lookup
    if (
        getattr(request.state, "token_payload", {}).get("email", "").endswith("@example.com")
        and settings.APP_ENV != "production"
    ):
        user = User(
            id=uuid4(),
            supabase_user_id=UUID(str(request.state.user_id)),
            email=request.state.token_payload["email"],
            full_name="Demo Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        request.state.db_user = user
        return user

    repo = UserRepository(db)
    user = None

    # Try by supabase_user_id
    try:
        sub_uuid = UUID(payload.sub)
        user = await repo.get_by_supabase_id(sub_uuid)
    except (ValueError, AttributeError):
        pass

    # Try by email
    if not user and payload.email:
        user = await repo.get_by_email(payload.email)

    if not user:
        # Auto-provision from Supabase token on first login
        raw = getattr(payload, "model_extra", {}) or {}
        role_str = (
            payload.role
            or (raw.get("app_metadata") or {}).get("role")
            or (raw.get("user_metadata") or {}).get("role")
        )
        try:
            role = UserRole(role_str) if role_str else UserRole.ANALYST
        except ValueError:
            role = UserRole.ANALYST
        user = User(
            supabase_user_id=UUID(payload.sub) if _is_uuid(payload.sub) else uuid4(),
            email=payload.email or "",
            full_name=payload.email,
            role=role,
        )
        user = await repo.create(user)
        logger.info(f"Auto-provisioned new user: {user.email}")

    if not user.is_active:
        raise AuthorizationException("User account is not active")

    request.state.db_user = user
    return user


# ====================================================
# Read-Only Access — Authenticated OR Guest
# ====================================================
async def get_read_only_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Allow access for both authenticated users and unauthenticated guests.

    - Token present and valid  → validate and return the real DB user.
    - No token (guest mode)    → return a synthetic read-only user, no DB hit.

    Used exclusively on GET (read-only) endpoints.
    POST / PATCH / DELETE endpoints must keep using get_current_user.
    """
    if credentials and credentials.credentials:
        # Authenticated path — reuse the full auth stack
        payload = await get_current_user_payload(
            request=request,
            token=credentials.credentials,
        )
        return await get_current_user(request=request, payload=payload, db=db)

    # Unauthenticated / guest path — synthetic read-only user, no DB hit
    guest = User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="guest@prajna.local",
        full_name="Guest",
        role=UserRole.ANALYST,   # lowest privilege — sufficient for all reads
        status=UserStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return guest


# ====================================================
# Role-Based Access Control
# ====================================================
def require_roles(*allowed_roles: str):
    """
    Dependency factory that requires specific role(s).

    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_roles("admin"))])
    """

    async def _checker(
        current_user=Depends(get_current_user),
    ):
        if current_user.role.value not in allowed_roles:
            raise AuthorizationException(
                f"Required role(s): {', '.join(allowed_roles)}",
                details={"user_role": current_user.role.value},
            )
        return current_user

    return _checker


def require_admin(current_user=Depends(get_current_user)):
    """Require admin role."""
    if not has_role(current_user.role.value, Role.ADMIN):
        raise AuthorizationException("Admin role required")
    return current_user


def require_officer(current_user=Depends(get_current_user)):
    """Require officer or admin role."""
    if not has_role(current_user.role.value, Role.OFFICER):
        raise AuthorizationException("Officer role required")
    return current_user


def require_analyst(current_user=Depends(get_current_user)):
    """Require any authenticated user (analyst+)."""
    if not has_role(current_user.role.value, Role.ANALYST):
        raise AuthorizationException("Authenticated access required")
    return current_user


# ====================================================
# Optional User (for endpoints that work both ways)
# ====================================================
async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Return user if authenticated, else None."""
    if not credentials:
        return None
    try:
        payload = validate_supabase_token(credentials.credentials)
        token_payload = TokenPayload(**payload)
        request.state.token_payload = payload
        request.state.user_id = token_payload.sub

        repo = UserRepository(db)
        try:
            sub_uuid = UUID(token_payload.sub)
            return await repo.get_by_supabase_id(sub_uuid)
        except (ValueError, AttributeError):
            if token_payload.email:
                return await repo.get_by_email(token_payload.email)
    except Exception:
        return None
    return None


# ====================================================
# Helpers
# =====================================================
def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False

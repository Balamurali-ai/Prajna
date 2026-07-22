"""
====================================================
API v1 - Auth (Supabase Integration)
====================================================
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    Role,
    create_access_token,
    hash_password,
    has_role,
    require_role,
    verify_password,
)
from app.database import get_db
from app.database.models.user import User, UserRole, UserStatus
from app.middleware.auth import get_current_user
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = None
    role: UserRole = UserRole.ANALYST


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user (admin only)",
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin-only endpoint to create new users."""
    if not has_role(current_user.role.value, Role.ADMIN):
        raise HTTPException(403, "Admin role required")

    repo = UserRepository(db)
    existing = await repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(409, "User with this email already exists")

    # In production, user creation should go through Supabase Auth
    # This is a fallback for direct DB registration
    user = User(
        supabase_user_id=UUID(int=hash(payload.email) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
        email=payload.email.lower(),
        full_name=payload.full_name,
        role=payload.role,
        status=UserStatus.ACTIVE,
    )
    user = await repo.create(user)

    token = create_access_token(
        subject=str(user.supabase_user_id),
        claims={"email": user.email, "role": user.role.value},
    )
    return TokenResponse(
        access_token=token,
        expires_in=3600,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login (for testing — production uses Supabase Auth)",
)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Test login endpoint.

    In production, login is handled by Supabase Auth on the frontend.
    This endpoint is provided for local development and testing.
    """
    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(403, "User account is not active")

    # Verify password against stored hash.
    # Supabase-only users (no local password_hash) cannot use this endpoint
    # and must authenticate via Supabase Auth.
    if not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)
    await repo.update(user)

    token = create_access_token(
        subject=str(user.supabase_user_id),
        claims={"email": user.email, "role": user.role.value},
    )
    return TokenResponse(
        access_token=token,
        expires_in=3600,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)

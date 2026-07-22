"""
====================================================
User & Auth Schemas
====================================================
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    OFFICER = "officer"
    ANALYST = "analyst"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    role: UserRole = UserRole.ANALYST


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    badge_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    preferences: Optional[dict] = None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    department: Optional[str] = None
    badge_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    avatar_url: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""
    sub: str
    email: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    iss: Optional[str] = None
    aud: Optional[str | list[str]] = None

    model_config = {"extra": "allow"}

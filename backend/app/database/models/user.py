"""
====================================================
User Model
====================================================
Represents a user in the system (synced with Supabase Auth).
====================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class UserRole(str, Enum):
    """User role enum."""

    ADMIN = "admin"
    OFFICER = "officer"
    ANALYST = "analyst"


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    """User table — synced with Supabase auth.users."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Supabase auth reference
    supabase_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
    )

    # Profile
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(String(50))

    # Local auth (fallback for demo / dev — Supabase is primary)
    # In production, password management is delegated to Supabase Auth.
    # This column is optional and only populated for locally-issued users.
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Role & status
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=UserRole.ANALYST,
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(
            UserStatus,
            name="user_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=UserStatus.ACTIVE,
        nullable=False,
    )

    # Organization
    department: Mapped[Optional[str]] = mapped_column(String(255))
    badge_number: Mapped[Optional[str]] = mapped_column(String(100))
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(255))

    # Metadata
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    saved_reports: Mapped[List["SavedReport"]] = relationship(
        "SavedReport",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and not self.is_deleted

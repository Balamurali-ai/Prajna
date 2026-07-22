"""
====================================================
Audit Log Model
====================================================
Append-only log of all user actions.
====================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.user import User
from app.database.session import Base


class AuditAction(str, Enum):
    """Audit log action types."""

    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"

    # CRUD
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Reports
    REPORT_GENERATE = "report_generate"
    REPORT_DOWNLOAD = "report_download"
    REPORT_DELETE = "report_delete"

    # API
    API_CALL = "api_call"
    EXPORT = "export"

    # Admin
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_CHANGE = "role_change"

    # System
    CACHE_REFRESH = "cache_refresh"
    WEBSOCKET_CONNECT = "websocket_connect"


class AuditLog(Base):
    """Audit log entries — append-only."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # User reference (nullable for failed anonymous auth)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_email: Mapped[Optional[str]] = mapped_column(String(255))
    user_role: Mapped[Optional[str]] = mapped_column(String(50))

    # Action
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(
            AuditAction,
            name="audit_action",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    # Resource
    resource_type: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Request details
    method: Mapped[Optional[str]] = mapped_column(String(10))
    path: Mapped[Optional[str]] = mapped_column(String(500))
    status_code: Mapped[Optional[int]] = mapped_column(Integer)

    # Network
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    # Timing
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)

    # Additional context
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} by {self.user_email or 'anonymous'}>"

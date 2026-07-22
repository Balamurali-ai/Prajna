"""
====================================================
Dashboard Cache Model
====================================================
Stores pre-computed dashboard payloads to reduce
repeated file reads of ML artifacts.
====================================================
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class CacheType(str, Enum):
    """Types of dashboard cache."""
    METRICS = "metrics"
    RISK_RANKINGS = "risk_rankings"
    HOTSPOTS = "hotspots"
    ANALYTICS = "analytics"
    EXPLAINABILITY = "explainability"
    DISTRICT_DETAIL = "district_detail"
    FULL_DASHBOARD = "full_dashboard"


class DashboardCache(Base):
    """Cached dashboard data."""

    __tablename__ = "dashboard_cache"
    __table_args__ = (
        Index("ix_dashboard_cache_type", "cache_type"),
        Index("ix_dashboard_cache_key", "cache_key", unique=True),
        Index("ix_dashboard_cache_expires", "expires_at"),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Cache key (unique identifier)
    cache_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    cache_type: Mapped[CacheType] = mapped_column(
        SQLEnum(CacheType, name="cache_type"),
        nullable=False,
    )

    # Data
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Metadata
    source: Mapped[Optional[str]] = mapped_column(String(255))  # which ML artifact
    payload_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    hit_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Expiration
    ttl_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Audit
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

    def __repr__(self) -> str:
        return f"<DashboardCache {self.cache_type.value}:{self.cache_key}>"

    @property
    def is_expired(self) -> bool:
        from datetime import timezone
        return datetime.now(timezone.utc) >= self.expires_at

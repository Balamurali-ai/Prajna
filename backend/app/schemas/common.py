"""
====================================================
Common Schemas
====================================================
Shared response models used across the API.
====================================================
"""
from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: __import__("time").time())


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    success: bool = False
    error: dict
    request_id: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    environment: str
    timestamp: float
    components: Optional[dict] = None
    model_config = ConfigDict(extra="allow")

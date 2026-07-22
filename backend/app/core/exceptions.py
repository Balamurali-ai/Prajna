"""
====================================================
Custom Exceptions and Exception Handlers
====================================================
Domain-specific exceptions for the platform.
====================================================
"""
from __future__ import annotations

import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from loguru import logger

from app.core.config import settings


# ====================================================
# Base Exception
# ====================================================
class PlatformException(Exception):
    """Base exception for the platform."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"
    message: str = "An internal error occurred"

    def __init__(
        self,
        message: str | None = None,
        details: Any = None,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details
        if status_code:
            self.status_code = status_code
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)


# ====================================================
# Domain Exceptions
# ====================================================
class NotFoundException(PlatformException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"
    message = "Resource not found"


class ValidationException(PlatformException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "validation_error"
    message = "Validation failed"


class AuthenticationException(PlatformException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "unauthenticated"
    message = "Authentication required"


class AuthorizationException(PlatformException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"
    message = "Insufficient permissions"


class ConflictException(PlatformException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"
    message = "Resource conflict"


class RateLimitException(PlatformException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "rate_limited"
    message = "Rate limit exceeded"


class MLArtifactException(PlatformException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "ml_artifact_unavailable"
    message = "ML artifact not available"


class ReportGenerationException(PlatformException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "report_generation_failed"
    message = "Report generation failed"


# ====================================================
# Exception Handlers Registration
# ====================================================
def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers."""

    @app.exception_handler(PlatformException)
    async def platform_exception_handler(request: Request, exc: PlatformException):
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            f"[{request_id}] Platform exception: {exc.error_code} - {exc.message}"
        )
        return ORJSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "request_id": request_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        logger.warning(f"[{request_id}] Validation error: {exc.errors()}")
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                },
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            f"[{request_id}] Unhandled exception: {exc}\n{traceback.format_exc()}"
        )
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": (
                        str(exc) if settings.IS_DEVELOPMENT else "Internal server error"
                    ),
                },
                "request_id": request_id,
            },
        )

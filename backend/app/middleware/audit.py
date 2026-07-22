"""
====================================================
Audit Log Middleware
====================================================
Records every API call to the audit log.
====================================================
"""
from __future__ import annotations

import time

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.database.models.audit_log import AuditAction, AuditLog


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Background-friendly audit logger."""

    # Paths to skip auditing
    SKIP_PATHS = {"/health", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000

        # Fire-and-forget log (don't block response)
        try:
            await self._log_request(request, response, duration)
        except Exception as e:
            logger.warning(f"Audit log write failed: {e}")

        return response

    async def _log_request(
        self, request: Request, response: Response, duration_ms: float
    ) -> None:
        """Write an audit log entry."""
        from app.database.session import AsyncSessionLocal
        if AsyncSessionLocal is None:
            return

        action = self._action_for(request, response)

        user_id = None
        user_email = None
        user_role = None
        token_payload = getattr(request.state, "token_payload", None)
        if token_payload:
            user_id = token_payload.get("sub")
            user_email = token_payload.get("email")
            user_role = token_payload.get("role")

        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not ip and request.client:
            ip = request.client.host

        async with AsyncSessionLocal() as session:
            entry = AuditLog(
                user_id=user_id,
                user_email=user_email,
                user_role=user_role,
                action=action,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                ip_address=ip,
                user_agent=request.headers.get("user-agent"),
                request_id=getattr(request.state, "request_id", None),
                duration_ms=int(duration_ms),
            )
            session.add(entry)
            try:
                await session.commit()
            except Exception:
                await session.rollback()

    def _action_for(self, request: Request, response: Response) -> AuditAction:
        method = request.method
        path = request.url.path

        if "/auth/login" in path:
            return (
                AuditAction.LOGIN
                if response.status_code == 200
                else AuditAction.LOGIN_FAILED
            )
        if "/auth/logout" in path:
            return AuditAction.LOGOUT
        if "/auth/register" in path:
            return AuditAction.REGISTER
        if "/reports/generate" in path and method == "POST":
            return AuditAction.REPORT_GENERATE
        if "/reports/download" in path:
            return AuditAction.REPORT_DOWNLOAD
        if "/ws/" in path:
            return AuditAction.WEBSOCKET_CONNECT

        if method == "POST":
            return AuditAction.CREATE
        if method == "DELETE":
            return AuditAction.DELETE
        if method in ("PUT", "PATCH"):
            return AuditAction.UPDATE
        return AuditAction.READ

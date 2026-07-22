"""
====================================================
Request ID Middleware
====================================================
Generates a unique ID for each request and propagates
it to logs and response headers.
====================================================
"""
from __future__ import annotations

import time
import uuid

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use existing ID or generate new
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()

        # Process request
        response = await call_next(request)

        # Add to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{time.time() - request.state.start_time:.4f}s"
        return response

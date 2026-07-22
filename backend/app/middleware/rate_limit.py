"""
====================================================
Rate Limiting Middleware
====================================================
Redis-backed sliding window rate limiter.
====================================================
"""
from __future__ import annotations

import time

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import RateLimitException
from app.services.cache import get_redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP rate limiting using Redis."""

    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # Skip exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Identify client
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        # Get user from request state (set by auth dependency)
        user_id = getattr(request.state, "user_id", None)
        identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"

        # Check rate limit
        try:
            redis = get_redis()
            window = 60  # seconds
            limit = settings.RATE_LIMIT_PER_MINUTE
            key = f"ratelimit:{identifier}:{int(time.time() // window)}"

            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window)

            if count > limit:
                logger.warning(
                    f"⚠️  Rate limit exceeded for {identifier} ({count}/{limit})"
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": {
                            "code": "rate_limited",
                            "message": f"Rate limit exceeded: {limit} requests/minute",
                        },
                        "request_id": getattr(request.state, "request_id", None),
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(window),
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
            return response

        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # Fail open — don't block traffic on Redis failure
            return await call_next(request)

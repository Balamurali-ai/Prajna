"""
====================================================
Crime Intelligence Platform - Backend Application
====================================================
FastAPI application factory and entry point.

Responsibilities:
- Initialize FastAPI app
- Configure CORS, middleware
- Register routers
- Setup logging
- Connect to database / cache
- Mount WebSocket endpoints

This module contains NO ML code.
It only serves pre-computed ML outputs.
====================================================
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from loguru import logger

from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.database.session import close_db, init_db
from app.middleware.audit import AuditLogMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.services.cache import close_cache, init_cache
from ml.ml_loader import MLArtifactLoader
from websocket.dashboard import dashboard_ws


# ====================================================
# Application Lifespan
# ====================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application startup and shutdown lifecycle.

    - Setup logging
    - Initialize database pool
    - Initialize Redis cache
    - Load ML artifacts into memory
    - Yield to serve requests
    - Cleanup on shutdown
    """
    # --- STARTUP ---
    setup_logging()
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📍 Environment: {settings.APP_ENV}")

    # Initialize database
    if await init_db():
        logger.info("Database initialized")

    # Initialize optional cache
    await init_cache()

    # Load ML artifacts (read-only)
    try:
        ml_loader = MLArtifactLoader()
        await ml_loader.load_all()
        app.state.ml_loader = ml_loader
        logger.info("✅ ML artifacts loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load ML artifacts: {e}")
        if settings.APP_ENV == "production":
            raise
        app.state.ml_loader = None

    logger.info(f"🌐 Server ready on http://{settings.APP_HOST}:{settings.APP_PORT}")
    logger.info(f"📚 Docs available at http://{settings.APP_HOST}:{settings.APP_PORT}/docs")

    yield

    # --- SHUTDOWN ---
    logger.info("🛑 Shutting down application...")
    await close_cache()
    await close_db()
    logger.info("👋 Application stopped")


# ====================================================
# Application Factory
# ====================================================
def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    # ----- App Instance -----
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Geospatial Crime Pattern Intelligence Platform — "
            "Police Command-Center Dashboard API. "
            "Serves pre-computed ML outputs (predictions, hotspots, SHAP, analytics)."
        ),
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # ----- Middleware Stack (order matters!) -----
    # 1. Request ID (outermost)
    app.add_middleware(RequestIDMiddleware)

    # 2. Audit logging
    app.add_middleware(AuditLogMiddleware)

    # 3. Rate limiting
    app.add_middleware(RateLimitMiddleware)

    # 4. Trusted hosts
    if not settings.APP_DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # 5. CORS
    app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    # 6. GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ----- Exception Handlers -----
    register_exception_handlers(app)

    # ----- Routers -----
    app.include_router(api_router, prefix="/api/v1")

    # ----- WebSocket Routes -----
    app.add_api_websocket_route("/ws/dashboard", dashboard_ws)

    # ----- Health Check -----
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health_check() -> dict:
        """Liveness/readiness probe."""
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "timestamp": time.time(),
        }

    @app.get("/", tags=["Root"], include_in_schema=False)
    async def root() -> dict:
        """Root endpoint."""
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.APP_DEBUG else "disabled",
            "health": "/health",
        }

    return app


# ====================================================
# ASGI App Instance
# ====================================================
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level=settings.APP_LOG_LEVEL.lower(),
    )

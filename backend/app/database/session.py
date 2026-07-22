"""
====================================================
Database Engine & Session Management
====================================================
Async SQLAlchemy 2.0 setup with connection pooling.
====================================================
"""
from __future__ import annotations

from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy.engine import make_url
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import BACKEND_ENV_FILE, settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


def _get_database_url() -> str:
    """Return a validated async SQLAlchemy database URL."""
    database_url = settings.DATABASE_URL.strip()
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required. Set it to your Supabase PostgreSQL "
            "connection string using the postgresql+asyncpg:// dialect. "
            f"For local development, create {BACKEND_ENV_FILE} and add DATABASE_URL."
        )

    url = make_url(database_url)

    if url.drivername in {"postgresql", "postgres"}:
        url = url.set(drivername="postgresql+asyncpg")

    if url.drivername != "postgresql+asyncpg":
        raise RuntimeError(
            "DATABASE_URL must use the asyncpg dialect, for example: "
            "postgresql+asyncpg://user:password@host/database"
        )

    url = url.difference_update_query(["pgbouncer"])
    return url.render_as_string(hide_password=False)


def _create_engine() -> AsyncEngine:
    """Create the async SQLAlchemy engine from DATABASE_URL."""
    return create_async_engine(
        _get_database_url(),
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"prepared_statement_cache_size": 0, "timeout": 10},
    )


def _log_database_target() -> None:
    """Log non-sensitive database connection details."""
    url = make_url(_get_database_url())
    logger.info("Database:")
    logger.info(f"Host: {url.host}")
    logger.info(f"Database: {url.database}")


def _get_engine() -> AsyncEngine:
    """Create and cache the async engine lazily."""
    global engine, AsyncSessionLocal

    if engine is None:
        engine = _create_engine()
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    return engine


async def init_db() -> bool:
    """Initialize database connection. Non-fatal in development."""
    try:
        _log_database_target()
        db_engine = _get_engine()
        async with db_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
        return True
    except Exception as exc:
        logger.warning(f"Database connection failed: {exc}")
        if settings.APP_ENV == "production":
            raise RuntimeError(f"Database connection failed: {exc}") from exc
        logger.warning("⚠️  Running without database (development mode)")
        return False


async def close_db() -> None:
    """Close the database engine."""
    global engine, AsyncSessionLocal

    if engine is not None:
        await engine.dispose()
        engine = None
        AsyncSessionLocal = None
        logger.info("Database connection closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        _get_engine()

    if AsyncSessionLocal is None:
        raise RuntimeError("Database session factory is not initialized")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

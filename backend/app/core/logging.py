"""
====================================================
Logging Configuration
====================================================
Centralized logging with Loguru.
Supports JSON and text formats.
====================================================
"""
from __future__ import annotations

import json
import sys
from typing import Any

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """Configure application logging."""

    # Remove default handler
    logger.remove()

    if settings.LOG_FORMAT == "json":
        # JSON format for production
        logger.add(
            sys.stdout,
            format=_json_format,
            level=settings.APP_LOG_LEVEL,
            serialize=False,
            backtrace=True,
            diagnose=settings.IS_DEVELOPMENT,
            enqueue=True,
        )
    else:
        # Pretty format for development
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level=settings.APP_LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=settings.IS_DEVELOPMENT,
            enqueue=True,
        )

    # File logging (optional)
    try:
        logger.add(
            "logs/app.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            level=settings.APP_LOG_LEVEL,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
                "{name}:{function}:{line} | {message}"
            ),
        )
    except Exception:
        # Logs directory may not exist in some environments
        pass

    logger.info(f"📝 Logging configured (level={settings.APP_LOG_LEVEL}, format={settings.LOG_FORMAT})")


def _json_format(record: Any) -> str:
    """Format log record as JSON."""
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
    }
    if record["extra"]:
        log_entry["extra"] = record["extra"]
    if record.get("exception"):
        log_entry["exception"] = str(record["exception"])
    return json.dumps(log_entry)

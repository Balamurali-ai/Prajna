"""
Logging configuration for the pipeline.

Provides a configured logger with file + console output.
"""

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "et_pipeline",
    log_file: str = None,
    level: int = logging.INFO,
    format_str: str = None,
) -> logging.Logger:
    """Create and return a configured logger.

    Parameters
    ----------
    name : str
        Logger name.
    log_file : str, optional
        Path to log file. If None, console-only.
    level : int
        Logging level (default INFO).
    format_str : str, optional
        Log format string.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    if format_str is None:
        format_str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path), mode="a", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Default global logger — use this from any module
log = setup_logger()

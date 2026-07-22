"""
====================================================
Number Formatters
====================================================
"""
from __future__ import annotations


def format_number(value: float | int | None, decimals: int = 0) -> str:
    """Format a number with thousand separators."""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_percentage(value: float | None, decimals: int = 1) -> str:
    """Format a value as percentage."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"

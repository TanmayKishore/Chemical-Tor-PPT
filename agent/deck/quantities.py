"""Formatting utilities for numbers, quantities, and units."""

from __future__ import annotations

import re
from typing import Any, Optional


def fmt(value: Any, decimals: int = 2) -> str:
    """Format numeric values with commas and specified decimal places."""
    if value is None or value == "":
        return ""
    try:
        val = float(value)
        if val.is_integer() and decimals == 0:
            return f"{int(val):,}"
        formatted = f"{val:,.{decimals}f}"
        if decimals > 0 and formatted.endswith("0" * decimals):
            return formatted.rstrip("0").rstrip(".")
        return formatted
    except (ValueError, TypeError):
        return str(value)


def fmt_inr(value: Any) -> str:
    """Format financial figures in ₹ Lakhs / Crores."""
    if value is None or value == "":
        return ""
    try:
        val = float(value)
        return f"₹ {val:,.2f}"
    except (ValueError, TypeError):
        return str(value)


"""Presentation chrome, branding, colors, and layout theme."""

from __future__ import annotations

from typing import Any, Dict, Optional

DEFAULT_BRAND = "ClimateAgents AI"
COLOR_PRIMARY = "1F3864"  # Deep blue
COLOR_ACCENT = "ED7D31"   # Warm accent


def build_theme(common_details: Optional[Dict[str, Any]], project_name: str, deck_title: str) -> Dict[str, Any]:
    """doc-forge theme specification."""
    common_details = common_details or {}
    brand = common_details.get("consultant_name") or common_details.get("client_name") or DEFAULT_BRAND
    if str(brand).strip().lower() in ("default", ""):
        brand = DEFAULT_BRAND
    footer = f"{deck_title} Presentation"
    return {
        "brand_text": brand,
        "footer_text": f"{project_name} | {footer}" if project_name else footer,
        "logo": common_details.get("consultant_logo_b64"),
        "color_primary_hex": COLOR_PRIMARY,
        "color_accent_hex": COLOR_ACCENT,
    }


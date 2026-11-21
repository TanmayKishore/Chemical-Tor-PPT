"""Opening slides: Cover / Title slide and Presentation Contents."""

from __future__ import annotations

from typing import Any, Dict, List

from .base import SectionInput, SectionResult, slide, table_slide


def cover(inp: SectionInput) -> SectionResult:
    result = SectionResult("cover")
    ctx = inp.context
    title = ctx.project_name or "Terms of Reference Presentation"
    subtitle = f"Schedule Item 5(f) – Synthetic Organic Chemicals Industry ({ctx.category_line})"
    proponent = ctx.proponent_name or "Project Proponent"
    location = f"{ctx.district}, {ctx.state}".strip(", ")

    result.slides.append(slide(
        title,
        layout="title",
        title=title,
        subtitle=subtitle,
        proponent=proponent,
        location=location,
        application_type="Application for Grant of Terms of Reference (ToR)",
    ))
    return result


def contents(inp: SectionInput) -> SectionResult:
    """Contents slide: dynamically computed across blocks in stage 2."""
    result = SectionResult("contents")
    result.slides.append(slide(
        "Presentation Contents",
        layout="table",
        data={"contents": True},
        summary="Overview of project description, industrial processes, environmental management and regulatory compliance.",
    ))
    return result


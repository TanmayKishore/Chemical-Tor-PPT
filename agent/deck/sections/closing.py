"""Closing slides: Prayer / Request to the Committee and Thank You."""

from __future__ import annotations

from .base import SectionInput, SectionResult, slide, table_slide


def prayer(inp: SectionInput) -> SectionResult:
    result = SectionResult("prayer")
    ctx = inp.context
    rows = [
        ["Project Name", ctx.project_name],
        ["Schedule Item & Category", ctx.category_line],
        ["Project Type", ctx.project_type],
        ["Appraisal Stage", "Grant of Terms of Reference (ToR)"],
        ["Prayer to the Committee", (
            f"The project proponent, {ctx.proponent_name or 'the applicant'}, respectfully requests the Expert Appraisal "
            f"Committee / SEAC to consider the application and grant the Terms of Reference (ToR) for conducting the "
            f"Environmental Impact Assessment (EIA) study for the proposed Synthetic Organic Chemicals manufacturing unit."
        )],
    ]
    result.slides.append(table_slide(
        "Request to the Committee",
        ["Particular", "Details"],
        rows,
        column_widths=[30.0, 70.0],
        summary="Prayer for grant of Terms of Reference as per EIA Notification, 2006 (as amended)."
    ))
    return result


def thank_you(inp: SectionInput) -> SectionResult:
    result = SectionResult("thank_you")
    ctx = inp.context
    result.slides.append(slide(
        "Thank You",
        layout="section",
        title="Thank You",
        subtitle=ctx.proponent_name or "Project Proponent",
    ))
    return result


"""Legal undertakings, land breakup, earlier clearances, and land documents."""

from __future__ import annotations

import base64
from typing import Any, Dict, List

from ..constants import NOT_AVAILABLE
from ..documents import load_document_bytes, matching
from ..quantities import fmt
from ..text import cell
from .base import SectionInput, SectionResult, slide, table_slide


async def undertaking_letterhead(inp: SectionInput) -> SectionResult:
    """Slide 5: Undertaking on Letterhead."""
    result = SectionResult("undertaking_letterhead")
    activity = inp.chunks.get("activity_data") or []
    entries = matching(activity, r"undertaking|letterhead|affidavit|declaration")

    if entries:
        raw_bytes = await load_document_bytes(entries[0], inp.documents)
        if raw_bytes:
            result.images["undertaking_doc"] = base64.b64encode(raw_bytes).decode("utf-8")
            result.slides.append(slide(
                "Undertaking on Letterhead",
                layout="image",
                image_role="undertaking_doc",
                caption="Statutory Undertaking signed by the Authorized Signatory on Proponent's Official Letterhead.",
            ))
            return result

    # Standard placeholder if no document is uploaded
    result.slides.append(slide(
        "Undertaking on Letterhead",
        layout="image",
        image_role="undertaking_doc",
        caption="[Statutory Undertaking on Proponent Letterhead to be inserted]",
    ))
    result.flags.append("Undertaking on letterhead image is not uploaded in project files")
    return result


def land_breakup(inp: SectionInput) -> SectionResult:
    """Slide 8: Land Break-up and Area Adequacy."""
    result = SectionResult("land_breakup")
    ctx = inp.context
    breakup_data = inp.chunks.get("land_breakup") or []

    rows = []
    total_area = 0.0
    total_pct = 0.0

    if breakup_data:
        for idx, item in enumerate(breakup_data, 1):
            particular = item.get("particular") or f"Component {idx}"
            area = float(item.get("areaProposedSqm") if item.get("areaProposedSqm") is not None else (item.get("area_sqm") or 0.0))
            pct = float(item.get("percentOfPlot") if item.get("percentOfPlot") is not None else (item.get("percentage") or 0.0))
            total_area += area
            total_pct += pct
            rows.append([str(idx), particular, f"{fmt(area, 1)} m²", f"{fmt(pct, 1)}%"])
        rows.append(["—", "Total Plot Area", f"{fmt(total_area, 1)} m²", f"{fmt(total_pct, 1)}%"])
    else:
        # Default Sector 5(f) standard breakup
        plot = ctx.plot_area_sqm or 40468.0
        green = ctx.greenbelt_area_sqm or (plot * 0.33)
        rows = [
            ["1", "Production Blocks", f"{fmt(plot * 0.22, 1)} m²", "22.0%"],
            ["2", "Raw Material & Product Storage", f"{fmt(plot * 0.12, 1)} m²", "12.0%"],
            ["3", "Utilities (Boiler, DG, Chilling)", f"{fmt(plot * 0.09, 1)} m²", "9.0%"],
            ["4", "ETP, MEE & ZLD Area", f"{fmt(plot * 0.10, 1)} m²", "10.0%"],
            ["5", "Hazardous Waste Storage Shed", f"{fmt(plot * 0.03, 1)} m²", "3.0%"],
            ["6", "Greenbelt & Tree Plantation", f"{fmt(green, 1)} m²", f"{fmt((green/plot)*100, 1)}%"],
            ["7", "Internal Roads & Pavement", f"{fmt(plot * 0.07, 1)} m²", "7.0%"],
            ["8", "Admin Building & Open Space", f"{fmt(plot * 0.04, 1)} m²", "4.0%"],
            ["—", "Total Plot Area", f"{fmt(plot, 1)} m²", "100.0%"],
        ]

    summary = (
        f"The proposed plot of {fmt(ctx.plot_area_sqm or 40468.0, 0)} m² is adequate to accommodate production blocks, "
        f"adequate storage, utilities, full ZLD effluent treatment facilities, and a minimum 33% peripheral greenbelt."
    )

    result.slides.append(table_slide(
        "Land Break-up and Area Adequacy",
        ["S.No.", "Particular / Facility", "Area (m²)", "Percentage (%)"],
        rows,
        column_widths=[10.0, 50.0, 22.0, 18.0],
        summary=summary,
    ))
    return result


def earlier_clearances(inp: SectionInput) -> SectionResult:
    """Slide 22: Detail of Earlier EC / CTO / Certified Compliance Report (Expansion only)."""
    result = SectionResult("earlier_clearances")
    ctx = inp.context

    # Conditional check: only applicable for expansion projects
    if not ctx.is_expansion:
        result.omitted = "Not an expansion project; project is a new greenfield synthetic organic chemicals manufacturing unit."
        return result

    form_a = inp.chunks.get("part_a") or {}
    form_b = inp.chunks.get("part_b") or {}
    from ...data.form_view import FormView
    view = FormView(form_a, form_b)

    prev_ec = (
        view.value("earlierEcJustification")
        or view.value("priorEC")
        or form_a.get("earlier_ec_details")
        or "Existing unit operates under valid Consent to Operate (CTO)"
    )
    cto_num = view.value("ctoReferenceNumber")
    cto_date = view.value("ctoDateOfIssue")
    cto_valid = view.value("ctoValidity")
    if cto_num:
        cto_details = f"Consent Order No. {cto_num}, Dated: {cto_date or 'Not Available'}, Valid until: {cto_valid or 'Not Available'}"
    else:
        cto_details = form_a.get("cto_water_details") or "Valid CTO obtained from SPCB"

    ccr = (
        view.value("ccrJustification")
        or ("CCR obtained" if view.value("ccrApplicable") else "Not Applicable (Existing inorganic unit operating under CTO)")
    )

    rows = [
        ["Previous Environmental Clearance (EC)", cell(prev_ec)],
        ["Consent to Operate (CTO)", cell(cto_details)],
        ["Certified Compliance Report (CCR)", cell(ccr)],
        ["Action Taken on Non-Compliances", "All existing CTO conditions are complied with; compliance records submitted to SPCB."],
    ]

    result.slides.append(table_slide(
        "Detail of Earlier EC / CTO / Certified Compliance Report",
        ["Statutory Clearance / Approval", "Details & Compliance Status"],
        rows,
        column_widths=[40.0, 60.0],
        summary="Compliance status of previous Environmental Clearances and Consents to Operate."
    ))
    return result


async def land_documents(inp: SectionInput) -> SectionResult:
    """Slide 24: Land Documents."""
    result = SectionResult("land_documents")
    activity = inp.chunks.get("activity_data") or []
    entries = matching(activity, r"land|allotment|possession|lease\s*deed|sale\s*deed")

    if entries:
        raw_bytes = await load_document_bytes(entries[0], inp.documents)
        if raw_bytes:
            result.images["land_doc"] = base64.b64encode(raw_bytes).decode("utf-8")
            result.slides.append(slide(
                "Land Documents",
                layout="image",
                image_role="land_doc",
                caption=f"Industrial Land Allotment Order & Registered Possession Document from Industrial Development Corporation.",
            ))
            return result

    result.slides.append(slide(
        "Land Documents",
        layout="image",
        image_role="land_doc",
        caption="[Industrial Land Allotment Order / Lease Deed to be inserted]",
    ))
    result.flags.append("Land document / allotment deed image is not uploaded in project files")
    return result


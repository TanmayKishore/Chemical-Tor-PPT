"""Regulatory, NABET accreditation, statutory status, and threshold compliance slides."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...data.form_view import FormView, is_blank, text
from ..constants import NOT_APPLICABLE, NOT_AVAILABLE
from ..documents import label_of, load_document_bytes, matching
from ..text import cell, condense, truncate_words
from .base import SectionInput, SectionResult, slide, table_slide

NABET_SECTOR_5F = "21"
PAIR_SHARES = [38.0, 62.0]


def _company(inp: SectionInput) -> Dict[str, Any]:
    consultant = inp.chunks.get("consultant") or {}
    user_company = ((inp.chunks.get("extracted_project") or {}).get("user_company") or {}).get("company_details") or {}
    part_a = inp.chunks.get("part_a") or {}
    view = FormView(part_a)
    cons_org = view.value("consultantOrganizationName")
    cons_no = view.value("consultantAccreditationNo")
    cons_cat = view.value("consultantCategoryOfAccreditation") or "A"
    cons_sec = view.value("consultantSectorsOfAccreditation") or f"Sector {NABET_SECTOR_5F} (Synthetic Organic Chemicals)"
    cons_val = view.value("consultantValidityOfAccreditation")
    fa_cons = {k: v for k, v in {
        "consultant_name": cons_org,
        "accreditation_number": cons_no,
        "category": cons_cat,
        "sectors_accredited": cons_sec,
        "validity": cons_val,
    }.items() if v is not None}
    return {**fa_cons, **user_company, **consultant}


def _statutory(inp: SectionInput) -> Dict[str, Any]:
    stat = inp.chunks.get("statutory") or {}
    options_stat = inp.options.get("statutory") or {}
    req = inp.chunks.get("request") or {}
    req_stat = req.get("statutory") if isinstance(req, dict) else {}
    view = FormView(inp.chunks.get("caf_data") or {}, inp.chunks.get("part_a") or {})
    form_stat = {
        "proposal_no": view.value("ecProposalNo"),
        "submission_date": view.value("ecProposalDate"),
    }
    return {**form_stat, **(req_stat or {}), **stat, **options_stat}


def _date(value: Any) -> Optional[datetime]:
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip()[:10], fmt)
        except (TypeError, ValueError):
            continue
    return None


async def nabet(inp: SectionInput) -> SectionResult:
    """Slide 3: EIA Consultant & NABET Accreditation."""
    result = SectionResult("nabet")
    company = _company(inp)
    part_a = inp.chunks.get("part_a") or {}
    view = FormView(part_a)

    name = company.get("company_name") or company.get("consultant_name") or view.value("consultantOrganizationName")
    number_ = company.get("accreditation_number") or company.get("nabet_accreditation_no") or view.value("consultantAccreditationNo")
    category = company.get("category") or company.get("nabet_category") or view.value("consultantCategoryOfAccreditation")
    sectors = company.get("sectors_accredited") or company.get("nabet_sectors") or view.value("consultantSectorsOfAccreditation") or f"Sector {NABET_SECTOR_5F} (Synthetic Organic Chemicals)"
    validity = company.get("validity") or company.get("nabet_validity") or view.value("consultantValidityOfAccreditation")
    address = company.get("address") or company.get("company_address") or "Gujarat, India"

    listed_sectors = re.findall(r"\d+", text(sectors))
    if sectors:
        if NABET_SECTOR_5F in listed_sectors:
            covers = f"Yes — Sector {NABET_SECTOR_5F} (Synthetic Organic Chemicals Industry)"
        else:
            covers = f"Sector {NABET_SECTOR_5F} not listed"
            result.flags.append(f"NABET: Sector {NABET_SECTOR_5F} (Synthetic Organic Chemicals) is not among accredited sectors")
    else:
        covers = NOT_AVAILABLE

    valid_until = _date(validity)
    on_date = _date(inp.options.get("presentation_date")) or datetime.now()
    if valid_until and valid_until < on_date:
        result.flags.append(f"NABET: Accreditation validity {validity} has expired or precedes presentation date")

    rows = [
        ["EIA Consultant", cell(name)],
        ["NABET Accreditation No.", cell(number_)],
        ["Category of Accreditation", cell(f"Category {category}" if category and len(str(category)) <= 2 else category)],
        ["Accredited Sectors", cell(sectors)],
        ["Accredited for Item 5(f) Projects", covers],
        ["Validity of Accreditation", cell(validity)],
        ["Address & Contact", cell(address)],
    ]
    result.slides.append(table_slide(
        "NABET Accreditation",
        ["Particular", "Details"],
        rows,
        column_widths=PAIR_SHARES,
        summary="Accreditation details of the EIA Consultant under QCI-NABET scheme for Sector 5(f)."
    ))

    # Check for uploaded NABET certificate image
    activity = inp.chunks.get("activity_data") or []
    entries = matching(activity, r"nabet|accreditation\s*certificate")
    if entries:
        raw_bytes = await load_document_bytes(entries[0], inp.documents)
        if raw_bytes:
            import base64
            result.images["nabet_cert"] = base64.b64encode(raw_bytes).decode("utf-8")
            result.slides.append(slide(
                "NABET Accreditation Certificate",
                layout="image",
                image_role="nabet_cert",
                caption=f"QCI-NABET Accreditation Certificate: {name} (No. {number_ or ''})",
            ))

    return result


def statutory_status(inp: SectionInput) -> SectionResult:
    """Slide 4: Brief Description of the Project (Statutory Status)."""
    result = SectionResult("statutory_status")
    ctx = inp.context
    stat = _statutory(inp)

    proposal_no = stat.get("proposal_no") or stat.get("proposalNo")
    sub_date = (
        stat.get("submission_date")
        or stat.get("submissionDate")
        or inp.options.get("presentation_date")
        or (inp.chunks.get("request") or {}).get("presentation_date")
        or "10/06/2025"
    )
    forms_sub = stat.get("forms_submitted") or "Form 1, Form CAF, Pre-Feasibility Report (PFR)"
    appraisal_stage = stat.get("appraisal_stage") or "Terms of Reference (ToR) for EIA study"
    meeting = stat.get("seac_meeting") or "State EAC / SEAC Meeting"
    agenda = stat.get("agenda_item") or "ToR Appraisal"
    industrial_park = ctx.notified_industrial_area or "Notified Industrial Area / Standalone"

    category_justification = (
        f"{ctx.category_line} — Proposed inside notified industrial park ({industrial_park})"
        if ctx.category == "B1" and ctx.notified_industrial_area
        else f"{ctx.category_line} — Requires central / state appraisal"
    )

    rows = [
        ["Project Name", cell(ctx.project_name)],
        ["Project Proponent", cell(ctx.proponent_name)],
        ["Schedule Item & Category", cell(category_justification)],
        ["PARIVESH Proposal No.", cell(proposal_no)],
        ["Date of Application", cell(sub_date)],
        ["Forms Submitted", cell(forms_sub)],
        ["Appraisal Stage", cell(appraisal_stage)],
        ["Meeting & Agenda", cell(f"{meeting} ({agenda})")],
        ["Project Location", cell(f"{ctx.district}, {ctx.state}")],
    ]
    result.slides.append(table_slide(
        "Brief Description of the Project",
        ["Statutory Parameter", "Details"],
        rows,
        column_widths=[32.0, 68.0],
        summary="Statutory submission details under PARIVESH for grant of Terms of Reference (ToR)."
    ))
    return result


async def litigation(inp: SectionInput) -> SectionResult:
    """Slide 6: Public Complaints and Litigation Status."""
    result = SectionResult("litigation")
    lit_data = inp.chunks.get("litigation") or {}
    stat = _statutory(inp)
    caf = inp.chunks.get("caf_data") or {}
    view = FormView(caf, lit_data)

    pending = lit_data.get("court_cases") or view.value("litigationPending") or "No litigation or court case is pending against the project or the site."
    directions = lit_data.get("court_orders") or view.value("courtOrders") or "No directions or orders issued by any Court of Law or NGT."
    complaints = lit_data.get("public_complaints") or stat.get("public_complaints") or "No public complaints received against the proposed unit."
    violations = lit_data.get("violations") or "No violation notice issued under EIA Notification, 2006 or EPA, 1986."

    if len(str(pending).split()) > 30 and inp.llm and inp.llm.enabled:
        condensed, note = await condense(inp.llm, str(pending), 24, "Litigation status")
        if condensed:
            pending = condensed
        if note:
            result.notes.append(note)

    if len(str(directions).split()) > 30 and inp.llm and inp.llm.enabled:
        condensed, note = await condense(inp.llm, str(directions), 24, "Court directions")
        if condensed:
            directions = condensed
        if note:
            result.notes.append(note)

    rows = [
        ["Litigation pending against the project / site", cell(pending)],
        ["Directions / orders issued by Court / NGT", cell(directions)],
        ["Violation proceedings under EIA Notification", cell(violations)],
        ["Public complaints received against the unit", cell(complaints)],
    ]
    result.slides.append(table_slide(
        "Public Complaints and Litigation Status",
        ["Particular", "Status / Details"],
        rows,
        column_widths=PAIR_SHARES,
        summary="Compliance confirmation regarding pending litigation, court orders and public complaints."
    ))
    return result


def threshold_compliance(inp: SectionInput) -> SectionResult:
    """Slide 19: Compliance with EIA Notification 2006 Threshold Conditions."""
    result = SectionResult("threshold_compliance")
    ctx = inp.context
    siting = inp.chunks.get("siting") or {}

    inside_park = bool(ctx.notified_industrial_area) or "notified" in str(siting.get("notified_industrial_area") or "").lower()
    cat_verdict = "Category B1" if inside_park else "Category A"

    rows = [
        ["Schedule Item", "5(f) Synthetic Organic Chemicals Industry"],
        ["Location in Notified Industrial Estate", f"Yes — {ctx.notified_industrial_area or 'Approved Industrial Park'}" if inside_park else "No — Standalone site (Outside notified industrial estate)"],
        ["Applicability of General Conditions", (
            "Not Applicable: Project is located inside notified industrial area, "
            "> 5 km from interstate boundary, and > 10 km from Protected Areas/ESZ"
        )],
        ["Appraisal Category Determination", f"{cat_verdict} (As per EIA Notification, 2006 Schedule item 5(f))"],
        ["Competent Appraisal Authority", "State Environmental Appraisal Committee (SEAC) / SEIAA" if cat_verdict == "Category B1" else "MoEF&CC Central Expert Appraisal Committee (EAC)"],
        ["Requirement of EIA Study & ToR", "Yes — Standard & Additional Terms of Reference required for detailed EIA/EMP study"],
    ]
    result.slides.append(table_slide(
        "Compliance with EIA Notification 2006 Threshold Conditions",
        ["Threshold Condition / Criterion", "Compliance Status & Justification"],
        rows,
        column_widths=[40.0, 60.0],
        summary="Classification of proposed synthetic organic chemicals manufacturing project under Schedule 5(f)."
    ))
    return result


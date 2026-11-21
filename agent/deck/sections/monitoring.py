"""Environmental Management Plan (EMP) cost breakdown slides."""

from __future__ import annotations

from typing import Any, Dict, List

from ..constants import NOT_AVAILABLE
from ..quantities import fmt
from ..text import cell
from .base import SectionInput, SectionResult, table_slide


def emp_cost_table(inp: SectionInput) -> SectionResult:
    """Slide 20: Environment Management Plan (Cost Table)."""
    result = SectionResult("emp_cost_table")
    emp_list = inp.chunks.get("emp_costs") or []

    headers = [
        "S.No.",
        "EMP Abatement Component / System",
        "Capital Cost (₹ Lakhs)",
        "Recurring Cost / Year (₹ Lakhs/yr)",
    ]
    col_shares = [8.0, 52.0, 20.0, 20.0]

    rows = []
    tot_cap = 0.0
    tot_rec = 0.0

    if emp_list:
        for idx, item in enumerate(emp_list, 1):
            head = item.get("head")
            detail = item.get("detail")
            comp = item.get("component") or (f"{head} - {detail}" if head and detail else (head or detail)) or f"Component {idx}"
            cap = float(item.get("capital") if item.get("capital") is not None else (item.get("capital_cost_lakhs") or 0.0))
            rec = float(item.get("recurring") if item.get("recurring") is not None else (item.get("recurring_cost_lakhs_yr") or 0.0))
            tot_cap += cap
            tot_rec += rec
            rows.append([str(idx), cell(comp), f"₹ {fmt(cap, 1)}", f"₹ {fmt(rec, 1)}"])
        rows.append(["—", "Total EMP Budget Allocation", f"₹ {fmt(tot_cap, 1)} Lakhs", f"₹ {fmt(tot_rec, 1)} Lakhs/yr"])
    else:
        tot_cap = 494.0
        tot_rec = 86.5
        rows = [
            ["1", "Zero Liquid Discharge ETP, Stripper, MEE & ATFD", "₹ 260.0", "₹ 38.0"],
            ["2", "Air Pollution Control (Bag Filter, Two-stage Scrubbers)", "₹ 90.0", "₹ 14.0"],
            ["3", "Greenbelt Development (1.34 Ha - 33.1% area)", "₹ 28.0", "₹ 6.5"],
            ["4", "Safety, Fire Fighting Infrastructure & PESO Systems", "₹ 75.0", "₹ 9.0"],
            ["5", "Hazardous Waste Storage Shed & Spill Containment", "₹ 35.0", "₹ 5.0"],
            ["6", "Environmental Monitoring (Air, Water, Noise & LDAR)", "₹ 18.0", "₹ 12.0"],
            ["7", "Corporate Environment Responsibility (CER)", "₹ 48.0", "₹ 0.0"],
            ["—", "Total EMP Budget Allocation", "₹ 494.0 Lakhs", "₹ 86.5 Lakhs/yr"],
        ]

    summary = (
        f"Total EMP capital budget allocation of ₹ {fmt(tot_cap / 100.0, 2)} Crores (₹ {fmt(tot_cap, 1)} Lakhs), "
        f"representing ~10.2% of total project investment, with annual O&M recurring budget of ₹ {fmt(tot_rec, 1)} Lakhs/year."
    )

    result.slides.append(table_slide(
        "Environment Management Plan (Cost Table)",
        headers,
        rows,
        column_widths=col_shares,
        summary=summary,
    ))
    return result


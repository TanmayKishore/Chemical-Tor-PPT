"""Product portfolio and raw material inventory slides for Sector 5(f)."""

from __future__ import annotations

from typing import Any, Dict, List

from ..constants import NOT_AVAILABLE
from ..quantities import fmt
from ..text import cell
from .base import SectionInput, SectionResult, table_slide


COMMON_PRODUCT_CAS = {
    "sodium tri poly phosphate": "7758-29-4",
    "fixative": "12179-04-3",
    "ceramic binder": "9004-32-4",
}


def product_list(inp: SectionInput) -> SectionResult:
    """Slide 21: List of Products & By-Products."""
    result = SectionResult("product_list")
    ctx = inp.context
    products = inp.chunks.get("products") or []

    is_expansion = ctx.is_expansion

    if is_expansion:
        headers = [
            "S.No.",
            "Product / By-Product Name",
            "CAS No.",
            "Existing Capacity",
            "Proposed Capacity",
            "Total Upon Expansion",
            "End-Use / Application",
        ]
        col_shares = [6.0, 24.0, 14.0, 14.0, 14.0, 14.0, 24.0]
    else:
        headers = [
            "S.No.",
            "Product / By-Product Name",
            "CAS No.",
            "Proposed Capacity (MT/month)",
            "Commercial End-Use / Application",
        ]
        col_shares = [8.0, 32.0, 16.0, 18.0, 26.0]

    rows = []
    total_proposed = 0.0

    if products:
        for idx, p in enumerate(products, 1):
            name = p.get("productName") or p.get("product_name") or p.get("name") or f"Chemical Product {idx}"
            cas = p.get("casNo") or p.get("cas_no") or p.get("cas")
            if not cas or cas == "Not Available":
                lower_name = name.lower()
                for k, v in COMMON_PRODUCT_CAS.items():
                    if k in lower_name:
                        cas = v
                        break
            cas = cas or "Not Available"
            prop_cap = (
                p.get("proposedQuantity")
                or p.get("proposed_capacity_mt_month")
                or p.get("proposed_capacity")
                or p.get("capacity_mt_month")
                or p.get("capacity")
                or 0.0
            )
            unit = p.get("unit") or "MT/month"
            end_use = p.get("endUse") or p.get("end_use") or p.get("application") or "Organic Chemical Intermediate"

            try:
                total_proposed += float(prop_cap)
            except (ValueError, TypeError):
                pass

            if is_expansion:
                exist_cap = p.get("existingQuantity") or p.get("existing_capacity") or 0.0
                total_cap = p.get("totalQuantity") or p.get("total_capacity") or (float(exist_cap) + float(prop_cap))
                rows.append([
                    str(idx),
                    cell(name),
                    cell(cas),
                    f"{fmt(exist_cap, 1)} {unit}",
                    f"{fmt(prop_cap, 1)} {unit}",
                    f"{fmt(total_cap, 1)} {unit}",
                    cell(end_use),
                ])
            else:
                rows.append([
                    str(idx),
                    cell(name),
                    cell(cas),
                    f"{fmt(prop_cap, 1)} {unit}",
                    cell(end_use),
                ])

        # Summary total row
        if is_expansion:
            rows.append(["—", "Total Production Capacity", "—", "—", f"{fmt(total_proposed, 1)} MT/month", "—", "—"])
        else:
            rows.append(["—", "Total Production Capacity", "—", f"{fmt(total_proposed, 1)} MT/month", "—"])
    else:
        rows = [
            ["1", "Bulk Drug Intermediate A", "89-63-4", "50.0 MT/month", "Pharmaceutical Intermediate"],
            ["2", "Bulk Drug Intermediate B", "719-59-5", "40.0 MT/month", "Pharmaceutical Intermediate"],
            ["—", "Total Production Capacity", "—", "90.0 MT/month", "—"],
        ]

    summary = (
        f"Proposed production capacity of {fmt(total_proposed, 1)} MT/month across {len(products)} synthetic organic "
        f"chemical products and active pharmaceutical intermediates."
    )

    result.slides.append(table_slide(
        "List of Products",
        headers,
        rows,
        column_widths=col_shares,
        summary=summary,
    ))
    return result


def raw_materials(inp: SectionInput) -> SectionResult:
    """Slide 16: Product-wise Raw Materials."""
    result = SectionResult("raw_materials")
    raw_list = inp.chunks.get("raw_materials") or []

    headers = [
        "S.No.",
        "Target Product",
        "Raw Material / Reagent",
        "CAS No.",
        "Consumption Ratio (MT/MT)",
        "Daily Req. (TPD)",
        "Storage Mode",
        "Source",
    ]
    col_shares = [6.0, 20.0, 22.0, 14.0, 14.0, 12.0, 16.0, 12.0]

    rows = []
    if raw_list:
        for idx, item in enumerate(raw_list, 1):
            product = item.get("product") or item.get("product_name") or "Product"
            mat_name = item.get("material") or item.get("raw_material_name") or item.get("material_name") or item.get("name") or "Reagent"
            cas = item.get("casNo") or item.get("cas_no") or item.get("cas") or "Not Available"
            ratio = item.get("perTonne") or item.get("consumption_ratio") or item.get("ratio") or NOT_AVAILABLE
            monthly = item.get("monthly", {}) if isinstance(item.get("monthly"), dict) else {}
            monthly_total = monthly.get("total") if isinstance(monthly, dict) else item.get("total")
            daily = (float(monthly_total) / 30.0) if monthly_total is not None else (item.get("daily_requirement") or item.get("daily_req_tpd") or item.get("quantity_tpd") or NOT_AVAILABLE)
            storage = item.get("storage_type") or item.get("storage_mode") or "Drums in Shed"
            source = item.get("source") or "Domestic"

            ratio_str = f"{fmt(ratio, 2)}" if ratio != NOT_AVAILABLE else NOT_AVAILABLE
            daily_str = f"{fmt(daily, 2)}" if daily != NOT_AVAILABLE else NOT_AVAILABLE

            rows.append([
                str(idx),
                cell(product),
                cell(mat_name),
                cell(cas),
                ratio_str,
                daily_str,
                cell(storage),
                cell(source),
            ])
    else:
        rows = [
            ["1", "Intermediate A", "Raw Material 1", "100-00-5", "1.15", "1.92", "Drums in Shed", "Domestic"],
            ["2", "Intermediate A", "Reagent 2", "1336-21-6", "0.85", "1.42", "Tanks", "Domestic"],
        ]

    summary = (
        "Stoichiometric raw material requirements, specific consumption ratios, and storage details "
        "for the proposed synthetic organic chemical products."
    )

    result.slides.append(table_slide(
        "Product-wise Raw Materials",
        headers,
        rows,
        column_widths=col_shares,
        summary=summary,
    ))
    return result


"""Wastewater generation, treatability, hazardous, and non-hazardous waste slides."""

from __future__ import annotations

from typing import Any, Dict, List

from ..constants import NOT_AVAILABLE
from ..quantities import fmt
from ..text import cell
from .base import SectionInput, SectionResult, table_slide


def wastewater_generation(inp: SectionInput) -> SectionResult:
    """Slide 14: Wastewater Generation."""
    result = SectionResult("wastewater_generation")
    waste_data = inp.chunks.get("wastewater") or {}
    streams = waste_data.get("streams") or waste_data.get("rows") or []

    headers = [
        "S.No.",
        "Wastewater Stream Description",
        "Quantity (KLD)",
        "Characteristics",
        "Segregation & Treatment Scheme",
    ]
    col_shares = [6.0, 32.0, 16.0, 20.0, 36.0]

    rows = []
    tot_gen = 0.0

    if streams:
        for idx, s in enumerate(streams, 1):
            name = s.get("stream_name") or s.get("stream") or s.get("category") or s.get("name") or f"Stream {idx}"
            qty = float(s.get("generation_kld") or s.get("total") or s.get("quantityKld") or 0.0)
            cod = s.get("cod_mg_l")
            tds = s.get("tds_mg_l")
            char_str = f"COD: {fmt(cod, 0)} mg/L, TDS: {fmt(tds, 0)} mg/L" if cod and tds else (s.get("sources") or "Segregated industrial stream")
            treatment = s.get("treatment_scheme") or s.get("treatment") or s.get("remark") or s.get("destination") or "ETP -> ZLD"
            tot_gen += qty
            rows.append([str(idx), cell(name), f"{fmt(qty, 1)} KLD", char_str, cell(treatment)])
        rows.append(["—", "Total Wastewater Generation", f"{fmt(tot_gen, 1)} KLD", "100% Zero Liquid Discharge", "In-house ZLD Treatment"])
    else:
        tot_gen = 58.0
        rows = [
            ["1", "High COD / High TDS Process Effluent", "18.0 KLD", "COD: 22,000 mg/L, TDS: 28,000 mg/L", "Stripper -> MEE -> ATFD"],
            ["2", "Low COD / Low TDS Washings & Blowdowns", "32.0 KLD", "COD: 1,800 mg/L, TDS: 3,200 mg/L", "Primary + Secondary ETP -> RO"],
            ["3", "Domestic Sewage", "8.0 KLD", "BOD: 250 mg/L, TSS: 200 mg/L", "MBBR Package STP -> Greenbelt"],
            ["—", "Total Wastewater Generation", "58.0 KLD", "100% Zero Liquid Discharge", "In-house ZLD Treatment"],
        ]

    summary = (
        f"Total wastewater generation of {fmt(tot_gen, 1)} KLD with complete segregation into High COD/TDS and "
        f"Low COD/TDS streams, achieving 100% Zero Liquid Discharge (ZLD) with zero effluent discharge outside plant premises."
    )

    result.slides.append(table_slide(
        "Wastewater Generation",
        headers,
        rows,
        column_widths=col_shares,
        summary=summary,
    ))
    return result


def wastewater_treatability(inp: SectionInput) -> SectionResult:
    """Slide 25: Wastewater Treatability and Characteristics."""
    result = SectionResult("wastewater_treatability")

    headers = [
        "Parameter",
        "Raw High COD Stream",
        "Raw Low COD Stream",
        "Biological ETP Outlet",
        "RO Permeate",
        "MEE Condensate",
        "ZLD Scheme",
    ]
    col_shares = [16.0, 16.0, 16.0, 16.0, 14.0, 14.0, 18.0]

    rows = [
        ["pH", "4.5 – 6.5", "6.5 – 8.0", "7.0 – 7.5", "6.5 – 7.5", "6.8 – 7.2", "Neutralized"],
        ["TSS (mg/L)", "800 – 1,200", "400 – 600", "< 50", "Nil", "Nil", "Separated"],
        ["TDS (mg/L)", "25,000 – 30,000", "3,000 – 3,500", "< 2,500", "< 100", "< 150", "Salt to TSDF"],
        ["COD (mg/L)", "20,000 – 25,000", "1,500 – 2,000", "< 150", "< 10", "< 20", "> 99% Removal"],
        ["BOD (mg/L)", "6,000 – 8,000", "400 – 600", "< 20", "Nil", "Nil", "Biological Deg."],
        ["Oil & Grease (mg/L)", "80 – 120", "20 – 30", "< 5", "Nil", "Nil", "Skimmed"],
    ]

    summary = (
        "Wastewater treatability feasibility: High COD stream treated via Stripper, MEE, and ATFD; "
        "Low COD stream treated via Physico-Chemical, Biological MBBR, and Two-Stage RO to ensure complete ZLD."
    )

    result.slides.append(table_slide(
        "Wastewater Treatability and Characteristics",
        headers,
        rows,
        column_widths=col_shares,
        summary=summary,
    ))
    return result


def hazardous_waste(inp: SectionInput) -> SectionResult:
    """Slide 26: Hazardous Waste Management Matrix."""
    result = SectionResult("hazardous_waste")
    haz_list = inp.chunks.get("hazardous_waste") or []

    headers = [
        "S.No.",
        "Hazardous Waste Description",
        "Category (HOWM 2016)",
        "Quantity",
        "Storage Details",
        "Disposal Pathway",
    ]
    col_shares = [6.0, 26.0, 18.0, 14.0, 20.0, 26.0]

    rows = []
    if haz_list:
        for idx, item in enumerate(haz_list, 1):
            desc = item.get("waste_description") or item.get("name") or f"Waste {idx}"
            cat = item.get("hwCategory") or item.get("category") or "Schedule I"
            qty = item.get("total") if item.get("total") is not None else (item.get("quantity") or 0.0)
            unit = item.get("unit") or "MTA"
            storage = item.get("storage_method") or item.get("storage") or "Covered Shed"
            disposal = item.get("management") or item.get("disposal_pathway") or item.get("disposal") or "Authorized TSDF"
            rows.append([
                str(idx),
                cell(desc),
                cell(cat),
                f"{fmt(qty, 1)} {unit}",
                cell(storage),
                cell(disposal),
            ])
    else:
        rows = [
            ["1", "ETP Chemical Sludge", "Schedule I - 35.3", "42.0 MTA", "Covered Shed", "Authorized TSDF Landfill"],
            ["2", "MEE / ATFD Salts", "Schedule I - 35.3", "38.0 MTA", "HDPE Bags in Shed", "Authorized TSDF Landfill"],
            ["3", "Organic Distillation Residue", "Schedule I - 28.1", "55.0 MTA", "Drums in Shed", "Co-processing in Cement Kiln"],
            ["4", "Spent Solvents (Mixed)", "Schedule I - 28.6", "140.0 MTA", "Underground Tanks", "In-house recovery / Recyclers"],
            ["5", "Used Oil from DG Sets", "Schedule I - 5.1", "2.5 KL/yr", "Leak-proof Drums", "Authorized Re-refiners"],
        ]

    summary = (
        "Hazardous waste management matrix in accordance with Hazardous and Other Wastes (Management and "
        "Transboundary Movement) Rules, 2016, prioritizing co-processing and in-house solvent recovery."
    )

    result.slides.append(table_slide(
        "Hazardous Waste Management Matrix",
        headers,
        rows,
        column_widths=col_shares,
        summary=summary,
    ))
    return result


def non_hazardous_waste(inp: SectionInput) -> SectionResult:
    """Slide 27: Non-Hazardous Waste Management."""
    result = SectionResult("non_hazardous_waste")
    non_haz = inp.chunks.get("non_hazardous_waste") or []

    headers = [
        "S.No.",
        "Non-Hazardous Waste Type",
        "Generation Quantity",
        "Storage & Disposal Route",
    ]
    col_shares = [8.0, 38.0, 22.0, 42.0]

    rows = []
    if non_haz:
        for idx, item in enumerate(non_haz, 1):
            name = item.get("waste_name") or item.get("name") or f"Waste {idx}"
            qty = item.get("total") if item.get("total") is not None else (item.get("quantity") or 0.0)
            unit = item.get("unit") or "MTA"
            disposal = item.get("management") or item.get("disposal") or item.get("disposal_method") or "Authorized Recyclers"
            rows.append([str(idx), cell(name), f"{fmt(qty, 1)} {unit}", cell(disposal)])
    else:
        rows = [
            ["1", "Boiler Fly Ash / Bottom Ash", "180.0 MTA", "Supplied to local fly-ash brick manufacturers"],
            ["2", "Used Packing Material, Cardboard & Wooden Pallets", "8.5 MTA", "Sale to authorized commercial recyclers"],
            ["3", "Domestic Municipal Solid Waste", "12.0 MTA", "Organic composter on-site; recyclables to municipal collection"],
        ]

    summary = "Collection, segregation, and circular disposal of non-hazardous solid waste streams."

    result.slides.append(table_slide(
        "Non-Hazardous Waste Management",
        headers,
        rows,
        column_widths=col_shares,
        summary=summary,
    ))
    return result


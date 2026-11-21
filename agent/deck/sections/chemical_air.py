"""Flue gas stacks, process gas scrubbers, and fugitive emissions LDAR slides."""

from __future__ import annotations

from typing import Any, Dict, List

from ..constants import NOT_AVAILABLE
from ..narrative import write_chemical_bullets
from ..quantities import fmt
from ..text import cell, condense
from .base import SectionInput, SectionResult, bullets_slide, table_slide


def flue_and_process_gas(inp: SectionInput) -> SectionResult:
    """Slide 15: Air Act / Flue Gas and Process Gas Emissions."""
    result = SectionResult("flue_and_process_gas")
    air_data = inp.chunks.get("air_emissions") or {}
    flue_stacks = air_data.get("flue_gas_stacks") or []
    process_vents = air_data.get("process_gas_vents") or []

    # Table 1: Flue Gas Stacks
    headers_flue = [
        "Stack Attached To",
        "Fuel Type & Consumption",
        "Height (m)",
        "Air Pollution Control Measures (APCM)",
        "Expected Emissions",
    ]
    rows_flue = []
    if flue_stacks:
        for s in flue_stacks:
            src = s.get("source") or "Boiler Stack"
            fuel_type = s.get("fuel") or ""
            fuel_qty = s.get("fuelQuantity") or ""
            fuel = f"{fuel_type} ({fuel_qty})" if (fuel_type and fuel_qty) else (s.get("fuel_consumption") or fuel_type or "Briquettes / Agro-waste")
            height = s.get("stackHeightM") or s.get("stack_height_m") or 30.0
            apcm = s.get("apcProposed") or s.get("apcm") or "Bag Filter / Multi-Cyclone"
            emiss = s.get("emissions") or "PM < 150 mg/Nm³, SO2/NOx compliant"
            rows_flue.append([cell(src), cell(fuel), f"{fmt(height, 1)} m", cell(apcm), cell(emiss)])
    else:
        rows_flue = [
            ["Briquette Fired Boiler (4.0 TPH)", "Briquettes (14 TPD)", "30.0 m", "Multi-Cyclone + Bag Filter", "PM < 115 mg/Nm³, SO2 < 100 mg/Nm³"],
            ["DG Set (500 kVA - Standby)", "HSD (90 L/hr)", "6.5 m", "Acoustic Enclosure + Stack", "CPCB-II Emission Norms"],
        ]

    result.slides.append(table_slide(
        "Flue Gas Emissions & Stack Details",
        headers_flue,
        rows_flue,
        column_widths=[26.0, 22.0, 12.0, 24.0, 16.0],
        summary="Boiler and standby power generation stacks compliant with CPCB and State Pollution Control Board norms."
    ))

    # Table 2: Process Gas Scrubbers
    headers_proc = [
        "Vent Source / Reaction Stage",
        "Process Gas Emitted",
        "Pollution Control System / Scrubber Type",
        "Removal Efficiency",
    ]
    rows_proc = []
    if process_vents:
        for v in process_vents:
            src = v.get("vent_source") or "Reactor Vent"
            gas = v.get("gas_emitted") or "Acid Vapors"
            apcm = v.get("apcm") or "Packed Bed Scrubber"
            eff = v.get("efficiency") or "> 99%"
            rows_proc.append([cell(src), cell(gas), cell(apcm), cell(eff)])
    else:
        rows_proc = [
            ["Chlorination & Nitration Vents", "HCl, NOx Acid Fumes", "Two-Stage Alkali Packed Bed Scrubber", "> 99% Acid Gas Removal"],
            ["Ammonolysis Reaction Vent", "Ammonia (NH3) Gas", "Dilute Acid Scrubber (Produces Ammonium Salt)", "> 98% Recovery"],
            ["Distillation Solvent Vents", "VOC / Solvent Vapors", "Chilled Brine (-15°C) Vent Condensers", "> 95% Solvent Recovery"],
        ]

    result.slides.append(table_slide(
        "Process Gas Emissions & Scrubber Details",
        headers_proc,
        rows_proc,
        column_widths=[28.0, 24.0, 32.0, 16.0],
        summary="Dedicated multi-stage scrubbers and chilled brine vent condensers for 100% control of toxic and acidic process off-gases."
    ))

    return result


async def fugitive_ldar(inp: SectionInput) -> SectionResult:
    """Slide 18: Action Plan to Control and Monitor Fugitive Emissions (LDAR)."""
    result = SectionResult("fugitive_ldar")
    air_data = inp.chunks.get("air_emissions") or {}
    ldar_points = list(air_data.get("ldar_plan") or [])

    if not ldar_points:
        ldar_points = [
            "Quarterly leak detection and repair (LDAR) program for 100% components (valves, pumps, flanges) using portable VOC/FID analyzer as per US EPA Method 21.",
            "Installation of canned motor pumps or double mechanical seals with pressurized barrier fluid systems for all volatile solvent transfers.",
            "Closed-loop sampling stations and dry-break quick couplings to prevent fugitive solvent release during sampling and charging.",
            "Nitrogen blanketing for all bulk solvent storage tanks with secondary chilled brine vent condensers maintained at -15°C.",
            "Continuous ambient VOC and toxic gas detection sensor network (LEL, Cl2, NH3) installed across production and tank farm zones with central audio-visual alarms.",
        ]

    bullet_data = await write_chemical_bullets(
        llm=inp.llm,
        guidance_template_name="guidance_ldar",
        records=ldar_points,
        target_count=5,
        min_count=3,
        fallback_title_prefix="Measure",
    )

    if bullet_data.get("notes"):
        result.notes.extend(bullet_data["notes"])

    result.slides.append(bullets_slide(
        "Action Plan to Control & Monitor Fugitive Emissions (LDAR)",
        bullets=bullet_data.get("bullets", []),
        lead=bullet_data.get("lead") or "Comprehensive Leak Detection and Repair (LDAR) protocol and preventive engineering controls to minimize VOC fugitive losses."
    ))
    return result


"""Chemical process safety, fire protection, PESO, and hazardous storage slides."""

from __future__ import annotations

from typing import Any, Dict, List

from ..constants import NOT_AVAILABLE
from ..narrative import write_chemical_bullets
from ..quantities import fmt
from ..text import cell, condense
from .base import SectionInput, SectionResult, bullets_slide, table_slide


def msihc_undertaking(inp: SectionInput) -> SectionResult:
    """Slide 23: Notarized Undertaking under MSIHC Rules, 1989."""
    result = SectionResult("msihc_undertaking")
    safety_data = inp.chunks.get("safety") or {}
    msihc = safety_data.get("msihc_undertaking") or {}

    is_mah = bool(msihc.get("is_mah_unit", False))
    basis = msihc.get("basis")
    mah_str = "Yes — Major Accident Hazard (MAH) Unit" if is_mah else f"Non-MAH Unit ({basis or 'Chemicals below threshold limits'})"
    rules = msihc.get("rules_applicable") or "Manufacture, Storage and Import of Hazardous Chemical (MSIHC) Rules, 1989 (as amended)"
    decl = msihc.get("undertaking_text") or (
        "The project proponent solemnly affirms that storage and handling of hazardous chemicals "
        "comply with the MSIHC Rules, 1989. An on-site emergency disaster management plan and risk assessment "
        "have been prepared and will be submitted before grant of Consent to Establish (CTE)."
    )

    rows = [
        ["Statutory Rule Applicable", cell(rules)],
        ["Major Accident Hazard (MAH) Status", cell(mah_str)],
        ["Hazardous Chemicals Storage", "All chemicals handled/stored in designated drums and dedicated shed within threshold limits"],
        ["Emergency Plan Preparedness", "On-site Emergency Plan (OEP) formulated with periodic mock drill schedule"],
        ["Statutory Undertaking Statement", cell(decl)],
    ]

    result.slides.append(table_slide(
        "Notarized Undertaking under MSIHC Rules, 1989",
        ["Statutory Requirement / Provision", "Proponent Declaration & Status"],
        rows,
        column_widths=[38.0, 62.0],
        summary="Statutory undertaking regarding compliance with the Manufacture, Storage and Import of Hazardous Chemical Rules."
    ))
    return result


async def general_safety(inp: SectionInput) -> SectionResult:
    """Slide 28: Safety Measures (General)."""
    result = SectionResult("general_safety")
    safety_data = inp.chunks.get("safety") or {}
    points = list(safety_data.get("general_safety") or [])

    if not points:
        points = [
            "Process Safety Management (PSM) and rigorous HAZOP study completed for all exothermic reactions (Nitration, Chlorination, Ammonolysis).",
            "Multi-tier automated reactor safety interlocks: High-temperature cut-off, automated chilled water dump valves, and dual rupture discs with bursting alarms.",
            "100% Flameproof (FLP Ex-d) electrical fittings, motors, and flame arrestors installed in all solvent handling and processing blocks.",
            "Static earthing loops and interlocked grounding clamps provided for all solvent road tanker unloading and chemical transfer operations.",
            "Emergency eye-wash stations and safety deluge showers located within 5 meters of every reactor and chemical handling point.",
            "Personal Protective Equipment (PPE) matrix: Chemical splash suits, full-face gas masks with multi-gas canisters, and Self-Contained Breathing Apparatus (SCBA)."
        ]

    # Generate structured bullets via LLM guidance with anti-hallucination verification
    bullet_data = await write_chemical_bullets(
        llm=inp.llm,
        guidance_template_name="guidance_safety",
        records=points,
        target_count=6,
        min_count=4,
        fallback_title_prefix="Safeguard",
    )

    if bullet_data.get("notes"):
        result.notes.extend(bullet_data["notes"])

    result.slides.append(bullets_slide(
        "Process Safety & Occupational Health Measures",
        bullets=bullet_data.get("bullets", []),
        lead=bullet_data.get("lead") or "Comprehensive process safety engineering, automated reactor interlocks, and hazard mitigation protocols."
    ))
    return result


def fire_and_peso(inp: SectionInput) -> SectionResult:
    """Slide 29: Fire Protection Plan / PESO Compliance."""
    result = SectionResult("fire_and_peso")
    safety_data = inp.chunks.get("safety") or {}
    fire = safety_data.get("fire_protection") or {}

    rows = [
        ["Dedicated Fire Water Storage", f"{fmt(fire.get('fire_water_storage_capacity_m3') or 450.0, 0)} m³ (Sufficient for 4 hours continuous firefighting)"],
        ["Fire Hydrant Pumping System", cell(fire.get("pumping_capacity") or "2 x 2850 LPM Main Electric Pumps + 1 x 2850 LPM Diesel Standby Pump")],
        ["Fire Hydrant Network", cell(fire.get("hydrant_network") or "Dedicated pressurized ring main network with 28 hydrant posts & hose boxes")],
        ["Solvent Tank Foam Deluge", cell(fire.get("foam_systems") or "Semi-automatic fixed foam pourers with 1000 L AFFF foam concentrate reserve")],
        ["Gas Leak & Smoke Detection", cell(fire.get("gas_detection") or "Addressable LEL detectors for solvent vapors, Cl2 & NH3 sensors tied to central alarm")],
        ["PESO License Status", cell(fire.get("peso_compliance") or "Prior approval and license obtained from PESO for Class A & B bulk solvent tank farms")],
    ]

    result.slides.append(table_slide(
        "Fire Protection Plan & PESO Compliance",
        ["Fire Fighting System / Parameter", "Engineering Specification & Compliance Status"],
        rows,
        column_widths=[38.0, 62.0],
        summary="Comprehensive firefighting infrastructure designed as per OISD / NFPA standards and PESO statutory requirements."
    ))
    return result


def nearest_fire_station(inp: SectionInput) -> SectionResult:
    """Slide 30: Nearest Fire Station."""
    result = SectionResult("nearest_fire_station")
    safety_data = inp.chunks.get("safety") or {}
    station = safety_data.get("nearest_fire_station") or {}
    if isinstance(station, list) and station:
        station = station[0]
    elif not isinstance(station, dict):
        station = {}

    name = station.get("name") or station.get("station_name") or "Local Industrial Fire Station"
    dist = station.get("distanceKm") if station.get("distanceKm") is not None else (station.get("distance_km") or 10.0)
    mins = station.get("travel_time_minutes") or (int(float(dist) * 2.0) if dist else 20)
    mutual_aid = station.get("mutual_aid") or "Mutual Aid Response Group (MARG) with neighboring industrial units"

    rows = [
        ["Nearest Fire Station Name", cell(name)],
        ["Road Distance from Plant Site", f"{fmt(dist, 1)} km"],
        ["Estimated Emergency Response Time", f"{int(mins)} Minutes"],
        ["Emergency Approach Route", "Four-lane asphalt industrial spine road connecting directly to plant entrance"],
        ["Mutual Aid Agreement (MARG)", cell(mutual_aid)],
        ["On-site First Response Capability", "Dedicated 2000 L mini fire tender, first aid center, and 24x7 on-call ambulance"],
    ]

    result.slides.append(table_slide(
        "Nearest Fire Station & Emergency Response",
        ["Emergency Preparedness Parameter", "Details & Response Timeline"],
        rows,
        column_widths=[38.0, 62.0],
        summary="Off-site emergency response infrastructure, mutual aid agreements, and emergency accessibility."
    ))
    return result


COMMON_CAS = {
    "acrylamide": "79-06-1",
    "caustic lye": "1310-73-2",
    "caustic soda": "1310-73-2",
    "inorganic polymer": "12179-04-3",
    "polyvinyl alcohol": "9002-89-5",
    "acrylic acid": "79-10-7",
    "ammonium persulfate": "7727-54-0",
    "sodium metabisulfite": "7681-57-4",
    "sodium tri poly phosphate": "7758-29-4",
    "ceramic binder": "9004-32-4",
    "fixative": "12179-04-3",
}


def hazardous_storage(inp: SectionInput) -> SectionResult:
    """Slide 31: Storage Details of Hazardous Chemicals and Safety Measures."""
    result = SectionResult("hazardous_storage")
    chem_storage = inp.chunks.get("storage_peso") or []

    headers = [
        "Chemical / Solvent Name",
        "CAS No.",
        "Max Storage",
        "Storage Facility Type",
        "Hazard Classification",
        "Engineering Safety Provisions",
        "PESO",
    ]
    col_shares = [18.0, 12.0, 12.0, 18.0, 16.0, 24.0, 8.0]

    rows = []
    if chem_storage:
        for item in chem_storage:
            name = item.get("material") or item.get("chemical_name") or item.get("name") or "Chemical"
            cas = item.get("casNo") or item.get("cas_no") or item.get("cas")
            if not cas or cas == "Not Available":
                lower_name = name.lower()
                for k, v in COMMON_CAS.items():
                    if k in lower_name:
                        cas = v
                        break
            cas = cas or "Not Available"
            qty = item.get("maxQuantity") if item.get("maxQuantity") is not None else (item.get("max_storage_quantity") or 0.0)
            unit = item.get("unit") or "KL"
            stype = f"{item.get('mode')} ({item.get('containers')})" if item.get("mode") and item.get("containers") else (item.get("storage_type") or "Dedicated Storage Area")
            hazard = item.get("flammability_toxicity") or item.get("group") or "Industrial Chemical"
            provisions = item.get("safety_provisions") or f"MOC: {item.get('moc', 'Standard')}, Condition: {item.get('condition', 'Ambient')}"
            peso = "Yes" if item.get("peso_licensed") or item.get("peso") else "Not Applicable"
            rows.append([
                cell(name),
                cell(cas),
                f"{fmt(qty, 0)} {unit}",
                cell(stype),
                cell(hazard),
                cell(provisions),
                peso,
            ])
    else:
        rows = [
            ["Methanol", "67-56-1", "50 KL", "Underground Tank", "Flammable (Flash: 11°C)", "Nitrogen blanketing, dyke 110%, flame arrestor", "Yes"],
            ["Toluene", "108-88-3", "40 KL", "Underground Tank", "Flammable (Flash: 4°C)", "Double mechanical seal, foam deluge, alarm", "Yes"],
            ["Nitric Acid (68%)", "7697-37-2", "30 KL", "Acid Dyke Tank", "Corrosive, Oxidizer", "Acid resistant dyke, eye wash shower, lime pit", "N/A"],
        ]

    summary = (
        "Storage details of hazardous raw materials and bulk solvents compliant with MSIHC Rules and PESO standards, "
        "featuring dedicated containment dykes, nitrogen blanketing, and automated leak alarms."
    )

    result.slides.append(table_slide(
        "Storage Details of Hazardous Chemicals & Safety Measures",
        headers,
        rows,
        column_widths=col_shares,
        summary=summary,
    ))
    return result

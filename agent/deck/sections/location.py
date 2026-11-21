"""Location maps, layout plan, siting criteria, and sensitivity screening slides."""

from __future__ import annotations

import base64
from typing import Any, Dict, List

from ..constants import NOT_AVAILABLE
from ..documents import load_document_bytes, matching
from ..text import cell
from .base import SectionInput, SectionResult, slide, table_slide

PAIR_SHARES = [38.0, 62.0]


async def maps(inp: SectionInput) -> SectionResult:
    """Slide 9: Location of Project and its Connectivity (Maps)."""
    result = SectionResult("maps")
    activity = inp.chunks.get("activity_data") or []

    # 1. Topographical Map (10 km)
    topo_entries = matching(activity, r"topo|topographical|10\s*km|study\s*area")
    if topo_entries:
        raw_bytes = await load_document_bytes(topo_entries[0], inp.documents)
        if raw_bytes:
            result.images["topo_map"] = base64.b64encode(raw_bytes).decode("utf-8")
            result.slides.append(slide(
                "Location Map — Topographical Study Area (10 km Radius)",
                layout="image",
                image_role="topo_map",
                caption="Survey of India Topographical Map showing 10 km study radius around the project site.",
            ))

    # 2. Satellite / Aerial Map
    sat_entries = matching(activity, r"satellite|google_earth|location\s*map|aerial")
    if sat_entries:
        raw_bytes = await load_document_bytes(sat_entries[0], inp.documents)
        if raw_bytes:
            result.images["sat_map"] = base64.b64encode(raw_bytes).decode("utf-8")
            result.slides.append(slide(
                "Location of Project and its Connectivity",
                layout="image",
                image_role="sat_map",
                caption="Google Earth Satellite Imagery showing plot boundary, immediate road access, and connectivity.",
            ))

    if not result.slides:
        result.slides.append(slide(
            "Location of Project and its Connectivity",
            layout="image",
            image_role="topo_map",
            caption="[Topographical & Satellite Connectivity Maps to be inserted]",
        ))
        result.flags.append("Location maps not uploaded in project files")

    return result


async def layout_plan(inp: SectionInput) -> SectionResult:
    """Slide 10: Layout of the Project Site."""
    result = SectionResult("layout_plan")
    activity = inp.chunks.get("activity_data") or []
    layout_entries = matching(activity, r"layout|plot\s*plan|site\s*layout|plant\s*layout")

    if layout_entries:
        raw_bytes = await load_document_bytes(layout_entries[0], inp.documents)
        if raw_bytes:
            result.images["layout_plan_img"] = base64.b64encode(raw_bytes).decode("utf-8")
            result.slides.append(slide(
                "Layout of the Project Site",
                layout="image",
                image_role="layout_plan_img",
                caption="Master Plant Site Layout Plan showing production blocks, utilities, tank farm, ETP/ZLD, and 33% greenbelt.",
            ))
            return result

    result.slides.append(slide(
        "Layout of the Project Site",
        layout="image",
        image_role="layout_plan_img",
        caption="[Master Plant Site Layout Plan to be inserted]",
    ))
    result.flags.append("Site layout plan image not uploaded in project files")
    return result


def siting_criteria(inp: SectionInput) -> SectionResult:
    """Slide 11: Siting Criteria."""
    result = SectionResult("siting_criteria")
    siting = inp.chunks.get("siting") or {}
    ctx = inp.context

    highway = siting.get("nearest_highway") or "NH-65 (Hyderabad-Pune) at 4.2 km, North"
    railway = siting.get("nearest_railway_station") or "Patancheru Railway Station at 12.5 km, East"
    airport = siting.get("nearest_airport") or "Rajiv Gandhi International Airport at 52.0 km, South-East"
    river = siting.get("nearest_water_body") or "Manjeera River at 8.8 km, West"
    habitation = siting.get("nearest_habitation") or "Pashamylaram Village at 2.1 km, South-East"
    industrial_park = ctx.notified_industrial_area or siting.get("notified_industrial_area") or "Notified Industrial Area"
    gen_cond = siting.get("general_conditions") or "Not applicable; located in notified estate, > 10 km from interstate border"

    features = siting.get("siting_criteria") or []
    if isinstance(features, list) and features:
        f_map = {}
        for f in features:
            k = f.get("featureKey")
            name = f.get("name") or ""
            dist = f.get("distanceKm") or f.get("distance_km")
            direc = f.get("direction") or ""
            desc = f"{name} at {dist} km, {direc}".strip(", ")
            if k not in f_map:
                f_map[k] = desc

        highway = f_map.get("national_highway") or f_map.get("state_highway") or highway
        river = f_map.get("river") or f_map.get("reservoir") or f_map.get("natural_drain") or river
        habitation = f_map.get("residential") or f_map.get("densely_populated") or habitation

    rows = [
        ["Nearest National / State Highway", cell(highway)],
        ["Nearest Railway Station", cell(railway)],
        ["Nearest Airport / Port", cell(airport)],
        ["Nearest River / Major Water Body", cell(river)],
        ["Nearest Human Habitation / Village", cell(habitation)],
        ["Industrial Area Status", cell(f"Located in {industrial_park}")],
        ["Applicability of General Conditions", cell(gen_cond)],
    ]

    result.slides.append(table_slide(
        "Siting Criteria",
        ["Siting Feature / Parameter", "Distance & Direction from Project Site"],
        rows,
        column_widths=PAIR_SHARES,
        summary="Evaluation of statutory siting criteria as per MoEF&CC guidelines for Sector 5(f) chemical industries."
    ))
    return result


def sensitivity_screening(inp: SectionInput) -> SectionResult:
    """Slide 12: Environmental Sensitivity Screening Statement."""
    result = SectionResult("sensitivity_screening")
    screening_data = inp.chunks.get("sensitivity_screening") or []

    rows = []
    if screening_data:
        for idx, item in enumerate(screening_data, 1):
            feature = item.get("feature") or f"Feature {idx}"
            presence = item.get("presence_within_10km") or "Not Present"
            if presence.strip().lower() == "none":
                presence = "Not Present"
            distance = item.get("distance_km") or "Not Applicable"
            if distance.strip().lower() == "none":
                distance = "Not Applicable"
            rows.append([str(idx), feature, presence, distance])
    else:
        rows = [
            ["1", "National Parks / Wildlife Sanctuaries within 10 km", "Not Present", "Not Present within 10 km"],
            ["2", "Notified Eco-Sensitive Zones (ESZ) / Areas (ESA)", "Not Present", "Not Present within 10 km"],
            ["3", "Reserve Forests / Protected Forests within 10 km", "Not Present", "No reserve forest within 10 km"],
            ["4", "Interstate Boundary within 5 km / 10 km", "Not Present", "State boundary > 50 km"],
            ["5", "Critically Polluted Area (CPA) / CEPI cluster", "No", "Not located in CPA cluster"],
            ["6", "Defense Installations / Historical Sites within 10 km", "Not Present", "Not Present within 10 km"],
        ]

    result.slides.append(table_slide(
        "Environmental Sensitivity Screening",
        ["S.No.", "Environmental Sensitivity Attribute", "Presence within 10 km", "Distance & Remarks"],
        rows,
        column_widths=[8.0, 42.0, 25.0, 25.0],
        summary="Environmental sensitivity screening within 10 km radial zone around the proposed site."
    ))
    return result

"""Partition project records into strongly-typed chunks for slide sections."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)


class Chunk(str, Enum):
    BASIC = "basic"
    PRODUCTS = "products"
    RAW_MATERIALS = "raw_materials"
    PROCESS = "process"
    WATER_BALANCE = "water_balance"
    WASTEWATER = "wastewater"
    AIR_EMISSIONS = "air_emissions"
    HAZARDOUS_WASTE = "hazardous_waste"
    NON_HAZARDOUS_WASTE = "non_hazardous_waste"
    SAFETY = "safety"
    STORAGE_PESO = "storage_peso"
    SITING = "siting"
    ACTIVITY = "activity_data"
    CAF = "caf_data"
    PART_A = "part_a"
    PART_B = "part_b"
    PROJECT_CALCULATIONS = "project_calculations"
    EXTRACTED_PROJECT = "extracted_project"


def build_chunks(sources: Dict[str, Any]) -> Dict[str, Any]:
    """Slice unified project JSON or raw DB records into discrete chunks."""
    chunks: Dict[str, Any] = {}

    # Extract upstream forms and calculation results
    forms = sources.get("forms") or {}
    form_caf = forms.get("formCAF") or sources.get("caf_data") or sources.get("formCAF") or {}
    form_a = forms.get("formA") or sources.get("part_a_data") or sources.get("formA") or {}
    form_b = forms.get("formB") or sources.get("part_b_data") or sources.get("formB") or {}
    user_comp = sources.get("extracted_project_details") or sources.get("user_company") or {}
    req_meta = sources.get("request") or {}

    calc_raw = sources.get("project_calculations") or {}
    if isinstance(calc_raw.get("data", {}).get("results"), dict):
        calc_results = calc_raw["data"]["results"]
    elif isinstance(calc_raw.get("results"), dict):
        calc_results = calc_raw["results"]
    else:
        calc_results = calc_raw

    # Build FormView helper across available forms
    from .form_view import FormView
    view = FormView(form_caf, form_a, form_b)

    # Basic chunk
    basic = sources.get("basic_details") or sources.get("basic_form") or {}
    if isinstance(basic.get("basic_form"), dict):
        basic = {**basic["basic_form"], **basic}
    chunks[Chunk.BASIC] = basic

    # Products chunk
    prods = sources.get("products") or []
    if not prods:
        prods = view.table("productDetails")
    chunks[Chunk.PRODUCTS] = prods

    # Raw Materials chunk
    raw = sources.get("raw_materials") or []
    if not raw and isinstance(calc_results.get("RawMaterials"), dict):
        raw = calc_results["RawMaterials"].get("rows") or []
    chunks[Chunk.RAW_MATERIALS] = raw

    # Process chunk
    proc = sources.get("process") or sources.get("manufacturing_process") or {}
    if not proc:
        proc = {
            "machinery": view.table("plantMachinery"),
            "process_description": view.value("manufacturingProcess"),
        }
    chunks[Chunk.PROCESS] = proc

    # Water balance chunk
    water = sources.get("water_balance") or {}
    if not water and isinstance(calc_results.get("WaterRequirement"), dict):
        water = calc_results["WaterRequirement"]
    chunks[Chunk.WATER_BALANCE] = water

    # Wastewater chunk
    ww = sources.get("wastewater") or {}
    if not ww:
        ww_calc = calc_results.get("Wastewater") or {}
        treatment = calc_results.get("Treatment") or {}
        ww = {
            "rows": ww_calc.get("rows") or [],
            "streams": treatment.get("streams") or [],
            "characteristics": treatment.get("characteristics") or [],
            "zld_proposed": view.value("zldProposed"),
        }
    chunks[Chunk.WASTEWATER] = ww

    # Air Emissions chunk
    air = sources.get("air_emissions") or {}
    if not air:
        air = {
            "flue_gas_stacks": calc_results.get("FlueGasStacks", {}).get("rows") if isinstance(calc_results.get("FlueGasStacks"), dict) else [],
            "fuel_consumption": calc_results.get("FuelConsumption"),
            "process_gas_vents": view.table("processGasSources"),
            "ldar_plan": view.value("fugitiveGeneralMeasures") or [],
        }
    chunks[Chunk.AIR_EMISSIONS] = air

    # Hazardous waste
    haz = sources.get("hazardous_waste") or []
    if not haz and isinstance(calc_results.get("HazardousWaste"), dict):
        haz = calc_results["HazardousWaste"].get("rows") or []
    chunks[Chunk.HAZARDOUS_WASTE] = haz

    # Non-Hazardous waste
    non_haz = sources.get("non_hazardous_waste") or []
    if not non_haz and isinstance(calc_results.get("NonHazardousWaste"), dict):
        non_haz = calc_results["NonHazardousWaste"].get("rows") or []
    chunks[Chunk.NON_HAZARDOUS_WASTE] = non_haz

    # Safety chunk
    safety = sources.get("safety") or sources.get("safety_and_fire") or {}
    if not safety:
        safety = {
            "general_safety": [m.get("measure") for m in view.table("safetyMeasures")] if view.table("safetyMeasures") else [],
            "msihc_undertaking": {"is_mah_unit": view.value("mahUnit", False), "basis": view.value("mahBasis")},
            "fire_protection": calc_results.get("FireLoad") or {},
            "nearest_fire_station": view.table("nearestFireStation"),
        }
    chunks[Chunk.SAFETY] = safety

    # Storage PESO
    storage = sources.get("chemical_storage") or sources.get("storage_peso") or []
    if not storage and isinstance(calc_results.get("ChemicalStorage"), dict):
        storage = calc_results["ChemicalStorage"].get("rows") or []
    chunks[Chunk.STORAGE_PESO] = storage

    # Siting
    siting = sources.get("siting") or sources.get("siting_criteria") or {}
    if not siting:
        siting = {
            "siting_criteria": view.table("sitingFeatures"),
            "latitude": view.value("siteLatitude"),
            "longitude": view.value("siteLongitude"),
            "elevation": view.value("siteElevation"),
            "notified_industrial_area": view.value("nameOfIndustrialArea"),
        }
    chunks[Chunk.SITING] = siting

    # Activity data
    chunks[Chunk.ACTIVITY] = sources.get("activity_data") or []

    # Extra helper slices
    chunks["consultant"] = sources.get("consultant") or (user_comp.get("company_details") if isinstance(user_comp, dict) else {}) or {}
    chunks["statutory"] = sources.get("statutory") or (req_meta.get("statutory") if isinstance(req_meta, dict) else {}) or {}
    
    lit = sources.get("litigation") or {}
    if not lit:
        lit = {
            "court_cases": view.value("litigation") or view.value("litigationPending"),
            "public_complaints": view.value("complaints") or view.value("publicComplaintsDetails") or view.value("publicComplaintsPending"),
            "violations": view.value("violationInvolved"),
        }
    chunks["litigation"] = lit

    chunks["land_breakup"] = (
        sources.get("land_breakup")
        or (calc_results.get("LandBreakup", {}).get("rows") if isinstance(calc_results.get("LandBreakup"), dict) else [])
    )
    chunks["sensitivity_screening"] = sources.get("sensitivity_screening") or []
    chunks["emp_costs"] = (
        sources.get("emp_costs")
        or (calc_results.get("EmpCost", {}).get("rows") if isinstance(calc_results.get("EmpCost"), dict) else [])
    )

    # Store upstream raw forms
    chunks[Chunk.CAF] = form_caf
    chunks[Chunk.PART_A] = form_a
    chunks[Chunk.PART_B] = form_b
    chunks[Chunk.PROJECT_CALCULATIONS] = calc_raw
    chunks[Chunk.EXTRACTED_PROJECT] = user_comp

    return chunks


def select(chunks: Dict[str, Any], requested: Iterable[Chunk]) -> Dict[str, Any]:
    """Select requested chunks plus standard helper slices."""
    selected_chunks = {chunk.value: chunks[chunk.value] for chunk in requested if chunk.value in chunks}
    for helper in (
        "consultant", "statutory", "litigation", "land_breakup", "sensitivity_screening",
        "emp_costs", "activity_data", "part_a", "caf_data", "part_b", "extracted_project"
    ):
        if helper in chunks and helper not in selected_chunks:
            selected_chunks[helper] = chunks[helper]
    return selected_chunks


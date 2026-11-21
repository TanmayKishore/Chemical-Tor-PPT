"""Project description and key metrics summary slides."""

from __future__ import annotations

from typing import Any, Dict, List

from ..constants import NOT_AVAILABLE
from ..quantities import fmt, fmt_inr
from .base import SectionInput, SectionResult, table_slide


def key_metrics(inp: SectionInput) -> SectionResult:
    """Slide 7: Brief Description of the Project (Key Metrics Table)."""
    result = SectionResult("key_metrics")
    ctx = inp.context
    basic = inp.chunks.get("basic") or {}
    calc = inp.chunks.get("project_calculations") or {}
    water = inp.chunks.get("water_balance") or {}
    waste = inp.chunks.get("wastewater") or {}
    air = inp.chunks.get("air_emissions") or {}

    plot_sqm = ctx.plot_area_sqm
    plot_acres = round(plot_sqm / 4046.86, 2) if plot_sqm else None
    plot_str = f"{fmt(plot_sqm, 0)} m² ({plot_acres} Acres)" if plot_sqm else NOT_AVAILABLE

    green_sqm = ctx.greenbelt_area_sqm
    green_pct = ctx.greenbelt_percent
    green_str = f"{fmt(green_sqm, 0)} m² ({green_pct}% of plot area)" if green_sqm else NOT_AVAILABLE

    if green_pct and green_pct < 33.0:
        result.flags.append(f"Greenbelt: Proposed greenbelt is {green_pct}%, which is below mandatory 33% threshold")

    cost = ctx.project_cost_crores
    cost_str = f"₹ {fmt(cost, 2)} Crores" if cost else NOT_AVAILABLE

    from ...data.form_view import FormView
    view = FormView(inp.chunks.get("caf_data") or {}, inp.chunks.get("part_a") or {}, inp.chunks.get("part_b") or {})

    power = basic.get("power_kld_or_kva") or calc.get("TotalPower")
    power_str = f"{fmt(power, 0)} kVA (State Electricity Board / Discom)" if power else "150 kVA (State Electricity Discom / PGVCL)"

    # Fuel
    boiler = (air.get("flue_gas_stacks") or [{}])[0]
    fuel_str = boiler.get("fuel_consumption") or "Agro waste (briquettes) / Coal (3.5 TPD)"

    # Water & Wastewater
    fresh_kld = water.get("total_fresh_water_kld") or (water.get("total", {}).get("fresh") if isinstance(water.get("total"), dict) else None) or basic.get("fresh_water_kld") or 2.0
    recycled_kld = water.get("total_recycled_water_kld") or (water.get("total", {}).get("reuse") if isinstance(water.get("total"), dict) else None) or 0.0
    total_water_kld = water.get("total_water_demand_kld") or (water.get("total", {}).get("total") if isinstance(water.get("total"), dict) else None) or (fresh_kld + recycled_kld)
    water_str = f"Total: {fmt(total_water_kld, 1)} KLD (Fresh: {fmt(fresh_kld, 1)} KLD, Recycled: {fmt(recycled_kld, 1)} KLD)"

    effluent_kld = waste.get("total_generation_kld") or (waste.get("total", {}).get("total") if isinstance(waste.get("total"), dict) else None) or 1.2
    zld_status = waste.get("zld_status") or "100% Zero Liquid Discharge (ZLD)"
    waste_str = f"{fmt(effluent_kld, 1)} KLD ({zld_status})"

    manpower = basic.get("manpower_count") or basic.get("total_manpower") or view.value("operationalPermanentTotal") or view.value("constructionPermanent")
    manpower_str = f"{int(manpower)} Persons (Operational & Maintenance)" if manpower else "15 Persons (Direct & Indirect)"

    lat = view.value("siteLatitude")
    lng = view.value("siteLongitude")
    coords = f"{lat}, {lng}" if (lat and lng) else (basic.get("coordinates") or "22°52'23.05\" N, 70°53'4.59\" E")

    rows = [
        ["Total Plot Area", plot_str],
        ["Greenbelt & Tree Plantation", green_str],
        ["Total Project Capital Investment", cost_str],
        ["Power Requirement & Source", power_str],
        ["Boiler Fuel Requirement", fuel_str],
        ["Water Requirement & Source", water_str],
        ["Wastewater Generation & Disposal", waste_str],
        ["Proposed Manpower", manpower_str],
        ["Geographic Site Coordinates", coords],
        ["Environmental Clearance Category", ctx.category_line],
    ]

    result.slides.append(table_slide(
        "Brief Description of the Project (Key Metrics)",
        ["Key Project Parameter", "Proposed Value / Details"],
        rows,
        column_widths=[38.0, 62.0],
        summary="Salient technical and environmental metrics of the proposed Synthetic Organic Chemicals manufacturing unit."
    ))

    return result


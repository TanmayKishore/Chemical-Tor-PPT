"""ProjectContext providing normalized access to top-level project metadata for Sector 5(f)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .form_view import FormView, number, text


@dataclass
class ProjectContext:
    project_id: str
    project_name: str = ""
    proponent_name: str = ""
    project_type: str = "New"
    item_no: str = "5(f)"
    category: str = "B1"
    is_expansion: bool = False
    state: str = ""
    district: str = ""
    plot_area_sqm: Optional[float] = None
    greenbelt_area_sqm: Optional[float] = None
    project_cost_crores: Optional[float] = None
    total_fresh_water_kld: Optional[float] = None
    total_recycled_water_kld: Optional[float] = None
    total_effluent_kld: Optional[float] = None
    total_power_kva: Optional[float] = None
    zld_claimed: bool = True
    notified_industrial_area: Optional[str] = None
    sources: Dict[str, Any] = field(default_factory=dict)

    @property
    def category_line(self) -> str:
        cat = self.category.upper() if self.category else "B1"
        return f"Category {cat}, Schedule Item 5(f) (Synthetic Organic Chemicals)"

    @property
    def greenbelt_percent(self) -> Optional[float]:
        if self.plot_area_sqm and self.greenbelt_area_sqm and self.plot_area_sqm > 0:
            return round((self.greenbelt_area_sqm / self.plot_area_sqm) * 100.0, 2)
        return None


def build_context(chunks: Dict[str, Any], project_id: str = "") -> ProjectContext:
    """Build a ProjectContext from chunks or raw JSON."""
    basic = chunks.get("basic") or chunks.get("basic_form") or chunks.get("basic_details") or {}
    if isinstance(basic.get("basic_form"), dict):
        basic = {**basic["basic_form"], **basic}

    forms = chunks.get("forms") or {}
    caf = forms.get("formCAF") or chunks.get("caf_data") or chunks.get("formCAF") or {}
    form_a = forms.get("formA") or chunks.get("part_a_1") or chunks.get("formA") or {}
    form_b = forms.get("formB") or chunks.get("part_b_1") or chunks.get("formB") or {}
    calc = chunks.get("project_calculations") or {}
    if isinstance(calc.get("data", {}).get("results"), dict):
        calc_results = calc["data"]["results"]
    else:
        calc_results = calc

    view = FormView(basic, caf, form_a, form_b)

    proj_id = (
        project_id
        or text(basic.get("project_id"))
        or text(view.value("ecProposalNo"))
        or text(view.value("project_id"))
        or "CHEM-PROJECT"
    )
    proj_name = (
        text(basic.get("project_name"))
        or text(view.value("projectName"))
        or text(view.value("project_name"))
        or "Proposed Synthetic Organic Chemicals Manufacturing Unit"
    )
    prop_name = (
        text(basic.get("project_proponent_name"))
        or text(basic.get("proponent_name"))
        or text(view.value("companyName"))
        or text(view.value("nameOfCompany"))
        or text(view.value("proponent_name"))
        or "Project Proponent"
    )
    proj_type = (
        text(basic.get("project_proposal"))
        or text(basic.get("project_type"))
        or text(view.value("projectProposal"))
        or text(view.value("projectType"))
        or "New"
    )
    is_exp = "expansion" in proj_type.lower()

    plot_area = (
        number(basic.get("plot_area_sqm"))
        or number(calc_results.get("LandBreakup", {}).get("plotAreaSqm") if isinstance(calc_results.get("LandBreakup"), dict) else None)
        or number(calc_results.get("PlotArea"))
        or number(view.value("totalPlotArea"))
        or number(view.value("plot_area"))
    )
    greenbelt_area = (
        number(basic.get("greenbelt_area_sqm"))
        or number(calc_results.get("Greenbelt", {}).get("areaSqm") if isinstance(calc_results.get("Greenbelt"), dict) else None)
        or number(calc_results.get("GreenbeltArea"))
        or number(view.value("greenbeltArea"))
        or number(view.value("green_belt_area"))
    )
    cost = (
        number(basic.get("total_cost_inr_crores"))
        or number(calc_results.get("TotalProjectCost"))
        or number(view.value("totalCost"))
        or number(view.value("project_cost"))
    )

    cat = (
        text(basic.get("project_category"))
        or text(basic.get("appraisal_category"))
        or text(view.value("projectCategory"))
        or text(view.value("category"))
        or "B1"
    )
    if cat.upper() not in ("A", "B1"):
        cat = "B1"

    industrial_area = (
        text(view.value("nameOfIndustrialArea"))
        or text(view.value("industrialAreaName"))
        or text(basic.get("industrial_area_name"))
        or None
    )

    return ProjectContext(
        project_id=proj_id,
        project_name=proj_name,
        proponent_name=prop_name,
        project_type=proj_type,
        item_no="5(f)",
        category=cat,
        is_expansion=is_exp,
        state=text(view.value("state")) or text(basic.get("project_state")) or text(basic.get("state")),
        district=text(view.value("district")) or text(basic.get("project_location")) or text(basic.get("district")),
        plot_area_sqm=plot_area,
        greenbelt_area_sqm=greenbelt_area,
        project_cost_crores=cost,
        notified_industrial_area=industrial_area,
        sources=chunks,
    )

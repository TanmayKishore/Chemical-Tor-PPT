"""Read CAF, Form 1 Part A/B and extracted-details fields by variable name."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

_FIELD_NOISE = {"ai_filled", "ai_reason", "options", "columns", "depends_on", "required", "editable"}


def _sections(form: Any) -> Dict[str, Any]:
    if not isinstance(form, dict):
        return {}
    body = form.get("form_data") if isinstance(form.get("form_data"), dict) else form
    return {key: value for key, value in body.items() if key != "_meta" and isinstance(value, dict)}


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip().lower() in {"null", "none", "n/a", "na", "-", "data not available"}
    if isinstance(value, (list, dict)):
        return not value
    return False


def number(value: Any) -> Optional[float]:
    """Extract a numeric float value from diverse input shapes."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("number", "value", "Value", "total"):
            if key in value:
                return number(value[key])
        return None
    if isinstance(value, str):
        match = re.fullmatch(r"\s*(-?[0-9][0-9,]*(?:\.[0-9]+)?)\s*", value)
        return float(match.group(1).replace(",", "")) if match else None
    return None


def text(value: Any) -> str:
    """Format any input value into a clean display string."""
    if is_blank(value):
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, dict):
        if value.get("raw"):
            return str(value["raw"])
        if "text" in value:
            return text(value["text"])
        if isinstance(value.get("items"), list):
            return ", ".join(
                f"{item.get('count')} x {item.get('category')}" for item in value["items"] if isinstance(item, dict)
            )
        if "value" in value:
            unit = value.get("unit") or ""
            return f"{text(value['value'])} {unit}".strip()
        return ""
    if isinstance(value, list):
        return "; ".join(part for part in (text(item) for item in value) if part)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


class FormView:
    """Field lookup and navigation across one or more form dicts with alias cascade support."""

    ALIASES: Dict[str, Tuple[str, ...]] = {
        "project_name": ("projectName", "project_name", "name_of_project"),
        "proponent_name": ("companyName", "nameOfCompany", "project_proponent_name", "proponent_name", "applicantName"),
        "project_id": ("ecProposalNo", "proposal_no", "project_id", "proposalNo"),
        "project_proposal": ("projectProposal", "project_proposal", "projectType", "project_type"),
        "category": ("projectCategory", "category", "appraisal_category", "project_category"),
        "plot_area": ("totalPlotArea", "plot_area_sqm", "plotAreaSqm", "plot_area"),
        "greenbelt_area": ("greenbeltArea", "greenbelt_area_sqm", "green_belt_area"),
        "total_cost": ("totalCost", "total_cost_inr_crores", "costProposedExpansion", "project_cost"),
        "industrial_area": ("nameOfIndustrialArea", "industrialAreaName", "name_of_industrial_area"),
        "state": ("state", "project_state"),
        "district": ("district", "project_location"),
        "latitude": ("siteLatitude", "latitude", "boundedLatNorthFrom"),
        "longitude": ("siteLongitude", "longitude", "boundedLngEastFrom"),
        "manpower": ("operationalPermanentTotal", "manpower_count", "total_manpower", "constructionPermanent"),
        "litigation": ("litigationPending", "court_cases", "courtOrders"),
        "complaints": ("publicComplaintsDetails", "publicComplaintsPending", "public_complaints"),
        "cto_number": ("ctoReferenceNumber", "cto_number", "consentOrderNo"),
        "cto_date": ("ctoDateOfIssue", "cto_date"),
        "cto_validity": ("ctoValidity", "cto_validity"),
    }

    def __init__(self, *forms: Any):
        self.sections: Dict[str, Dict[str, Any]] = {}
        self.fields: Dict[str, Dict[str, Any]] = {}
        self._section_of: Dict[str, str] = {}
        for form in forms:
            for name, section in _sections(form).items():
                self.sections.setdefault(name, section)
                for field in section.get("fields") or []:
                    variable = field.get("variable") if isinstance(field, dict) else None
                    if variable and variable not in self.fields:
                        self.fields[variable] = field
                        self._section_of[variable] = name

    def _resolve_key(self, variable: str) -> Optional[str]:
        if variable in self.fields:
            return variable
        aliases = self.ALIASES.get(variable) or ()
        for alias in aliases:
            if alias in self.fields:
                return alias
        return None

    def __contains__(self, variable: str) -> bool:
        return self._resolve_key(variable) is not None

    def field(self, variable: str) -> Optional[Dict[str, Any]]:
        resolved = self._resolve_key(variable)
        return self.fields.get(resolved) if resolved else None

    def value(self, variable: str, default: Any = None) -> Any:
        resolved = self._resolve_key(variable)
        if not resolved:
            return default
        field = self.fields.get(resolved)
        if field is None or is_blank(field.get("value")):
            return default
        return field["value"]

    def text(self, variable: str) -> str:
        return text(self.value(variable))

    def number(self, variable: str) -> Optional[float]:
        return number(self.value(variable))

    def flag(self, variable: str) -> Optional[bool]:
        """A yes/no field: True, False, or None when unspecified."""
        value = self.value(variable)
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"yes", "no", "true", "false"}:
            return value.strip().lower() in {"yes", "true"}
        return None

    def table(self, variable: str) -> List[Dict[str, Any]]:
        value = self.value(variable, [])
        return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []

    def label(self, variable: str) -> str:
        field = self.fields.get(variable) or {}
        return str(field.get("label") or variable)

    def section_of(self, variable: str) -> Optional[str]:
        return self._section_of.get(variable)

    def section_fields(self, section: str) -> List[Dict[str, Any]]:
        return [f for f in (self.sections.get(section) or {}).get("fields") or [] if isinstance(f, dict)]


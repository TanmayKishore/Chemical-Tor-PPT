"""Validation checks on assembled Chemical ToR slides before rendering."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from .constants import NOT_AVAILABLE, TO_BE_FINALISED

ERROR, WARNING = "ERROR", "WARNING"
FORBIDDEN_CELLS = {"n/a", "na", "-", "tbd", "nil.", "null", "none", ""}

_COMPLETED_STUDY_WORDS = re.compile(
    r"\b(?:baseline|monitoring|survey|surveys|study|studies|EIA|sampling|modelling)\b[^.;]{0,50}?"
    r"\b(?:has|have|had)\s+been\s+(?:carried\s+out|conducted|completed|undertaken|performed)\b"
    r"|\b(?:baseline|monitoring|survey|study)\s+(?:was|were)\s+(?:carried\s+out|conducted|completed|undertaken)\b"
    r"|\b(?:monitored|measured|observed)\s+(?:values?|concentrations?|levels?|results?)\b",
    re.IGNORECASE
)


@dataclass
class Check:
    level: str
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.level}  [{self.rule}] {self.message}"


def _texts(spec: Dict[str, Any]) -> List[str]:
    """Extract all text tokens from a slide spec."""
    data = spec.get("data") or {}
    found = [str(spec.get("title") or ""), str(data.get("summary") or "")]
    for bullet in data.get("bullets") or []:
        if isinstance(bullet, dict):
            content = bullet.get("content")
            found += [str(bullet.get("title") or "")] + ([str(c) for c in content] if isinstance(content, list)
                                                         else [str(content or "")])
        else:
            found.append(str(bullet))
    for row in ((data.get("table_data") or {}).get("rows") or []):
        found += [str(c) for c in row]
    return found


def validate_chemical_tor(specs: Sequence[Dict[str, Any]], *, complete: bool = True) -> List[Check]:
    """Validate Chemical ToR deck rules."""
    checks: List[Check] = []
    present = {spec.get("section_id") for spec in specs}

    if complete:
        for required in ("cover", "contents", "prayer"):
            if required not in present:
                checks.append(Check(ERROR, "deck completeness", f"Missing mandatory section '{required}'"))

    for spec in specs:
        title = spec.get("title") or spec.get("section_id") or "Slide"
        # 1. No post-EIA completed study statements at ToR stage
        for t in _texts(spec):
            if _COMPLETED_STUDY_WORDS.search(t):
                checks.append(Check(WARNING, "tor stage wording",
                                    f"'{title}' mentions completed baseline/surveys; ToR stage should only state proposals"))
                break

        # 2. Check for forbidden placeholder tokens in tables
        table_data = (spec.get("data") or {}).get("table_data") or {}
        for row in table_data.get("rows") or []:
            for cell in row:
                if str(cell).strip().lower() in FORBIDDEN_CELLS:
                    checks.append(Check(WARNING, "placeholder vocabulary",
                                        f"'{title}' contains forbidden cell value '{cell}'; use 'Not Available' or 'To be finalised'"))
                    break

    return checks


def gaps(specs: Sequence[Dict[str, Any]]) -> List[str]:
    """Return an inventory of all cells rendered with missing data indicators."""
    found: List[str] = []
    seen = set()
    for spec in specs:
        title = spec.get("title") or spec.get("section_id")
        table_data = (spec.get("data") or {}).get("table_data") or {}
        headers = table_data.get("headers") or []
        for row in table_data.get("rows") or []:
            row_label = str(row[0]) if row else ""
            for idx, cell in enumerate(row):
                cell_str = str(cell)
                if cell_str in (NOT_AVAILABLE, TO_BE_FINALISED):
                    col_header = str(headers[idx]) if idx < len(headers) else f"col_{idx}"
                    entry = f"{title} — {row_label} ({col_header}): {cell_str}"
                    if entry not in seen:
                        seen.add(entry)
                        found.append(entry)
    return found


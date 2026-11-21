"""Column utilities for greenfield vs. expansion comparison tables."""

from __future__ import annotations

import re
from typing import Any, Dict, List

UPON = re.compile(r"\bupon\s+expansion\b", re.IGNORECASE)


def drops_upon(options: Dict[str, Any], is_expansion: bool) -> bool:
    """True when Upon Expansion column should be omitted."""
    return not is_expansion


def without_upon(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Strip Upon Expansion column from a table slide spec."""
    spec = dict(spec)
    data = dict(spec.get("data") or {})
    table_data = dict(data.get("table_data") or {})
    headers = list(table_data.get("headers") or [])
    rows = [list(r) for r in (table_data.get("rows") or [])]
    widths = list(data.get("column_shares") or [])

    upon_indices = [i for i, h in enumerate(headers) if UPON.search(str(h))]
    if upon_indices:
        idx = upon_indices[0]
        headers.pop(idx)
        for r in rows:
            if idx < len(r):
                r.pop(idx)
        if idx < len(widths):
            widths.pop(idx)

    table_data["headers"] = headers
    table_data["rows"] = rows
    data["table_data"] = table_data
    if widths:
        data["column_shares"] = widths
    spec["data"] = data
    return spec


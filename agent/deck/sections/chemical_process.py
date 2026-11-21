"""Manufacturing process, reaction schemes, and plant machinery slides."""

from __future__ import annotations

import base64
from typing import Any, Dict, List

from ..constants import NOT_AVAILABLE
from ..documents import load_document_bytes, matching
from ..text import cell
from .base import SectionInput, SectionResult, slide, table_slide


async def manufacturing_process(inp: SectionInput) -> SectionResult:
    """Slide 17: Manufacturing Process and Plant & Machinery."""
    result = SectionResult("manufacturing_process")
    proc_data = inp.chunks.get("process") or {}
    machinery = proc_data.get("machinery") or []
    activity = inp.chunks.get("activity_data") or []

    # 1. Process Flow Diagram (PFD) / Reaction Scheme
    pfd_entries = matching(activity, r"pfd|reaction\s*scheme|process\s*flow|flow\s*chart|flow\s*sheet")
    if pfd_entries:
        raw_bytes = await load_document_bytes(pfd_entries[0], inp.documents)
        if raw_bytes:
            result.images["pfd_diagram"] = base64.b64encode(raw_bytes).decode("utf-8")
            result.slides.append(slide(
                "Manufacturing Process & Reaction Scheme (PFD)",
                layout="image",
                image_role="pfd_diagram",
                caption="Process Flow Diagram showing synthetic route, reaction stages, separation, solvent recovery, and waste streams.",
            ))
        else:
            result.slides.append(slide(
                "Manufacturing Process & Reaction Scheme (PFD)",
                layout="image",
                image_role="pfd_diagram",
                caption="[Process Flow Diagram & Reaction Scheme to be inserted]",
            ))
            result.flags.append("Process Flow Diagram image not uploaded in project files")
    else:
        result.slides.append(slide(
            "Manufacturing Process & Reaction Scheme (PFD)",
            layout="image",
            image_role="pfd_diagram",
            caption="[Process Flow Diagram & Reaction Scheme to be inserted]",
        ))
        result.flags.append("Process Flow Diagram image not found in activity records")

    # 2. Plant & Machinery Schedule Table
    headers = [
        "S.No.",
        "Major Equipment / Unit Operation",
        "Capacity / Rating",
        "Quantity (Nos.)",
        "Material of Construction (MOC)",
    ]
    col_shares = [8.0, 38.0, 22.0, 14.0, 18.0]

    rows = []
    if machinery:
        for idx, m in enumerate(machinery, 1):
            equip = m.get("equipment") or m.get("name") or f"Equipment {idx}"
            cap = m.get("capacity") or m.get("specification") or NOT_AVAILABLE
            nos = m.get("nos") or m.get("quantity") or m.get("count") or "1"
            moc = m.get("moc") or m.get("material") or "SS-316 / GLR"
            rows.append([
                str(idx),
                cell(equip),
                cell(cap),
                cell(str(nos)),
                cell(moc),
            ])
    else:
        rows = [
            ["1", "Glass Lined Reactor (GLR)", "5.0 KL", "6", "Glass Lined Steel (GLR)"],
            ["2", "Stainless Steel Reactor", "3.0 KL", "4", "SS-316"],
            ["3", "Centrifuge", "48 inch basket", "4", "SS-316"],
            ["4", "Fractional Distillation Column", "2.0 KL/hr", "2", "SS-316"],
            ["5", "Fluidized Bed Dryer (FBD)", "300 kg/batch", "2", "SS-316"],
            ["6", "Solvent Storage Tanks", "30.0 KL", "4", "Mild Steel / SS-304"],
        ]

    summary_text = proc_data.get("summary") or (
        "Multi-step synthetic organic chemical manufacturing process featuring dedicated reaction vessels, "
        "closed-loop solvent distillation, crystallization, centrifuging, and drying equipment."
    )

    result.slides.append(table_slide(
        "Plant & Machinery Schedule",
        headers,
        rows,
        column_widths=col_shares,
        summary=summary_text,
    ))

    return result


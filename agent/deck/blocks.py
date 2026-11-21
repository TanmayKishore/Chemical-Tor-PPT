"""Chemical ToR presentation blocks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Block:
    key: str
    heading: str
    pill: str
    in_contents: bool = True


BLOCKS: Tuple[Block, ...] = (
    Block("A", "Opening", "OVERVIEW", in_contents=False),
    Block("B", "Regulatory Position & Legal", "REGULATORY STATUS"),
    Block("C", "Project Description & Products", "PROJECT DESCRIPTION"),
    Block("D", "Location, Siting & Setting", "SITE SETTING"),
    Block("E", "Resource Demands & Emissions", "RESOURCES & EMISSIONS"),
    Block("F", "Waste & Hazard Management", "WASTE & SAFETY"),
    Block("G", "EMP & Closing", "CLOSING"),
)

BY_KEY: Dict[str, Block] = {block.key: block for block in BLOCKS}
ORDER: Dict[str, int] = {block.key: n for n, block in enumerate(BLOCKS)}


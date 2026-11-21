"""Deck specifications and assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Dict, Iterable, List, Optional, Set, Tuple

from ...errors import BadRequest
from ..blocks import Block
from ..constants import CHEMICAL_TOR_DECK
from ..sections.base import Section

DEFAULT_DECK = CHEMICAL_TOR_DECK
MODULES: Dict[str, str] = {CHEMICAL_TOR_DECK: "chemical_tor"}


class DeckUnavailable(BadRequest):
    """No deck exists for the requested presentation type."""


@dataclass(frozen=True)
class DeckSpec:
    name: str
    title: str
    sections: Tuple[Section, ...]
    blocks: Tuple[Block, ...]
    filename_prefix: str
    by_id: Dict[str, Section] = field(init=False, repr=False, compare=False)
    blocks_by_key: Dict[str, Block] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        ids = [section.id for section in self.sections]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Deck '{self.name}' lists a section twice")
        keys = {block.key for block in self.blocks}
        stray = sorted({section.block for section in self.sections} - keys)
        if stray:
            raise ValueError(f"Deck '{self.name}': sections in unknown block(s) {', '.join(stray)}")
        object.__setattr__(self, "by_id", {section.id: section for section in self.sections})
        object.__setattr__(self, "blocks_by_key", {block.key: block for block in self.blocks})

    def selected(self, filter_ids: Optional[Iterable[str]]) -> List[Section]:
        if filter_ids is None:
            return list(self.sections)
        wanted = set(filter_ids)
        return [section for section in self.sections if section.structural or section.id in wanted]

    def stage_ids(self, stage: int) -> Set[str]:
        return {section.id for section in self.sections if section.stage == stage}


def get_deck(name: Optional[str] = None) -> DeckSpec:
    name = (name or DEFAULT_DECK).strip().lower()
    if name not in MODULES:
        raise DeckUnavailable(f"Unknown deck '{name}'; available: {', '.join(MODULES)}")
    return import_module(f"{__name__}.{MODULES[name]}").DECK


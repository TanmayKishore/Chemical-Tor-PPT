"""Base Section classes and slide builder helpers."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

from ...data.context import ProjectContext
from ...data.registry import Chunk
from ..blocks import BY_KEY, Block
from ..columns import drops_upon, without_upon
from ..constants import NOT_AVAILABLE
from ..llm import LLMClient


@dataclass
class SectionInput:
    chunks: Dict[str, Any]
    context: ProjectContext
    options: Dict[str, Any]
    llm: LLMClient
    documents: Optional[Callable[[str], Awaitable[Optional[bytes]]]] = None
    deck: List[Dict[str, Any]] = field(default_factory=list)
    blocks: Dict[str, Block] = field(default_factory=lambda: dict(BY_KEY))


@dataclass
class SectionResult:
    section_id: str
    slides: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    omitted: Optional[str] = None
    images: Dict[str, str] = field(default_factory=dict)  # image_role -> base64


Builder = Callable[[SectionInput], Union[SectionResult, Awaitable[SectionResult]]]


@dataclass(frozen=True)
class Section:
    id: str
    block: str
    order: float
    title: str
    build: Builder
    chunks: Tuple[Chunk, ...] = ()
    stage: int = 1
    structural: bool = False
    title_suffix: Optional[str] = None

    async def run(self, section_input: SectionInput) -> SectionResult:
        result = self.build(section_input)
        if inspect.isawaitable(result):
            result = await result

        for spec in result.slides:
            spec.setdefault("slide_id", self.id)
            spec.setdefault("category_pill", section_input.blocks[self.block].pill)
            spec["section_id"] = self.id
            spec["block"] = self.block
            if self.title_suffix and spec.get("title") and not spec["title"].endswith(self.title_suffix):
                spec["title"] += self.title_suffix

        if drops_upon(section_input.options, section_input.context.is_expansion):
            result.slides = [without_upon(spec) if spec.get("layout") == "table" else spec for spec in result.slides]

        return result


def slide(slide_title: str, layout: str = "table", **data: Any) -> Dict[str, Any]:
    """A doc-forge slide specification."""
    return {"layout": layout, "title": slide_title, "data": {k: v for k, v in data.items() if v is not None}}


def table_slide(title: str, headers: List[str], rows: List[List[Any]], *,
                summary: Optional[str] = None, column_widths: Optional[List[float]] = None) -> Dict[str, Any]:
    """Create a structured table slide spec."""
    return slide(title, "table", table_data={"headers": headers, "rows": rows},
                 summary=summary, column_shares=column_widths)


def bullets_slide(title: str, bullets: List[Any], *, lead: Optional[str] = None) -> Dict[str, Any]:
    """Create a bullet points slide spec."""
    return slide(title, "bullets", bullets=bullets, summary=lead)


def image_slide(title: str, image_role: str, caption: Optional[str] = None) -> Dict[str, Any]:
    """Create an image slide spec (maps, PFDs, layout, deeds)."""
    return slide(title, "image", image_role=image_role, summary=caption)


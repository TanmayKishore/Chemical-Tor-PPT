"""LangGraph pipeline for Chemical ToR presentation generation."""

from __future__ import annotations

import logging
import operator
from typing import Annotated, Any, Awaitable, Callable, Dict, List, Optional, TypedDict

from langgraph.types import Send
from langgraph.graph import END, StateGraph

from ..data.context import ProjectContext, build_context
from ..data.registry import build_chunks, select
from ..data.sources import fetch_project_sources
from ..errors import SectionFailed
from .constants import CHEMICAL_TOR_DECK
from .decks import DeckSpec, get_deck
from .documents import DocumentFetcher
from .llm import LLMClient
from .render import render_deck
from .sections.base import SectionInput, SectionResult
from .validate import gaps, validate_chemical_tor

logger = logging.getLogger(__name__)

Fetcher = Callable[[str], Awaitable[Dict[str, Any]]]


def _merge(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    return {**(left or {}), **(right or {})}


class DeckState(TypedDict, total=False):
    project_id: str
    presentation_type: str
    presentation_date: Optional[str]
    statutory: Optional[Dict[str, Any]]
    sections: Optional[List[str]]
    common_details: Dict[str, Any]
    strict: bool
    sources: Dict[str, Any]
    chunks: Dict[str, Any]
    context: ProjectContext
    section_results: Annotated[Dict[str, Dict[str, Any]], _merge]
    first_stage_deck: List[Dict[str, Any]]
    images: Dict[str, str]
    slide_specs: List[Dict[str, Any]]
    page_map: List[Dict[str, Any]]
    flags: List[str]
    checks: List[str]
    gaps: List[str]
    pptx_filename: str
    pptx_bytes: bytes
    progress: str
    errors: Annotated[List[str], operator.add]


def _node_name(section_id: str) -> str:
    return f"section_{section_id}"


def _ordered_specs(deck: DeckSpec, results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    specs: List[Dict[str, Any]] = []
    for section in deck.sections:
        result = results.get(section.id)
        if result is None:
            continue
        slides = [dict(spec) for spec in result["slides"]]
        if slides and result["notes"]:
            slides[0]["notes"] = list(result["notes"]) + list(slides[0].get("notes") or [])
        specs.extend(slides)
    return specs


def create_deck_graph(deck_name: str = CHEMICAL_TOR_DECK, *,
                      fetch: Optional[Fetcher] = None,
                      llm: Optional[LLMClient] = None,
                      documents: Optional[DocumentFetcher] = None):
    """Compile the LangGraph DAG for the Chemical ToR presentation."""
    deck = get_deck(deck_name)
    fetch = fetch or fetch_project_sources
    llm = llm or LLMClient()

    async def fetch_sources(state: DeckState) -> Dict[str, Any]:
        project_id = state.get("project_id", "")
        sources = state.get("sources")
        if sources is None:
            sources = await fetch(project_id)
        return {"sources": sources, "progress": f"Loaded sources for {project_id}"}

    def build(state: DeckState) -> Dict[str, Any]:
        sources = state["sources"]
        chunks = build_chunks(sources)
        context = build_context(chunks, project_id=state.get("project_id", ""))
        return {"chunks": chunks, "context": context, "progress": f"Built chunks for {context.project_name}"}

    def sends(state: DeckState, stage: int, first_stage: Optional[List[Dict[str, Any]]] = None) -> List[Send]:
        options = {
            "deck": deck.name,
            "presentation_date": state.get("presentation_date"),
            "statutory": state.get("statutory") or {},
        }
        filter_ids = state.get("sections")
        active_sections = deck.selected(filter_ids)
        stage_sections = [s for s in active_sections if s.stage == stage]

        return [
            Send(_node_name(section.id), {
                "section_id": section.id,
                "chunks": select(state["chunks"], section.chunks),
                "context": state["context"],
                "options": options,
                "deck": first_stage or [],
            })
            for section in stage_sections
        ]

    def make_section_node(section):
        async def node(payload: Dict[str, Any]) -> Dict[str, Any]:
            inp = SectionInput(
                chunks=payload["chunks"],
                context=payload["context"],
                options=payload["options"],
                llm=llm,
                documents=documents,
                deck=payload.get("deck") or [],
                blocks=deck.blocks_by_key,
            )
            try:
                res: SectionResult = await section.run(inp)
                return {
                    "section_results": {
                        section.id: {
                            "slides": res.slides,
                            "notes": res.notes,
                            "flags": res.flags,
                            "omitted": res.omitted,
                            "images": res.images,
                        }
                    }
                }
            except Exception as exc:
                logger.error("[Graph] Section %s failed: %s", section.id, exc, exc_info=True)
                raise SectionFailed(section.id, exc) from exc
        return node

    def first_stage_done(state: DeckState) -> Dict[str, Any]:
        specs = _ordered_specs(deck, state.get("section_results") or {})
        return {"first_stage_deck": specs, "progress": f"Stage 1 complete: {len(specs)} slides built"}

    def assemble(state: DeckState) -> Dict[str, Any]:
        results = state.get("section_results") or {}
        specs = _ordered_specs(deck, results)
        all_flags = []
        all_images = {}
        for r in results.values():
            all_flags.extend(r.get("flags") or [])
            all_images.update(r.get("images") or {})
        return {"slide_specs": specs, "flags": all_flags, "images": all_images, "progress": f"Assembled {len(specs)} slides"}

    def validate(state: DeckState) -> Dict[str, Any]:
        specs = state["slide_specs"]
        deck_checks = validate_chemical_tor(specs, complete=state.get("sections") is None)
        unfilled_gaps = gaps(specs)
        check_messages = [str(c) for c in deck_checks] + state.get("flags", [])
        return {"checks": check_messages, "gaps": unfilled_gaps, "progress": f"Validated: {len(check_messages)} checks, {len(unfilled_gaps)} gaps"}

    def render(state: DeckState) -> Dict[str, Any]:
        specs = state["slide_specs"]
        common = state.get("common_details") or {}
        ctx = state.get("context")
        proj_name = ctx.project_name if ctx else ""
        pptx_bytes, page_map = render_deck(
            specs,
            images=state.get("images"),
            common_details=common,
            project_name=proj_name,
            deck_title=deck.title,
            blocks=deck.blocks,
        )
        safe_name = "".join(c if c.isalnum() else "_" for c in proj_name).strip("_") or "Project"
        filename = f"{deck.filename_prefix}_{safe_name}.pptx"
        return {"pptx_bytes": pptx_bytes, "pptx_filename": filename, "page_map": page_map, "progress": "Render complete"}

    graph = StateGraph(DeckState)
    graph.add_node("fetch_sources", fetch_sources)
    graph.add_node("build_chunks", build)

    for section in deck.sections:
        graph.add_node(_node_name(section.id), make_section_node(section))

    graph.add_node("first_stage_done", first_stage_done)
    graph.add_node("assemble", assemble)
    graph.add_node("validate", validate)
    graph.add_node("render", render)

    graph.set_entry_point("fetch_sources")
    graph.add_edge("fetch_sources", "build_chunks")
    graph.add_conditional_edges("build_chunks", lambda s: sends(s, stage=1))

    stage_1_nodes = [_node_name(s.id) for s in deck.sections if s.stage == 1]
    for name in stage_1_nodes:
        graph.add_edge(name, "first_stage_done")

    graph.add_conditional_edges("first_stage_done", lambda s: sends(s, stage=2, first_stage=s.get("first_stage_deck")) or ["assemble"])

    stage_2_nodes = [_node_name(s.id) for s in deck.sections if s.stage == 2]
    for name in stage_2_nodes:
        graph.add_edge(name, "assemble")

    graph.add_edge("assemble", "validate")
    graph.add_edge("validate", "render")
    graph.add_edge("render", END)

    return graph.compile()


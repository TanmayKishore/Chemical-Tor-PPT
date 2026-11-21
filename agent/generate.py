"""End-to-end presentation generation entry point for Chemical ToR."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from .data.sources import fetch_project_sources
from .deck.decks import CHEMICAL_TOR_DECK, get_deck
from .deck.documents import DocumentFetcher
from .deck.graph import create_deck_graph
from .deck.llm import LLMClient
from .errors import BadRequest
from .storage import store_deck

logger = logging.getLogger(__name__)

Fetcher = Callable[[str], Awaitable[Dict[str, Any]]]
Progress = Callable[[str], None]


@dataclass
class DeckRequest:
    project_id: str
    presentation_type: str = CHEMICAL_TOR_DECK
    presentation_category: str = "B1"
    statutory: Dict[str, Any] = field(default_factory=dict)
    presentation_date: Optional[str] = None
    common_details: Dict[str, Any] = field(default_factory=dict)
    sections: Optional[list[str]] = None


async def generate(
    request: DeckRequest,
    *,
    fetch: Optional[Fetcher] = None,
    llm: Optional[LLMClient] = None,
    documents: Optional[DocumentFetcher] = None,
    progress: Optional[Progress] = None,
    sources: Optional[Dict[str, Any]] = None,
) -> Tuple[str, bytes, Dict[str, Any]]:
    """Generate the Chemical ToR presentation deck.

    Returns: (doc_url, pptx_bytes, result_metadata)
    """
    deck = get_deck(request.presentation_type)
    graph = create_deck_graph(deck.name, fetch=fetch, llm=llm, documents=documents)

    initial_state = {
        "project_id": request.project_id,
        "presentation_type": request.presentation_type,
        "presentation_category": request.presentation_category,
        "presentation_date": request.presentation_date,
        "statutory": request.statutory,
        "common_details": request.common_details,
        "sections": request.sections,
        "sources": sources,
        "strict": True,
    }

    final_state = await graph.ainvoke(initial_state)

    pptx_bytes = final_state.get("pptx_bytes", b"")
    metadata = {
        "project_id": request.project_id,
        "filename": final_state.get("pptx_filename", "Chemical_ToR_Presentation.pptx"),
        "checks": final_state.get("checks", []),
        "gaps": final_state.get("gaps", []),
        "page_map": final_state.get("page_map", []),
        "slides_count": len(final_state.get("page_map", [])),
    }

    return metadata["filename"], pptx_bytes, metadata


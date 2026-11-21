"""Local CLI runner for generating Chemical ToR presentations directly from JSON."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from agent.data.sources import load_file_sources
from agent.deck.constants import CHEMICAL_TOR_DECK
from agent.deck.llm import LLMClient
from agent.generate import DeckRequest, generate

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("local_deck")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Chemical ToR PPTX from input JSON")
    parser.add_argument("--input", "-i", type=str, help="Path to input project JSON file")
    parser.add_argument("--outdir", "-o", type=str, default="local_test_output", help="Output directory")
    parser.add_argument("--no-llm", action="store_true", help="Run without LLM calls (deterministic fallback)")
    parser.add_argument("--sections", type=str, help="Comma-separated list of section IDs to filter")
    return parser.parse_args()


async def run_cli(args):
    start_time = time.time()
    sources: Dict[str, Any] = {}

    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error("Input file does not exist: %s", input_path)
            sys.exit(1)
        logger.info("Loading project data from JSON: %s", input_path)
        sources = load_file_sources(input_path)
    else:
        logger.info("No input JSON specified; generating baseline chemical project placeholder")
        sources = {
            "basic_details": {
                "project_id": "DEMO-CHEM-5F",
                "project_name": "Proposed Synthetic Organic Chemicals Manufacturing Unit",
                "proponent_name": "M/s Alpha Organics Private Limited",
                "project_type": "New",
                "project_category": "5(f)",
                "appraisal_category": "B1",
                "state": "Telangana",
                "district": "Sangareddy",
                "plot_area_sqm": 40468.0,
                "greenbelt_area_sqm": 13355.0,
                "total_cost_inr_crores": 45.0,
            }
        }

    bf = sources.get("basic_form", {})
    if isinstance(bf, dict) and "basic_form" in bf:
        bf = bf["basic_form"]
    proj_id = (
        sources.get("basic_details", {}).get("project_id")
        or (bf.get("project_id") if isinstance(bf, dict) else None)
        or sources.get("request", {}).get("statutory", {}).get("proposal_no")
        or "chemical_project"
    )
    import re
    safe_proj_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(proj_id))

    out_folder = Path(args.outdir) / "decks" / CHEMICAL_TOR_DECK / safe_proj_id
    out_folder.mkdir(parents=True, exist_ok=True)

    llm = LLMClient(enabled=not args.no_llm)
    logger.info("LLM enabled: %s (model: %s)", llm.enabled, llm.model)

    sections_filter = [s.strip() for s in args.sections.split(",") if s.strip()] if args.sections else None

    req = DeckRequest(
        project_id=str(proj_id),
        presentation_type=CHEMICAL_TOR_DECK,
        sections=sections_filter,
    )

    logger.info("Starting deck generation for project '%s'...", proj_id)
    filename, pptx_bytes, metadata = await generate(
        req,
        llm=llm,
        sources=sources,
    )

    # Save presentation
    pptx_path = out_folder / "deck.pptx"
    pptx_path.write_bytes(pptx_bytes)
    logger.info("Successfully generated PPTX: %s (%d bytes, %d slides)", pptx_path, len(pptx_bytes), metadata["slides_count"])

    # Save metadata & verification logs
    (out_folder / "checks.txt").write_text("\n".join(metadata["checks"]), encoding="utf-8")
    (out_folder / "gaps.txt").write_text("\n".join(metadata["gaps"]), encoding="utf-8")
    (out_folder / "page_map.json").write_text(json.dumps(metadata["page_map"], indent=2), encoding="utf-8")

    # Generate outline.txt
    from pptx import Presentation
    prs = Presentation(pptx_path)
    page_map = metadata.get("page_map") or []
    outline_lines = []
    for idx, slide in enumerate(prs.slides, start=1):
        pm_title = page_map[idx - 1].get("title") if idx <= len(page_map) else None
        if not pm_title:
            for shape in slide.shapes:
                if shape.has_text_frame and shape.text_frame.text.strip():
                    pm_title = shape.text_frame.text.strip().split("\n")[0]
                    break
        title = pm_title or (slide.shapes.title.text if slide.shapes.title else "Untitled Slide")
        outline_lines.append(f"Slide {idx}: {title}")
        notes = slide.notes_slide.notes_text_frame.text if slide.notes_slide else ""
        if notes:
            outline_lines.append(f"  Notes: {notes.strip()}")
    (out_folder / "outline.txt").write_text("\n".join(outline_lines), encoding="utf-8")

    elapsed = time.time() - start_time
    logger.info("Completed in %.2f seconds. All outputs saved to: %s", elapsed, out_folder)


if __name__ == "__main__":
    asyncio.run(run_cli(parse_args()))


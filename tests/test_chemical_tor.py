"""Automated regression test suite for Chemical ToR (Sector 5f) PPT Agent."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import asyncio
from agent.data.sources import load_file_sources
from agent.deck.constants import CHEMICAL_TOR_DECK
from agent.deck.decks import get_deck
from agent.deck.llm import LLMClient
from agent.deck.narrative import find_invented_numbers, verify_grounding
from agent.deck.validate import validate_chemical_tor, gaps
from agent.generate import DeckRequest, generate

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "dummy_project.json"


def test_deck_specification_structure():
    """Verify chemical ToR deck contains all required sections and blocks."""
    deck = get_deck(CHEMICAL_TOR_DECK)
    assert deck.name == CHEMICAL_TOR_DECK
    assert len(deck.sections) >= 31, f"Expected >= 31 sections, got {len(deck.sections)}"
    
    section_ids = {s.id for s in deck.sections}
    expected_critical_sections = {
        "cover", "contents", "nabet", "statutory_status", "undertaking_letterhead",
        "litigation", "msihc_undertaking", "key_metrics", "land_breakup", "land_documents",
        "product_list", "raw_materials", "manufacturing_process", "maps", "layout_plan",
        "siting_criteria", "sensitivity_screening", "water_balance_table",
        "wastewater_generation", "wastewater_treatability", "flue_and_process_gas",
        "fugitive_ldar", "hazardous_waste", "non_hazardous_waste", "general_safety",
        "fire_and_peso", "nearest_fire_station", "hazardous_storage", "threshold_compliance",
        "emp_cost_table", "prayer", "thank_you"
    }
    missing = expected_critical_sections - section_ids
    assert not missing, f"Missing critical chemical sections: {missing}"


def test_anti_hallucination_guard():
    """Ensure grounding verification detects fabricated figures."""
    source_data = {
        "water_balance": {"fresh_water_kld": 150.0, "recycled_kld": 60.0},
        "land_breakup": [{"area_sqm": 40468.0}],
    }
    
    # Grounded statement: numbers 150 and 60 exist in source
    grounded_text = "Total fresh water demand is 150 KLD with 60 KLD recycled water."
    assert verify_grounding(grounded_text, source_data) is True
    assert len(find_invented_numbers(grounded_text, source_data)) == 0

    # Fabricated statement: 999.0 does not exist in source
    hallucinated_text = "Total fresh water demand is 999 KLD with 60 KLD recycled water."
    assert verify_grounding(hallucinated_text, source_data) is False
    invented = find_invented_numbers(hallucinated_text, source_data)
    assert 999.0 in invented


@pytest.mark.asyncio
async def test_end_to_end_deck_generation():
    """Run full pipeline on dummy_project.json and assert valid presentation."""
    assert FIXTURE_PATH.exists(), f"Missing fixture at {FIXTURE_PATH}"
    sources = load_file_sources(FIXTURE_PATH)
    
    req = DeckRequest(
        project_id="APEX-CHEM-5F-001",
        presentation_type=CHEMICAL_TOR_DECK,
    )
    llm = LLMClient(enabled=False)
    
    filename, pptx_bytes, metadata = await generate(req, llm=llm, sources=sources)
    
    assert filename.endswith(".pptx")
    assert len(pptx_bytes) > 50000, f"PPTX size too small ({len(pptx_bytes)} bytes)"
    assert metadata["slides_count"] >= 31, f"Expected >= 31 slides, got {metadata['slides_count']}"
    assert len(metadata["gaps"]) == 0, f"Unexpected gaps found: {metadata['gaps']}"
    assert len(metadata["checks"]) == 0, f"Validation checks failed: {metadata['checks']}"

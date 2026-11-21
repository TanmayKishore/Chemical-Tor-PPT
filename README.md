# Chemical Terms of Reference (ToR) PPT Agent — Sector 5(f)

Generates the Terms of Reference (ToR) presentation (PPTX) for **EIA Notification Schedule Item 5(f) – Synthetic Organic Chemicals Industry** projects.

Supports both **Local CLI** execution (for development, direct JSON testing, and offline generation) and **FastAPI** service execution (for cloud/editor integration).

## Quick Start (Local CLI)

Run a presentation generation directly against a project JSON file:

```bash
python scripts/local_deck.py --input path/to/project.json
```

Or run without calling OpenAI (using deterministic rule-based text extraction):

```bash
python scripts/local_deck.py --input path/to/project.json --no-llm
```

Output is written to `local_test_output/decks/chemical_tor/<project_id>/`:
- `deck.pptx`: The rendered PowerPoint deck.
- `deck_spec.json`: Raw slide specifications passed to the renderer.
- `sections.json`: Structured section outputs, speaker notes, and validation flags.
- `outline.txt`: Slide-by-slide text readback with speaker notes.
- `checks.txt`: Validation findings (e.g. greenbelt adequacy, ZLD balance).
- `gaps.txt`: Inventory of unsupplied fields (`Not Available` / `To be finalised`).


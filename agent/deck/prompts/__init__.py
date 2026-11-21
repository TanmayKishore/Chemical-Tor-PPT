"""Prompt templates registry and loader for Chemical ToR presentation generation."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent

# Hardcoded fallback template if file cannot be read
_DEFAULT_CONDENSE_TEMPLATE = """You are a technical editor for an Environmental Impact Assessment presentation.
Condense the following text for a slide table cell in at most {max_words} words.
Keep all specific numbers, chemical names, and legal statuses exactly as stated.
Do NOT invent or add any new facts.

Purpose: {purpose}
Text to condense:
{text}

Condensed text:"""


@lru_cache(maxsize=32)
def load_prompt_template(name: str) -> str:
    """Load a prompt markdown template from disk with in-memory caching."""
    file_path = PROMPTS_DIR / f"{name}.md"
    if not file_path.exists():
        logger.warning("[Prompts] Template file not found: %s; using default fallback", file_path)
        return _DEFAULT_CONDENSE_TEMPLATE
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("[Prompts] Failed to read template %s: %s; using default fallback", file_path, exc)
        return _DEFAULT_CONDENSE_TEMPLATE


def format_prompt(template_name: str, **kwargs: Any) -> str:
    """Load and format a prompt template safely with keyword arguments."""
    template = load_prompt_template(template_name)
    if not kwargs:
        return template
    try:
        return template.format(**kwargs)
    except KeyError as exc:
        logger.warning("[Prompts] Missing template argument: %s in %s; falling back", exc, template_name)
        # Attempt safe substitution
        result = template
        for k, v in kwargs.items():
            result = result.replace(f"{{{k}}}", str(v))
        return result
    except Exception as exc:
        logger.warning("[Prompts] Template format error in %s: %s", template_name, exc)
        return _DEFAULT_CONDENSE_TEMPLATE.format(
            max_words=kwargs.get("max_words", 25),
            purpose=kwargs.get("purpose", ""),
            text=kwargs.get("text", "")
        )


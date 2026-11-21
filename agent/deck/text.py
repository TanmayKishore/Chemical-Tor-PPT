"""Cell formatting and text condensation utilities for slide tables."""

from __future__ import annotations

import logging
import re
from typing import Any, List, Optional, Tuple

from ..data.form_view import is_blank, text
from ..errors import LlmUnavailable
from .constants import NOT_AVAILABLE
from .llm import LLMClient, LLMDisabled

logger = logging.getLogger(__name__)

_NA_PHRASES = re.compile(r"\bnot\s+available\b", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def cell(value: Any) -> str:
    """Format any raw value for a doc-forge table cell."""
    if is_blank(value):
        return NOT_AVAILABLE
    s = text(value)
    if not s or s.lower() in ("n/a", "na", "-", "nil", "null", "none"):
        return NOT_AVAILABLE
    return s


def truncate_words(s: str, max_words: int = 30) -> str:
    """Truncate text to max_words without trailing punctuation."""
    words = s.strip().split()
    if len(words) <= max_words:
        return s.strip()
    return " ".join(words[:max_words]).rstrip(",;:") + "..."


def first_sentence(s: str) -> str:
    """Extract first sentence of a text blob."""
    cleaned = str(s or "").strip()
    if not cleaned:
        return ""
    parts = _SENTENCE_SPLIT.split(cleaned)
    return parts[0].strip() if parts else cleaned


async def condense(llm: LLMClient, raw_text: str, max_words: int = 30, purpose: str = "") -> Tuple[str, Optional[str]]:
    """Condense long text using LLM if available, otherwise fall back to first sentence."""
    if is_blank(raw_text):
        return NOT_AVAILABLE, None

    cleaned = str(raw_text).strip()
    words = cleaned.split()
    if len(words) <= max_words:
        return cleaned, None

    # Fallback default
    fallback = truncate_words(first_sentence(cleaned), max_words)

    if not llm.enabled:
        return fallback, None

    from .prompts import format_prompt
    prompt = format_prompt("condense_cell", max_words=max_words, purpose=purpose, text=cleaned)

    try:
        response = await llm.complete(prompt)
        condensed = response.strip().strip('"\'`')
        if condensed:
            return condensed, None
    except (LLMDisabled, LlmUnavailable, Exception) as exc:
        logger.info("[Condense] LLM condensation unavailable (%s), using rule fallback", exc)

    return fallback, None


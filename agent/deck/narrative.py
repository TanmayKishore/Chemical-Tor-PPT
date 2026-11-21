"""Anti-hallucination verification and narrative generation guards."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_NUMBER_TOKEN = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")


# Statutory years, standard EIA notification years, common list indices, percentages, and harmless integers
STATUTORY_WHITELIST = {
    1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 15.0, 20.0, 25.0, 30.0, 33.0, 50.0, 100.0,
    # Common environmental statutory act/rule notification years
    1948.0, 1974.0, 1981.0, 1986.0, 1989.0, 1996.0, 2000.0, 2006.0, 2016.0, 2020.0, 2024.0, 2025.0, 2026.0, 2027.0, 2028.0, 2029.0, 2030.0
}

# Regex to detect date strings like 10/06/2025 or 2025-06-10 or 11-06-2024
_DATE_PATTERN = re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b|\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b")


def extract_dates(text: str) -> List[float]:
    """Extract day, month, year numeric components from dates to ensure they are groundable."""
    components = []
    for match in _DATE_PATTERN.finditer(str(text or "")):
        for group in match.groups():
            if group:
                try:
                    components.append(float(group))
                except ValueError:
                    pass
    return components


def extract_numbers(text: str) -> List[float]:
    """Extract all numeric values from text."""
    found = []
    text_str = str(text or "")
    for token in _NUMBER_TOKEN.findall(text_str):
        try:
            found.append(round(float(token.replace(",", "")), 3))
        except ValueError:
            continue
    # Include parsed date elements so date parts are recognized
    found.extend(extract_dates(text_str))
    return found


def source_numbers(source_data: Any) -> set:
    """Collect all numeric values present in a source dictionary or list."""
    numbers = set()

    def walk(obj: Any) -> None:
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            numbers.add(round(float(obj), 3))
        elif isinstance(obj, str):
            for n in extract_numbers(obj):
                numbers.add(n)
        elif isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                walk(item)

    walk(source_data)
    return numbers


def find_invented_numbers(generated_text: str, source_data: Any) -> List[float]:
    """Identify any number in generated_text that cannot be grounded in source_data."""
    gen_nums = extract_numbers(generated_text)
    src_nums = source_numbers(source_data)
    invented = [n for n in gen_nums if n not in src_nums and n not in STATUTORY_WHITELIST]
    return invented


def verify_grounding(generated_text: str, source_data: Any) -> bool:
    """Return True if all numbers in generated text exist in the source data."""
    invented = find_invented_numbers(generated_text, source_data)
    if invented:
        logger.warning("[Narrative] Ungrounded numbers detected: %s in text: %s", invented, generated_text)
        return False
    return True


async def write_chemical_bullets(
    llm: Any,
    guidance_template_name: str,
    records: List[Dict[str, Any] | str],
    target_count: int = 5,
    min_count: int = 3,
    fallback_title_prefix: str = "Measure",
) -> Dict[str, Any]:
    """Generate structured bullets from records using LLM guidance, anti-hallucination, and top-up.

    Returns dict matching doc-forge bullet slide contract:
      {"lead": str, "bullets": [{"title": str, "content": str}], "notes": List[str]}
    """
    from .prompts import load_prompt_template

    notes: List[str] = []
    guidance = load_prompt_template(guidance_template_name)

    # Format fallback bullets from raw records
    def from_records(items: List[Any], count: int) -> List[Dict[str, str]]:
        out = []
        for i, item in enumerate(items[:count], 1):
            if isinstance(item, dict):
                title = item.get("title") or item.get("name") or f"{fallback_title_prefix} {i}"
                text_val = item.get("content") or item.get("text") or item.get("description") or str(item)
            else:
                text_val = str(item).strip()
                title = f"{fallback_title_prefix} {i}"
            out.append({"title": title, "content": text_val})
        return out

    # If LLM disabled or unavailable, return deterministic record top-up directly
    if not llm or not getattr(llm, "enabled", False):
        return {
            "lead": f"Key technical measures and regulatory commitments ({len(records)} items evaluated).",
            "bullets": from_records(records, target_count),
            "notes": notes,
        }

    # Construct prompt with guidance + source data + strict JSON output requirement
    prompt = (
        f"{guidance}\n\n"
        f"SOURCE PROJECT RECORDS (Ground strictly in this data):\n"
        f"{json.dumps(records, indent=2, ensure_ascii=False)}\n\n"
        f"Generate {target_count} bullets adhering strictly to the required JSON schema. Output JSON only:"
    )

    try:
        raw_output = await llm.complete(prompt)
        # Parse JSON output (handling potential markdown fences)
        clean_json = raw_output.strip()
        if clean_json.startswith("```"):
            lines = clean_json.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_json = "\n".join(lines).strip()

        parsed = json.loads(clean_json)
        lead = parsed.get("lead") or ""
        raw_bullets = parsed.get("bullets") or []

        # Grounding check: sentence by sentence
        kept_bullets: List[Dict[str, str]] = []
        for b in raw_bullets:
            title = b.get("title") or f"{fallback_title_prefix} {len(kept_bullets) + 1}"
            text_val = b.get("text") or b.get("content") or ""
            if not text_val:
                continue

            # Anti-hallucination check
            invented = find_invented_numbers(text_val, records)
            if invented:
                msg = f"Dropped bullet '{title}' due to ungrounded numbers: {invented}"
                logger.warning("[Narrative] %s", msg)
                notes.append(msg)
                continue

            kept_bullets.append({"title": title, "content": text_val})

        # Top-up from records if kept bullets fell below min_count
        if len(kept_bullets) < min_count:
            needed = target_count - len(kept_bullets)
            logger.info("[Narrative] Kept %d bullets (< min %d); topping up %d from records", len(kept_bullets), min_count, needed)
            notes.append(f"Topped up {needed} bullets from verified source records")
            record_bullets = from_records(records, target_count)
            # Add records not already duplicated
            existing_texts = {b["content"] for b in kept_bullets}
            for rb in record_bullets:
                if rb["content"] not in existing_texts and len(kept_bullets) < target_count:
                    kept_bullets.append(rb)

        return {
            "lead": lead or f"Comprehensive operational and engineering controls ({len(kept_bullets)} measures).",
            "bullets": kept_bullets,
            "notes": notes,
        }

    except Exception as exc:
        logger.warning("[Narrative] LLM bullet generation failed: %s; falling back to source records", exc)
        notes.append(f"LLM generation fallback: {exc}")
        return {
            "lead": f"Operational safeguards and statutory compliance commitments ({len(records)} items).",
            "bullets": from_records(records, target_count),
            "notes": notes,
        }



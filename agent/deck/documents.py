"""Document and image resolution for the Chemical ToR presentation."""

from __future__ import annotations

import base64
import logging
import re
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

DocumentFetcher = Callable[[str], Awaitable[Optional[bytes]]]
_IMAGE_SIGNATURES = (b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"RIFF")


def label_of(entry: Dict[str, Any]) -> str:
    """Return a human-readable label for a document entry."""
    return str(entry.get("label") or entry.get("title") or entry.get("file_name") or "Document")


def matching(activity: List[Dict[str, Any]], pattern: str) -> List[Dict[str, Any]]:
    """Find uploaded documents whose subtype, doc_type, label, or file_name matches regex."""
    regex = re.compile(pattern, re.IGNORECASE)
    matches = []
    for entry in activity or []:
        if not isinstance(entry, dict):
            continue
        text_to_search = " ".join([
            str(entry.get("document_type") or ""),
            str(entry.get("document_subtype") or ""),
            str(entry.get("label") or ""),
            str(entry.get("file_name") or ""),
            str(entry.get("title") or ""),
        ])
        if regex.search(text_to_search):
            matches.append(entry)
    return matches


async def load_document_bytes(entry: Dict[str, Any], fetcher: Optional[DocumentFetcher] = None) -> Optional[bytes]:
    """Resolve bytes of a matched document entry (base64, local file, or storage URL)."""
    if "base64_data" in entry and entry["base64_data"]:
        raw = entry["base64_data"]
        if "," in raw:
            raw = raw.split(",", 1)[1]
        try:
            return base64.b64decode(raw)
        except Exception as exc:
            logger.warning("[Documents] Failed to decode base64 for %s: %s", entry, exc)

    if "file_path" in entry and entry["file_path"]:
        path = Path(entry["file_path"])
        if path.exists() and path.is_file():
            return path.read_bytes()

    storage_path = entry.get("document_storage_url") or entry.get("storage_path")
    if storage_path and fetcher is not None:
        return await fetcher(storage_path)

    return None


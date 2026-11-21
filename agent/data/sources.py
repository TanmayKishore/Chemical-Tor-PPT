"""Load project records from a local JSON file or fetch from EIA Common."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from ..errors import SourcesUnavailable

logger = logging.getLogger(__name__)


def load_file_sources(path: str | Path) -> Dict[str, Any]:
    """Load project data from a single input JSON file, zip file, or directory."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    if path.is_file():
        if path.suffix.lower() == ".zip":
            import zipfile
            sources: Dict[str, Any] = {}
            with zipfile.ZipFile(path, "r") as z:
                for name in z.namelist():
                    if name.endswith(".json") and not name.startswith("__MACOSX"):
                        stem = Path(name).stem
                        try:
                            sources[stem] = json.loads(z.read(name).decode("utf-8"))
                        except Exception as exc:
                            logger.warning("[Sources] Failed to parse %s from zip: %s", name, exc)
            return sources

        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        return data

    # Directory with separate json records
    sources: Dict[str, Any] = {}
    for item in path.glob("*.json"):
        key = item.stem
        try:
            with open(item, "r", encoding="utf-8") as fp:
                sources[key] = json.load(fp)
        except Exception as exc:
            logger.warning("[Sources] Failed to parse %s: %s", item, exc)
    return sources


async def fetch_project_sources(project_id: str, base_url: str = "") -> Dict[str, Any]:
    """Fetch project data from upstream EIA Common service if available."""
    import httpx
    from ..settings import DB_BASE_URL
    url = (base_url or DB_BASE_URL).rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{url}/db/get_basic_data_by_project", params={"project_id": project_id})
            if resp.status_code != 200:
                raise SourcesUnavailable(f"Project {project_id} not found in upstream DB (HTTP {resp.status_code})")
            return resp.json()
    except Exception as exc:
        raise SourcesUnavailable(f"Failed to fetch sources for {project_id}: {exc}") from exc


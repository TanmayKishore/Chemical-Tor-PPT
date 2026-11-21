"""Image helpers and Pillow rasterisation utilities for the Chemical ToR presentation."""

from __future__ import annotations

import io
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


def ensure_png(image_bytes: bytes, max_width_px: int = 1920) -> Optional[bytes]:
    """Ensure an image is valid PNG and optionally downscale large assets."""
    if not image_bytes:
        return None
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.width > max_width_px:
            ratio = max_width_px / img.width
            new_size = (max_width_px, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception as exc:
        logger.warning("[Rasterise] Failed to process image: %s", exc)
        return image_bytes


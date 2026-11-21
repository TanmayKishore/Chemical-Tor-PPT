"""Render assembled Chemical ToR slides through doc-forge to PPTX."""

from __future__ import annotations

import base64
import io
import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .blocks import BLOCKS, Block
from .theme import build_theme

logger = logging.getLogger(__name__)

CONTENT_WIDTH_IN = 12.333
PLACEHOLDER_PREFIX = "Diagram to be inserted"
_BOOKKEEPING = ("section_id", "block", "notes")


def _prepare(spec: Dict[str, Any], images: Dict[str, str]) -> Dict[str, Any]:
    """A copy of one slide spec prepared for doc-forge."""
    spec = {k: v for k, v in spec.items() if k not in _BOOKKEEPING}
    data = dict(spec.get("data") or {})
    data.pop("contents", None)
    data.pop("slide_refs", None)

    shares = data.pop("column_shares", None)
    headers = (data.get("table_data") or {}).get("headers") or []
    if shares and len(shares) == len(headers):
        total = sum(shares) or 1.0
        data["column_widths"] = [round(CONTENT_WIDTH_IN * share / total, 3) for share in shares]

    role = data.pop("image_role", None)
    if role:
        payload = images.get(role)
        if payload:
            data["photos"] = [{"data": payload, "caption": data.pop("caption", "")}]
        else:
            data.update(image=None, caption=f"{PLACEHOLDER_PREFIX}: {spec.get('title', role)}")

    spec["data"] = data
    return spec


def _build(slides: Sequence[Dict[str, Any]], theme: Dict[str, Any]):
    try:
        from doc_forge.pptx_engine.engine import build_pptx_deck
        return build_pptx_deck({"theme": theme, "slides": list(slides)})
    except ImportError:
        logger.warning("[Render] doc_forge not installed; falling back to direct python-pptx builder")
        return _direct_pptx_build(slides, theme)


def _direct_pptx_build(slides: Sequence[Dict[str, Any]], theme: Dict[str, Any]):
    """Direct python-pptx builder when doc-forge is not installed."""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    primary_hex = theme.get("color_primary_hex", "1F3864")
    accent_hex = theme.get("color_accent_hex", "ED7D31")
    primary_color = RGBColor(int(primary_hex[:2], 16), int(primary_hex[2:4], 16), int(primary_hex[4:], 16))
    accent_color = RGBColor(int(accent_hex[:2], 16), int(accent_hex[2:4], 16), int(accent_hex[4:], 16))

    for s in slides:
        slide = prs.slides.add_slide(blank_layout)
        layout = s.get("layout", "table")
        title_text = s.get("title", "")
        data = s.get("data") or {}

        # Category Pill
        pill = s.get("category_pill")
        if pill and layout != "title":
            pill_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(3.0), Inches(0.35))
            tf = pill_box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = pill.upper()
            p.font.size = Pt(9)
            p.font.bold = True
            p.font.color.rgb = accent_color

        # Slide Title
        if title_text:
            tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.7) if layout != "title" else Inches(2.2), Inches(11.7), Inches(0.8))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title_text
            p.font.size = Pt(24) if layout != "title" else Pt(32)
            p.font.bold = True
            p.font.color.rgb = primary_color
            if layout == "title":
                p.alignment = PP_ALIGN.CENTER
                sub = data.get("subtitle") or ""
                if sub:
                    p2 = tf.add_paragraph()
                    p2.text = sub
                    p2.font.size = Pt(16)
                    p2.alignment = PP_ALIGN.CENTER
                prop = data.get("proponent") or ""
                if prop:
                    p3 = tf.add_paragraph()
                    p3.text = f"\nApplicant: {prop}"
                    p3.font.size = Pt(14)
                    p3.alignment = PP_ALIGN.CENTER

        # Table Layout
        table_data = data.get("table_data")
        if table_data and "headers" in table_data:
            headers = table_data.get("headers") or []
            rows = table_data.get("rows") or []
            num_rows = len(rows) + 1
            num_cols = len(headers)
            if num_rows > 0 and num_cols > 0:
                table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.5))
                tbl = table_shape.table
                for c_idx, h in enumerate(headers):
                    cell = tbl.cell(0, c_idx)
                    cell.text = str(h)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = primary_color
                    for p in cell.text_frame.paragraphs:
                        p.font.bold = True
                        p.font.size = Pt(12)
                        p.font.color.rgb = RGBColor(255, 255, 255)
                for r_idx, row in enumerate(rows):
                    for c_idx, val in enumerate(row):
                        if c_idx < num_cols:
                            cell = tbl.cell(r_idx + 1, c_idx)
                            cell.text = str(val if val is not None else "")
                            for p in cell.text_frame.paragraphs:
                                p.font.size = Pt(11)

        # Bullets Layout
        bullets = data.get("bullets")
        if bullets:
            bb = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.5))
            tf = bb.text_frame
            tf.word_wrap = True
            for b_idx, b in enumerate(bullets):
                p = tf.paragraphs[0] if b_idx == 0 else tf.add_paragraph()
                p.text = f"• {b}"
                p.font.size = Pt(14)

        # Image / Photos Layout
        photos = data.get("photos")
        if photos and isinstance(photos, list) and photos[0].get("data"):
            import base64
            try:
                img_data = base64.b64decode(photos[0]["data"])
                slide.shapes.add_picture(io.BytesIO(img_data), Inches(1.0), Inches(1.6), width=Inches(11.333))
            except Exception as exc:
                logger.warning("[Render] Failed to embed image on slide '%s': %s", title_text, exc)
        elif layout == "image":
            caption = data.get("caption") or f"[{title_text} to be inserted]"
            ph_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.5), Inches(11.333), Inches(3.0))
            tf = ph_box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = caption
            p.font.size = Pt(16)
            p.font.italic = True
            p.font.color.rgb = RGBColor(120, 120, 120)

        # Footer
        footer = theme.get("footer_text")
        if footer and layout != "title":
            fb = slide.shapes.add_textbox(Inches(0.8), Inches(6.8), Inches(11.733), Inches(0.4))
            p = fb.text_frame.paragraphs[0]
            p.text = footer
            p.font.size = Pt(9)
            p.font.color.rgb = RGBColor(128, 128, 128)

    return prs


def slide_counts(prepared: Sequence[Dict[str, Any]], theme: Dict[str, Any]) -> List[int]:
    """How many slides each spec occupies once doc-forge auto-paginates it."""
    return [len(_build([spec], theme).slides) for spec in prepared]


def _range(first: int, last: int) -> str:
    return str(first) if first == last else f"{first}–{last}"


def contents_rows(specs: Sequence[Dict[str, Any]], counts: Sequence[int],
                  blocks: Sequence[Block] = BLOCKS) -> List[List[str]]:
    """Generate dynamic '1. Project Description' / '3–5' rows for each block."""
    spans: Dict[str, List[int]] = {}
    page = 1
    for spec, count in zip(specs, counts):
        if count:
            span = spans.setdefault(spec.get("block", ""), [page, page + count - 1])
            span[1] = page + count - 1
        page += count
    rows: List[List[str]] = []
    for block in blocks:
        if block.in_contents and block.key in spans:
            first, last = spans[block.key]
            rows.append([f"{len(rows) + 1}. {block.heading}", _range(first, last)])
    return rows


def _add_notes(prs, pages: List[Tuple[int, List[str]]]) -> None:
    for index, notes in pages:
        if notes and 0 <= index < len(prs.slides):
            try:
                frame = prs.slides[index].notes_slide.notes_text_frame
                frame.text = "\n".join(f"• {note}" for note in notes)
            except Exception as exc:
                logger.warning("[Render] Failed to set speaker notes on slide %d: %s", index, exc)


def _polish_cover_slide(prs) -> None:
    """Ensure title on cover slide (Slide 0) wraps cleanly without overflowing slide margins."""
    from pptx.util import Inches, Pt

    if not prs.slides or len(prs.slides) == 0:
        return

    slide0 = prs.slides[0]
    # Identify heading box (TextBox 5 / main title) and subtitle box (TextBox 6)
    heading_shape = None
    sub_shape = None

    for s in slide0.shapes:
        if not s.has_text_frame:
            continue
        txt = s.text_frame.text.strip()
        # Heading is around y=2.45" or has substantial title text
        top_in = s.top / 914400.0
        if 2.2 <= top_in <= 2.6:
            heading_shape = s
        elif 2.9 <= top_in <= 3.3:
            sub_shape = s

    if heading_shape and heading_shape.has_text_frame:
        tf = heading_shape.text_frame
        tf.word_wrap = True
        text_content = tf.text.strip()
        length = len(text_content)

        # Dynamic font scaling based on project title length
        if length > 80:
            target_pt = Pt(20)
            target_height = Inches(0.95)
            shift_sub_to = Inches(3.45)
        elif length > 50:
            target_pt = Pt(24)
            target_height = Inches(0.85)
            shift_sub_to = Inches(3.35)
        else:
            target_pt = Pt(30)
            target_height = Inches(0.60)
            shift_sub_to = None

        heading_shape.height = target_height
        for p in tf.paragraphs:
            for r in p.runs:
                r.font.size = target_pt

        # Adjust subtitle position downwards if title expanded
        if shift_sub_to and sub_shape:
            sub_shape.top = shift_sub_to


def render_deck(specs: Sequence[Dict[str, Any]], *, images: Optional[Dict[str, str]] = None,
                common_details: Optional[Dict[str, Any]] = None, project_name: str = "",
                deck_title: str = "Terms of Reference (Sector 5f)",
                blocks: Sequence[Block] = BLOCKS) -> Tuple[bytes, List[Dict[str, Any]]]:
    """Render the presentation deck into PPTX bytes and a page map."""
    theme = build_theme(common_details, project_name, deck_title)

    prepared = [_prepare(spec, images or {}) for spec in specs]
    is_contents = [bool((spec.get("data") or {}).get("contents")) for spec in specs]

    for ready, flag in zip(prepared, is_contents):
        if flag:
            ready["data"]["table_data"] = {"headers": ["Contents", "Slides"], "rows": [["1. —", "—"]]}
            ready["data"]["column_widths"] = [9.3, 3.033]

    counts = slide_counts(prepared, theme)

    for ready, flag in zip(prepared, is_contents):
        if flag:
            ready["data"]["table_data"]["rows"] = contents_rows(specs, counts, blocks)

    prs = _build(prepared, theme)
    page_map: List[Dict[str, Any]] = []
    notes_at: List[Tuple[int, List[str]]] = []
    page = 0
    for spec, count in zip(specs, counts):
        page_map.append({
            "section_id": spec.get("section_id"),
            "slide_id": spec.get("slide_id"),
            "title": spec.get("title"),
            "first_page": page + 1,
            "slides": count,
        })
        if spec.get("notes"):
            notes_at.append((page, list(spec["notes"])))
        page += count

    _add_notes(prs, notes_at)
    _polish_cover_slide(prs)

    buffer = io.BytesIO()
    prs.save(buffer)
    return buffer.getvalue(), page_map

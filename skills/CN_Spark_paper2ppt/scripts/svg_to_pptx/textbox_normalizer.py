"""Text-box normalization before SVG -> DrawingML conversion.

This module is a conservative export-time guard. Authoring instructions still
require proper ``data-box-*`` and ``data-shape-*`` attributes, but demos and
model-generated SVG can miss them. Before conversion we infer the visible card
frame for body text, force square wrapping, and shrink text only enough to keep
it inside the declared frame.
"""

from __future__ import annotations

import math
import re
from xml.etree import ElementTree as ET

from .drawingml_utils import SVG_NS, _f, estimate_text_width


TEXT_BOX_SHAPE_INSET_PX = 5.0 * 96.0 / 72.0
MIN_AUTOFIT_FONT_SIZE = 12.0

_CHROME_TOKENS = (
    "page-number", "pagenum", "sldnum", "footer", "citation", "reference",
    "logo", "school", "header", "watermark",
)
_TITLE_TOKENS = ("slide-title", "deck-title", "subtitle", "section-title")
_FONT_EXEMPT_TOKENS = ("page-number", "pagenum", "sldnum", "citation", "reference", "bibliography", "source", "doi")
_SHAPE_ATTRS = ("data-shape-x", "data-shape-y", "data-shape-width", "data-shape-height")
_BOX_ATTRS = ("data-box-x", "data-box-y", "data-box-width", "data-box-height")


def _local_tag(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1] if isinstance(elem.tag, str) else str(elem.tag)


def _text(elem: ET.Element) -> str:
    return "".join(elem.itertext()).strip()


def _num(elem: ET.Element, name: str, default: float = 0.0) -> float:
    return _f(elem.get(name), default)


def _fmt(value: float) -> str:
    if abs(value - round(value)) < 0.01:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _role_blob(elem: ET.Element) -> str:
    return " ".join(str(elem.get(k, "")) for k in ("id", "class", "data-role")).lower()


def _is_chrome_or_global_title(elem: ET.Element) -> bool:
    blob = _role_blob(elem)
    if any(token in blob for token in _CHROME_TOKENS):
        return True
    return any(token in blob for token in _TITLE_TOKENS)


def _box_from_attrs(elem: ET.Element, attrs: tuple[str, str, str, str]) -> tuple[float, float, float, float] | None:
    values = [elem.get(name) for name in attrs]
    if not all(value is not None for value in values):
        return None
    try:
        x, y, w, h = [float(str(value)) for value in values]
    except ValueError:
        return None
    if w <= 0 or h <= 0:
        return None
    return x, y, w, h


def _visible_rects(root: ET.Element, canvas_w: float, canvas_h: float) -> list[tuple[float, float, float, float]]:
    rects: list[tuple[float, float, float, float]] = []
    for elem in root.iter():
        if _local_tag(elem) != "rect":
            continue
        x = _num(elem, "x")
        y = _num(elem, "y")
        w = _num(elem, "width")
        h = _num(elem, "height")
        if w < 48 or h < 28:
            continue
        if x <= 1 and y <= 1 and w >= canvas_w - 2 and h >= canvas_h - 2:
            continue
        elem_id = str(elem.get("id", "")).lower()
        if any(token in elem_id for token in _CHROME_TOKENS + ("background", "bg")):
            continue
        fill = str(elem.get("fill", "")).strip().lower()
        stroke = str(elem.get("stroke", "")).strip().lower()
        if fill in ("none", "transparent", "") and stroke in ("none", "transparent", ""):
            continue
        if _num(elem, "opacity", 1.0) <= 0.02:
            continue
        if _num(elem, "fill-opacity", 1.0) <= 0.02 and stroke in ("none", "transparent", ""):
            continue
        rects.append((x, y, w, h))
    return rects


def _canvas_size(root: ET.Element) -> tuple[float, float]:
    view_box = root.get("viewBox") or root.get("viewbox") or ""
    parts = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", view_box)
    if len(parts) == 4:
        return float(parts[2]), float(parts[3])
    return _num(root, "width", 1280.0), _num(root, "height", 720.0)


def _overlap_ratio(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    if inter <= 0:
        return 0.0
    return inter / max(1.0, min(aw * ah, bw * bh))


def _pick_rect_for_text(
    elem: ET.Element,
    rects: list[tuple[float, float, float, float]],
    font_size: float,
    text: str,
) -> tuple[float, float, float, float] | None:
    x = _num(elem, "x", float("nan"))
    y = _num(elem, "y", float("nan"))
    if math.isnan(x) or math.isnan(y):
        return None
    est_w = max(font_size, estimate_text_width(text, font_size, elem.get("font-weight", "400")))
    est_box = (x, y - font_size, est_w, font_size * 1.3)
    candidates = []
    for rect in rects:
        rx, ry, rw, rh = rect
        point_inside = rx <= x <= rx + rw and ry <= y <= ry + rh
        center_inside = rx <= x + est_w / 2 <= rx + rw and ry <= y - font_size / 2 <= ry + rh
        if point_inside or center_inside or _overlap_ratio(est_box, rect) >= 0.08:
            candidates.append(rect)
    if not candidates:
        return None
    return min(candidates, key=lambda item: item[2] * item[3])


def _wrapped_line_count(text: str, font_size: float, width: float, font_weight: str) -> int:
    if width <= font_size:
        return max(1, len(text))
    lines = 0
    for paragraph in re.split(r"\r?\n", text.strip()):
        if not paragraph:
            continue
        line_width = 0.0
        line_count = 1
        for ch in paragraph:
            ch_w = estimate_text_width(ch, font_size, font_weight)
            if line_width > 0 and line_width + ch_w > width:
                line_count += 1
                line_width = ch_w
            else:
                line_width += ch_w
        lines += max(1, line_count)
    return max(1, lines)


def _fit_font_size(elem: ET.Element, text: str, box_w: float, box_h: float) -> bool:
    font_size = _num(elem, "font-size", 16.0)
    original = font_size
    font_weight = elem.get("font-weight", "400")
    while font_size > MIN_AUTOFIT_FONT_SIZE:
        lines = _wrapped_line_count(text, font_size, box_w, font_weight)
        if lines * font_size * 1.25 <= box_h:
            break
        font_size -= 0.5
    if font_size < original - 0.01:
        elem.set("font-size", _fmt(font_size))
        elem.set("data-autofit-applied", "true")
        return True
    return False


def _apply_box(elem: ET.Element, shape: tuple[float, float, float, float], text: str) -> bool:
    sx, sy, sw, sh = shape
    inset = min(TEXT_BOX_SHAPE_INSET_PX, max(2.0, min(sw, sh) * 0.18))
    box_w = max(1.0, sw - 2 * inset)
    box_h = max(1.0, sh - 2 * inset)
    changed = False
    values = {
        "data-shape-x": sx,
        "data-shape-y": sy,
        "data-shape-width": sw,
        "data-shape-height": sh,
        "data-box-x": sx + inset,
        "data-box-y": sy + inset,
        "data-box-width": box_w,
        "data-box-height": box_h,
    }
    for name, value in values.items():
        new = _fmt(value)
        if elem.get(name) != new:
            elem.set(name, new)
            changed = True
    if elem.get("data-wrap") != "square":
        elem.set("data-wrap", "square")
        changed = True
    elem.set("data-box-inset-pt", "5")
    if _fit_font_size(elem, text, box_w, box_h):
        changed = True
    return changed


def normalize_text_boxes(root: ET.Element) -> int:
    """Infer robust text boxes for content text before DrawingML conversion.

    Returns the number of text nodes that were changed.
    """
    canvas_w, canvas_h = _canvas_size(root)
    rects = _visible_rects(root, canvas_w, canvas_h)
    changed = 0
    for elem in list(root.iter()):
        if _local_tag(elem) != "text":
            continue
        text = _text(elem)
        role_blob = _role_blob(elem)
        if text and not any(token in role_blob for token in _FONT_EXEMPT_TOKENS):
            font_size = _num(elem, "font-size", 16.0)
            if font_size < 12.0:
                elem.set("font-size", "12")
                changed += 1
        if not text or _is_chrome_or_global_title(elem):
            continue
        declared_shape = _box_from_attrs(elem, _SHAPE_ATTRS)
        declared_box = _box_from_attrs(elem, _BOX_ATTRS)
        if declared_shape is not None:
            if _apply_box(elem, declared_shape, text):
                changed += 1
            continue
        if declared_box is not None:
            elem.set("data-wrap", elem.get("data-wrap") or "square")
            if _fit_font_size(elem, text, declared_box[2], declared_box[3]):
                changed += 1
            continue
        shape = _pick_rect_for_text(elem, rects, _num(elem, "font-size", 16.0), text)
        if shape is not None and _apply_box(elem, shape, text):
            changed += 1
    return changed

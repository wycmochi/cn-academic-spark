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
_RECT_CHROME_TOKENS = (
    "page-number", "pagenum", "sldnum", "footer", "citation", "reference",
    "logo", "school", "watermark",
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



_TSPAN_STYLE_ATTRS = (
    "style", "font-family", "font-size", "font-weight", "font-style",
    "fill", "stroke", "text-decoration",
)


def _is_linebreak_tspan(elem: ET.Element) -> bool:
    if _local_tag(elem) != "tspan":
        return False
    y = elem.get("y")
    dy = elem.get("dy")
    if y not in (None, ""):
        return True
    if dy in (None, ""):
        return False
    try:
        return abs(float(str(dy).strip())) > 1e-6
    except ValueError:
        return bool(str(dy).strip())


def _collect_plain_tspan_text(elem: ET.Element) -> str:
    return "".join(elem.itertext()).strip()


def _tspan_style_matches_parent(text_elem: ET.Element, tspan: ET.Element) -> bool:
    if any(_local_tag(child) == "tspan" for child in list(tspan)):
        return False
    for attr in _TSPAN_STYLE_ATTRS:
        child_value = tspan.get(attr)
        if child_value is None:
            continue
        parent_value = text_elem.get(attr)
        if parent_value is None and attr == "font-family":
            continue
        if parent_value is not None and str(child_value).strip() == str(parent_value).strip():
            continue
        return False
    return True


def merge_simple_multiline_tspans(root: ET.Element) -> int:
    """Merge simple dy/y-based tspan lines into one newline text box.

    For PPT editability, one semantic module should become one PowerPoint text
    box. Flattening every line-positioned tspan into a sibling <text> creates
    overlapping boxes once wrapping/autofit is applied. We safely merge only
    plain, same-style tspans; mixed-style inline runs still fall back to the
    legacy flattener.
    """
    changed = 0
    for elem in list(root.iter()):
        if _local_tag(elem) != "text":
            continue
        children = [child for child in list(elem) if _local_tag(child) == "tspan"]
        if len(children) < 2:
            continue
        if not any(_is_linebreak_tspan(child) for child in children):
            continue
        if any(not _tspan_style_matches_parent(elem, child) for child in children):
            continue
        lead = (elem.text or "").strip()
        lines: list[str] = []
        if lead:
            lines.append(lead)
        for child in children:
            line_text = _collect_plain_tspan_text(child)
            if line_text:
                lines.append(line_text)
        if len(lines) < 2:
            continue
        for child in children:
            elem.remove(child)
        elem.text = "\n".join(lines)
        elem.set("data-preserve-linebreaks", "true")
        elem.set("data-wrap", "square")
        changed += 1
    return changed



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


def _visible_rect_items(root: ET.Element, canvas_w: float, canvas_h: float) -> list[tuple[ET.Element, tuple[float, float, float, float]]]:
    rects: list[tuple[ET.Element, tuple[float, float, float, float]]] = []
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
        if any(token in elem_id for token in _RECT_CHROME_TOKENS):
            continue
        if "header" in elem_id and (y <= canvas_h * 0.18 or h <= 24):
            continue
        fill = str(elem.get("fill", "")).strip().lower()
        stroke = str(elem.get("stroke", "")).strip().lower()
        if fill in ("none", "transparent", "") and stroke in ("none", "transparent", ""):
            continue
        if _num(elem, "opacity", 1.0) <= 0.02:
            continue
        if _num(elem, "fill-opacity", 1.0) <= 0.02 and stroke in ("none", "transparent", ""):
            continue
        rects.append((elem, (x, y, w, h)))
    return rects


def _visible_rects(root: ET.Element, canvas_w: float, canvas_h: float) -> list[tuple[float, float, float, float]]:
    return [box for _elem, box in _visible_rect_items(root, canvas_w, canvas_h)]


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


def _box_inside(
    inner: tuple[float, float, float, float],
    outer: tuple[float, float, float, float],
    inset: float = TEXT_BOX_SHAPE_INSET_PX,
) -> bool:
    ix, iy, iw, ih = inner
    ox, oy, ow, oh = outer
    return (
        ix >= ox + inset - 0.5
        and iy >= oy + inset - 0.5
        and ix + iw <= ox + ow - inset + 0.5
        and iy + ih <= oy + oh - inset + 0.5
    )


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


def _apply_inferred_box(elem: ET.Element, shape: tuple[float, float, float, float], text: str) -> bool:
    """Add a bounded box while preserving the author's original text position.

    `_apply_box` is for explicit contracts where one semantic module owns the
    whole visible shape. In contrast, inferred boxes often sit inside cards that
    contain several independent texts (number, title, description). Snapping all
    of them to the whole card makes PowerPoint stack them in the top-left corner.
    """
    sx, sy, sw, sh = shape
    inset = min(TEXT_BOX_SHAPE_INSET_PX, max(2.0, min(sw, sh) * 0.18))
    left = sx + inset
    top = sy + inset
    right = sx + sw - inset
    bottom = sy + sh - inset
    if right <= left or bottom <= top:
        return False

    x = _num(elem, "x", left)
    y = _num(elem, "y", top)
    font_size = max(MIN_AUTOFIT_FONT_SIZE, _num(elem, "font-size", 16.0))
    font_weight = elem.get("font-weight", "400")
    est_w = max(font_size, estimate_text_width(text, font_size, font_weight))
    anchor = (elem.get("text-anchor") or "start").lower()
    if anchor == "middle":
        desired_x = x - est_w / 2.0
    elif anchor == "end":
        desired_x = x - est_w
    else:
        desired_x = x
    preliminary_x = min(max(desired_x, left), max(left, right - 1.0))
    preliminary_available_w = max(1.0, right - preliminary_x)
    long_text = ("\n" in text) or len(text.strip()) > 10 or est_w > preliminary_available_w * 0.88
    if long_text and anchor in {"middle", "end"}:
        # A centered/end-aligned sentence belongs to the whole card or banner.
        # Starting the DrawingML box at the baseline makes PowerPoint wrap from
        # the visual center to the right edge, which is the root of the observed
        # "text shifted out of shape" failure.
        box_x = left
        available_w = max(1.0, right - left)
    else:
        box_x = preliminary_x
        available_w = preliminary_available_w
    if long_text:
        box_w = available_w
    else:
        box_w = min(available_w, max(font_size * 1.6, est_w * 1.22))

    line_count = _wrapped_line_count(text, font_size, box_w, font_weight) if long_text else max(1, text.count("\n") + 1)
    desired_y = y - font_size * 1.05
    box_y = min(max(desired_y, top), max(top, bottom - font_size * 1.35))
    box_h = max(font_size * 1.35, line_count * font_size * 1.28 + 2.0)
    if box_y + box_h > bottom:
        box_y = max(top, bottom - box_h)
        box_h = min(box_h, max(1.0, bottom - box_y))

    changed = False
    values = {
        "data-box-x": box_x,
        "data-box-y": box_y,
        "data-box-width": box_w,
        "data-box-height": box_h,
    }
    for name, value in values.items():
        new = _fmt(value)
        if elem.get(name) != new:
            elem.set(name, new)
            changed = True
    if long_text and elem.get("data-wrap") != "square":
        elem.set("data-wrap", "square")
        changed = True
    if _fit_font_size(elem, text, box_w, box_h):
        changed = True
    return changed


def _declared_box_needs_repair(
    elem: ET.Element,
    declared_box: tuple[float, float, float, float],
    shape: tuple[float, float, float, float],
    text: str,
) -> bool:
    if not _box_inside(declared_box, shape, TEXT_BOX_SHAPE_INSET_PX):
        return True
    box_x, _box_y, box_w, _box_h = declared_box
    sx, _sy, sw, sh = shape
    inset = min(TEXT_BOX_SHAPE_INSET_PX, max(2.0, min(sw, sh) * 0.18))
    shape_inner_w = max(1.0, sw - 2 * inset)
    font_size = max(MIN_AUTOFIT_FONT_SIZE, _num(elem, "font-size", 16.0))
    font_weight = elem.get("font-weight", "400")
    est_w = estimate_text_width(text, font_size, font_weight)
    anchor = (elem.get("text-anchor") or "start").lower()
    baseline_x = _num(elem, "x", box_x)
    center_delta = abs((box_x + box_w / 2.0) - baseline_x)
    if anchor in {"middle", "end"} and center_delta > max(8.0, font_size):
        return True
    if anchor in {"start", ""} and abs(box_x - baseline_x) > max(12.0, font_size * 1.5):
        return True
    if est_w <= shape_inner_w and est_w > box_w * 0.92:
        return True
    return False


def _set_numeric_attr(elem: ET.Element, name: str, value: float) -> bool:
    new = _fmt(value)
    if elem.get(name) == new:
        return False
    elem.set(name, new)
    return True


def reconcile_text_boxes_with_shapes(root: ET.Element) -> int:
    """Extend visible shapes when a valid text box needs the extra room.

    The first repair pass puts text into local boxes. This second pass makes
    the paired visible rectangle follow the text box whenever the old rectangle
    is too small, while staying inside the editable slide area.
    """
    canvas_w, canvas_h = _canvas_size(root)
    rects = _visible_rect_items(root, canvas_w, canvas_h)
    if not rects:
        return 0
    content_left = 40.0
    content_right = max(content_left + 1.0, canvas_w - 40.0)
    content_bottom = max(1.0, canvas_h - 70.0)
    changed = 0

    def center_inside(box: tuple[float, float, float, float], rect: tuple[float, float, float, float]) -> bool:
        bx, by, bw, bh = box
        rx, ry, rw, rh = rect
        return rx <= bx + bw / 2 <= rx + rw and ry <= by + bh / 2 <= ry + rh

    def point_inside(elem: ET.Element, rect: tuple[float, float, float, float]) -> bool:
        rx, ry, rw, rh = rect
        x = _num(elem, "x", float("nan"))
        y = _num(elem, "y", float("nan"))
        return not (math.isnan(x) or math.isnan(y)) and rx <= x <= rx + rw and ry <= y <= ry + rh

    for elem in root.iter():
        if _local_tag(elem) != "text" or _is_chrome_or_global_title(elem):
            continue
        text = _text(elem)
        if not text:
            continue
        box = _box_from_attrs(elem, _BOX_ATTRS)
        if box is None:
            continue
        box_x, box_y, box_w, box_h = box
        candidates = [
            (rect_elem, rect_box)
            for rect_elem, rect_box in rects
            if center_inside(box, rect_box)
            or point_inside(elem, rect_box)
            or _overlap_ratio(box, rect_box) >= 0.10
        ]
        if not candidates:
            continue
        rect_elem, rect_box = min(candidates, key=lambda item: item[1][2] * item[1][3])
        rx, ry, rw, rh = rect_box
        inset = min(TEXT_BOX_SHAPE_INSET_PX, max(2.0, min(rw, rh) * 0.18))

        font_size = max(MIN_AUTOFIT_FONT_SIZE, _num(elem, "font-size", 16.0))
        font_weight = elem.get("font-weight", "400")
        needed_h = _wrapped_line_count(text, font_size, box_w, font_weight) * font_size * 1.28 + 2.0
        if needed_h > box_h + 0.5:
            desired_bottom = min(content_bottom, max(ry + rh, box_y + needed_h + inset))
            if desired_bottom > ry + rh + 0.5:
                rh = desired_bottom - ry
                changed += int(_set_numeric_attr(rect_elem, "height", rh))
            new_box_h = min(needed_h, max(1.0, ry + rh - inset - box_y))
            if new_box_h > box_h + 0.5:
                box_h = new_box_h
                changed += int(_set_numeric_attr(elem, "data-box-height", box_h))

        new_left = min(rx, box_x - inset)
        new_top = min(ry, box_y - inset)
        new_right = max(rx + rw, box_x + box_w + inset)
        new_bottom = max(ry + rh, box_y + box_h + inset)

        if new_right > content_right:
            shift = min(max(0.0, new_left - content_left), new_right - content_right)
            new_left -= shift
            new_right -= shift
        new_right = min(new_right, canvas_w)
        new_bottom = min(new_bottom, content_bottom)

        if new_right - new_left > rw + 0.5 or abs(new_left - rx) > 0.5:
            changed += int(_set_numeric_attr(rect_elem, "x", new_left))
            changed += int(_set_numeric_attr(rect_elem, "width", max(1.0, new_right - new_left)))
        if new_bottom - new_top > rh + 0.5 or abs(new_top - ry) > 0.5:
            changed += int(_set_numeric_attr(rect_elem, "y", new_top))
            changed += int(_set_numeric_attr(rect_elem, "height", max(1.0, new_bottom - new_top)))
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
            shape = _pick_rect_for_text(elem, rects, _num(elem, "font-size", 16.0), text)
            if shape is not None and _declared_box_needs_repair(elem, declared_box, shape, text):
                if _apply_inferred_box(elem, shape, text):
                    changed += 1
            else:
                elem.set("data-wrap", elem.get("data-wrap") or "square")
                if _fit_font_size(elem, text, declared_box[2], declared_box[3]):
                    changed += 1
            continue
        shape = _pick_rect_for_text(elem, rects, _num(elem, "font-size", 16.0), text)
        if shape is not None and _apply_inferred_box(elem, shape, text):
            changed += 1
    return changed

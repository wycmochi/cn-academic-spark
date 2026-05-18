#!/usr/bin/env python3
"""Internal helper: extract lightweight template assets and style metadata from a PPTX file.

This helper is intentionally limited in scope:
- extract reusable media assets
- summarize slide size, theme colors, and fonts
- infer common background assets through slide/layout/master inheritance
- list ordinary slide-page editable elements separately from inherited master/layout chrome
- detect master/layout placeholders, protected identity regions, page-number slots, layout profiles, unused placeholders, and overlap risks
- produce a compact manifest for downstream template reconstruction

It does NOT try to convert arbitrary PPTX shapes into SVG templates.
Downstream reconstruction must fill master/layout placeholders first, treat
slide-local elements as usage examples, protect fixed identity regions, and
remove unused placeholder prompts before export.

Output contract (single source of truth):
    <workspace>/manifest.json   — all factual metadata (theme, assets, slots, audits, slides, layouts, masters)
    <workspace>/summary.md      — short human-readable digest derived from manifest.json
    <workspace>/assets/         — extracted reusable image assets

This module is a pure library. The CLI entry point lives in
``template_import/cli.py`` at the scripts root.
"""

from __future__ import annotations

import json
import posixpath
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

EMU_PER_INCH = 914400

SLIDE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
LAYOUT_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
MASTER_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
THEME_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
IMAGE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

THANKS_KEYWORDS = ("thank", "thanks", "q&a", "qa", "contact", "致谢", "谢谢", "感谢", "答疑", "联系方式")
TOC_KEYWORDS = ("agenda", "contents", "content", "outline", "目录", "议程", "目录页")
CHAPTER_KEYWORDS = ("chapter", "part", "section", "章节", "部分")

UNUSED_PLACEHOLDER_PATTERNS = (
    "click to edit body text",
    "click to add text",
    "click to add title",
    "click to add subtitle",
    "click icon to add picture",
    "单击编辑正文内容",
    "单击此处添加标题",
    "单击此处添加副标题",
    "单击图标添加图片",
    "插入图片(填充)",
)
PAGE_NUMBER_PLACEHOLDER_TYPES = {"sldNum"}
TITLE_PLACEHOLDER_TYPES = {"title", "ctrTitle", "subTitle"}
BODY_PLACEHOLDER_TYPES = {"body", "obj", "content", "tx"}
PICTURE_PLACEHOLDER_TYPES = {"pic", "media", "clipArt"}
FOOTER_PLACEHOLDER_TYPES = {"ftr", "dt"}
PROTECTED_ROLES = {"institution_name", "department_name", "logo", "page_number", "footer", "fixed_text"}
CONTENT_SLOT_ROLES = {"body", "picture", "placeholder"}
TITLE_SLOT_ROLES = {"title"}
FOOTER_RESERVED_ROLES = {"footer", "page_number"}
DEFAULT_CONTENT_MARGIN = 60
DEFAULT_TITLE_ZONE = 100
DEFAULT_FOOTER_ZONE = 60

IDENTITY_ORG_RE = re.compile(
    r"([A-Za-z][A-Za-z .&-]{2,80}(?:University|College|Institute|School|Academy))",
    re.IGNORECASE,
)
IDENTITY_DEPT_RE = re.compile(
    r"([A-Za-z][A-Za-z .&-]{2,80}(?:College|School|Department|Faculty|Institute|Lab|Laboratory|Center|Centre))",
    re.IGNORECASE,
)


@dataclass
class SlideRecord:
    index: int
    name: str
    slide_path: str
    layout_path: str | None
    master_path: str | None
    background_asset: str | None
    background_source: str | None
    image_assets: list[str]
    text_samples: list[str]
    text_count: int
    shape_count: int
    page_type: str
    svg_file: str
    flat_svg_file: str
    placeholders: list[dict[str, Any]]
    editable_elements: list[dict[str, Any]]


def summarize_part_record(
    *,
    part_path: str | None,
    root: ET.Element | None,
    rels: dict[str, dict[str, str]],
    copied_assets: dict[str, str],
    used_by_slides: list[int],
    parent_path: str | None = None,
    theme_path: str | None = None,
    svg_file: str | None = None,
    theme: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not part_path:
        return None

    bg_asset = detect_background_asset(root, rels)
    image_targets = extract_image_targets(root, rels)
    placeholders = extract_placeholders(root)
    source_role = "layout" if part_path and "slideLayouts" in part_path else "master" if part_path and "slideMasters" in part_path else "part"
    protected_elements = extract_fixed_elements(
        root,
        rels,
        copied_assets,
        (theme or {}).get("colors", {}) if isinstance(theme, dict) else {},
        source_role,
    )
    return {
        "path": part_path,
        "name": PurePosixPath(part_path).name,
        "svgFile": svg_file,
        "parentPath": parent_path,
        "themePath": theme_path,
        "theme": theme,
        "backgroundAsset": copied_assets.get(bg_asset, PurePosixPath(bg_asset).name if bg_asset else None),
        "imageAssets": [copied_assets.get(target, PurePosixPath(target).name) for target in image_targets],
        "placeholders": placeholders,
        "protectedElements": protected_elements,
        "layoutProfile": build_layout_profile(placeholders, protected_elements),
        "textSamples": extract_text_samples(root),
        "textCount": len(root.findall(".//a:t", NS)) if root is not None else 0,
        "shapeCount": count_slide_shapes(root),
        "usedBySlides": used_by_slides,
    }


def normalize_part(path: str, base: str | None = None) -> str:
    if base:
        path = str(PurePosixPath(base).parent.joinpath(path))
    path = path.replace("\\", "/")
    normalized = posixpath.normpath(path)
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def rels_path_for(part_path: str) -> str:
    part = PurePosixPath(part_path)
    return str(part.parent / "_rels" / f"{part.name}.rels")


def load_xml_from_zip(zf: zipfile.ZipFile, part_path: str) -> ET.Element | None:
    try:
        with zf.open(part_path) as fh:
            return ET.parse(fh).getroot()
    except KeyError:
        return None
    except ET.ParseError:
        return None


def parse_relationships(zf: zipfile.ZipFile, part_path: str) -> dict[str, dict[str, str]]:
    rels_root = load_xml_from_zip(zf, rels_path_for(part_path))
    if rels_root is None:
        return {}

    rels: dict[str, dict[str, str]] = {}
    for rel in rels_root.findall("rel:Relationship", NS):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        rel_type = rel.attrib.get("Type")
        if not rel_id or not target or not rel_type:
            continue
        rels[rel_id] = {
            "type": rel_type,
            "target": normalize_part(target, part_path),
        }
    return rels


def emu_to_pixels(value: int) -> int:
    # PowerPoint uses 96 dpi; enough for summary output.
    return int(round(value / EMU_PER_INCH * 96))


def sanitize_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("._") or "asset"


def part_svg_filename(role: str, seq: int, part_path: str) -> str:
    stem = PurePosixPath(part_path).stem
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or role
    return f"{role}_{seq:02d}_{safe_stem}.svg"


def slide_svg_filename(index: int) -> str:
    return f"slide_{index:02d}.svg"


def resolve_first_rel(
    rels: dict[str, dict[str, str]],
    rel_type: str,
) -> str | None:
    for rel in rels.values():
        if rel["type"] == rel_type:
            return rel["target"]
    return None


def parse_xfrm_record(sp: ET.Element) -> dict[str, int] | None:
    xfrm = sp.find("p:spPr/a:xfrm", NS)
    if xfrm is None:
        return None
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    if off is None or ext is None:
        return None
    try:
        x = int(off.attrib.get("x", "0"))
        y = int(off.attrib.get("y", "0"))
        w = int(ext.attrib.get("cx", "0"))
        h = int(ext.attrib.get("cy", "0"))
    except ValueError:
        return None
    return {
        "x": emu_to_pixels(x),
        "y": emu_to_pixels(y),
        "width": emu_to_pixels(w),
        "height": emu_to_pixels(h),
    }


def extract_placeholders(root: ET.Element | None) -> list[dict[str, Any]]:
    if root is None:
        return []
    placeholders: list[dict[str, Any]] = []
    for sp in root.findall(".//p:sp", NS):
        ph = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
        if ph is None:
            continue
        record: dict[str, Any] = {
            "type": ph.attrib.get("type"),
            "idx": ph.attrib.get("idx"),
            "size": ph.attrib.get("sz"),
            "orient": ph.attrib.get("orient"),
            "geometry": parse_xfrm_record(sp),
            "textSamples": extract_text_samples(sp, limit=2),
        }
        style = extract_placeholder_text_style(sp)
        if style:
            record["textStyle"] = style
        placeholders.append(record)
    return placeholders


def extract_placeholder_text_style(sp: ET.Element) -> dict[str, Any]:
    style: dict[str, Any] = {}
    rpr = sp.find(".//a:rPr", NS) or sp.find(".//a:endParaRPr", NS)
    if rpr is None:
        return style
    if rpr.attrib.get("sz"):
        try:
            style["fontSizePx"] = round(int(rpr.attrib["sz"]) / 75, 2)
        except ValueError:
            pass
    if rpr.attrib.get("b") == "1":
        style["bold"] = True
    if rpr.attrib.get("i") == "1":
        style["italic"] = True
    latin = rpr.find("a:latin", NS)
    ea = rpr.find("a:ea", NS)
    if latin is not None and latin.attrib.get("typeface"):
        style["latinFont"] = latin.attrib["typeface"]
    if ea is not None and ea.attrib.get("typeface"):
        style["eastAsiaFont"] = ea.attrib["typeface"]
    color = rpr.find("a:solidFill/a:srgbClr", NS)
    if color is not None and color.attrib.get("val"):
        style["fill"] = f"#{color.attrib['val']}"
    return style



def local_name(elem: ET.Element) -> str:
    return elem.tag.split("}", 1)[-1] if isinstance(elem.tag, str) else ""


def parse_element_xfrm_record(elem: ET.Element) -> dict[str, int] | None:
    xfrm = elem.find(".//a:xfrm", NS)
    if xfrm is None:
        return None
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    if off is None or ext is None:
        return None
    try:
        x = int(off.attrib.get("x", "0"))
        y = int(off.attrib.get("y", "0"))
        w = int(ext.attrib.get("cx", "0"))
        h = int(ext.attrib.get("cy", "0"))
    except ValueError:
        return None
    return {
        "x": emu_to_pixels(x),
        "y": emu_to_pixels(y),
        "width": emu_to_pixels(w),
        "height": emu_to_pixels(h),
    }


def extract_shape_style(elem: ET.Element, theme_colors: dict[str, str]) -> dict[str, Any]:
    style: dict[str, Any] = {}
    fill = resolve_color_elem(elem.find(".//p:spPr/a:solidFill", NS), theme_colors)
    line = resolve_color_elem(elem.find(".//p:spPr/a:ln/a:solidFill", NS), theme_colors)
    if fill:
        style["fill"] = fill
    if line:
        style["line"] = line
    prst = elem.find(".//p:spPr/a:prstGeom", NS)
    if prst is not None and prst.attrib.get("prst"):
        style["shapeType"] = prst.attrib["prst"]
    text_style = extract_placeholder_text_style(elem)
    if text_style:
        style["textStyle"] = text_style
    return style


def extract_pic_asset(elem: ET.Element, rels: dict[str, dict[str, str]], copied_assets: dict[str, str]) -> str | None:
    blip = elem.find(".//a:blip", NS)
    if blip is None:
        return None
    rel_id = blip.attrib.get(f"{{{NS['r']}}}embed")
    if not rel_id:
        return None
    rel = rels.get(rel_id)
    if not rel or rel["type"] != IMAGE_REL:
        return None
    return copied_assets.get(rel["target"], PurePosixPath(rel["target"]).name)


def extract_slide_editable_elements(
    root: ET.Element | None,
    rels: dict[str, dict[str, str]],
    copied_assets: dict[str, str],
    theme_colors: dict[str, str],
    limit: int = 60,
) -> list[dict[str, Any]]:
    """Return only elements authored on the normal slide canvas.

    The caller passes only the slide XML root, never layout or master roots, so
    this list excludes locked inherited decoration by construction.
    """
    if root is None:
        return []
    sp_tree = root.find("p:cSld/p:spTree", NS)
    if sp_tree is None:
        return []

    elements: list[dict[str, Any]] = []
    for z_order, child in enumerate(list(sp_tree), start=1):
        tag = local_name(child)
        if tag in {"nvGrpSpPr", "grpSpPr"}:
            continue
        geometry = parse_element_xfrm_record(child)
        if geometry is None:
            continue

        record: dict[str, Any] = {
            "source": "slide",
            "editable": True,
            "zOrder": z_order,
            "geometry": geometry,
        }
        c_nv_pr = child.find(".//p:cNvPr", NS)
        if c_nv_pr is not None:
            if c_nv_pr.attrib.get("name"):
                record["name"] = c_nv_pr.attrib["name"]
            if c_nv_pr.attrib.get("id"):
                record["id"] = c_nv_pr.attrib["id"]

        if tag == "sp":
            texts = extract_text_samples(child, limit=8)
            ph = child.find("p:nvSpPr/p:nvPr/p:ph", NS)
            record["kind"] = "text_box" if texts else "shape"
            if texts:
                record["textSamples"] = texts
                record["textPreview"] = " ".join(texts)[:180]
            if ph is not None:
                record["placeholder"] = {
                    "type": ph.attrib.get("type"),
                    "idx": ph.attrib.get("idx"),
                    "size": ph.attrib.get("sz"),
                    "orient": ph.attrib.get("orient"),
                }
            style = extract_shape_style(child, theme_colors)
            if style:
                record["style"] = style
        elif tag == "pic":
            record["kind"] = "picture"
            asset = extract_pic_asset(child, rels, copied_assets)
            if asset:
                record["asset"] = asset
        elif tag == "graphicFrame":
            record["kind"] = "graphic_frame"
        elif tag == "grpSp":
            record["kind"] = "group"
        else:
            record["kind"] = tag or "unknown"

        record["role"] = infer_element_role(record)
        if has_unused_placeholder_text(record.get("textSamples", [])):
            record["unusedPlaceholder"] = True
        elements.append(record)
        if len(elements) >= limit:
            break
    return elements
def extract_text_samples(root: ET.Element | None, limit: int = 6) -> list[str]:
    if root is None:
        return []
    samples: list[str] = []
    for node in root.findall(".//a:t", NS):
        text = (node.text or "").strip()
        if not text:
            continue
        samples.append(text)
        if len(samples) >= limit:
            break
    return samples


def extract_image_targets(root: ET.Element | None, rels: dict[str, dict[str, str]]) -> list[str]:
    if root is None:
        return []
    targets: list[str] = []
    seen: set[str] = set()
    for blip in root.findall(".//a:blip", NS):
        rel_id = blip.attrib.get(f"{{{NS['r']}}}embed")
        if not rel_id:
            continue
        rel = rels.get(rel_id)
        if not rel or rel["type"] != IMAGE_REL:
            continue
        target = rel["target"]
        if target in seen:
            continue
        seen.add(target)
        targets.append(target)
    return targets


def detect_background_asset(root: ET.Element | None, rels: dict[str, dict[str, str]]) -> str | None:
    if root is None:
        return None

    bg = root.find("p:cSld/p:bg", NS)
    if bg is None:
        bg = root.find("p:bg", NS)
    if bg is None:
        return None

    blip = bg.find(".//a:blip", NS)
    if blip is None:
        return None

    rel_id = blip.attrib.get(f"{{{NS['r']}}}embed")
    if not rel_id:
        return None
    rel = rels.get(rel_id)
    if not rel or rel["type"] != IMAGE_REL:
        return None
    return rel["target"]


def count_slide_shapes(root: ET.Element | None) -> int:
    if root is None:
        return 0
    sp_tree = root.find("p:cSld/p:spTree", NS)
    if sp_tree is None:
        return 0
    return len(list(sp_tree))


def classify_slide(index: int, total: int, texts: list[str], image_count: int, shape_count: int) -> str:
    joined = " ".join(texts).lower()
    if any(keyword in joined for keyword in THANKS_KEYWORDS):
        return "ending_candidate"
    if any(keyword in joined for keyword in TOC_KEYWORDS):
        return "toc_candidate"
    if any(keyword in joined for keyword in CHAPTER_KEYWORDS):
        return "chapter_candidate"
    if index == 1 and image_count <= 3:
        return "cover_candidate"
    if index == total and len(texts) <= 6:
        return "ending_candidate"
    if len(texts) <= 3 and shape_count <= 12:
        return "chapter_candidate"
    return "content_candidate"


def parse_theme(root: ET.Element | None) -> dict[str, Any]:
    if root is None:
        return {"colors": {}, "fonts": {}}

    colors: dict[str, str] = {}
    clr_scheme = root.find(".//a:clrScheme", NS)
    if clr_scheme is not None:
        for child in list(clr_scheme):
            if not isinstance(child.tag, str):
                continue
            name = child.tag.split("}", 1)[-1]
            srgb = child.find("a:srgbClr", NS)
            sys_clr = child.find("a:sysClr", NS)
            if srgb is not None and "val" in srgb.attrib:
                colors[name] = normalize_hex(f"#{srgb.attrib['val']}")
            elif sys_clr is not None:
                last = sys_clr.attrib.get("lastClr")
                if last:
                    colors[name] = normalize_hex(f"#{last}")

    fonts: dict[str, str] = {}
    font_scheme = root.find(".//a:fontScheme", NS)
    if font_scheme is not None:
        major = font_scheme.find("a:majorFont", NS)
        minor = font_scheme.find("a:minorFont", NS)
        if major is not None:
            latin = major.find("a:latin", NS)
            if latin is not None and latin.attrib.get("typeface"):
                fonts["majorLatin"] = latin.attrib["typeface"]
        if minor is not None:
            latin = minor.find("a:latin", NS)
            if latin is not None and latin.attrib.get("typeface"):
                fonts["minorLatin"] = latin.attrib["typeface"]
            ea = minor.find("a:ea", NS)
            if ea is not None and ea.attrib.get("typeface"):
                fonts["minorEastAsia"] = ea.attrib["typeface"]

    return {"colors": colors, "fonts": fonts}


def normalize_hex(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip().lstrip("#").upper()
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if not re.fullmatch(r"[0-9A-F]{6}", value):
        return ""
    return f"#{value}"


def _apply_lum_transform(hex_color: str, elem: ET.Element) -> str:
    """Apply common OOXML luminance transforms to an RGB color."""
    color = normalize_hex(hex_color)
    if not color:
        return ""
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)

    lum_mod = elem.find("a:lumMod", NS)
    lum_off = elem.find("a:lumOff", NS)
    mod = 1.0
    off = 0.0
    if lum_mod is not None:
        try:
            mod = int(lum_mod.attrib.get("val", "100000")) / 100000.0
        except ValueError:
            pass
    if lum_off is not None:
        try:
            off = int(lum_off.attrib.get("val", "0")) / 100000.0
        except ValueError:
            pass

    def channel(v: int) -> int:
        return max(0, min(255, round(v * mod + 255 * off)))

    return f"#{channel(r):02X}{channel(g):02X}{channel(b):02X}"


def resolve_color_elem(elem: ET.Element | None, theme_colors: dict[str, str]) -> str:
    if elem is None:
        return ""
    srgb = elem.find("a:srgbClr", NS)
    if srgb is not None and srgb.attrib.get("val"):
        return _apply_lum_transform(f"#{srgb.attrib['val']}", srgb)
    scheme = elem.find("a:schemeClr", NS)
    if scheme is not None and scheme.attrib.get("val"):
        base = theme_colors.get(scheme.attrib["val"], "")
        return _apply_lum_transform(base, scheme)
    sys_clr = elem.find("a:sysClr", NS)
    if sys_clr is not None and sys_clr.attrib.get("lastClr"):
        return _apply_lum_transform(f"#{sys_clr.attrib['lastClr']}", sys_clr)
    return ""


def extract_color_usage(root: ET.Element | None, theme_colors: dict[str, str]) -> Counter[str]:
    usage: Counter[str] = Counter()
    if root is None:
        return usage
    for fill in root.findall(".//a:solidFill", NS):
        color = resolve_color_elem(fill, theme_colors)
        if color:
            usage[color] += 1
    for ln in root.findall(".//a:ln", NS):
        fill = ln.find("a:solidFill", NS)
        color = resolve_color_elem(fill, theme_colors)
        if color:
            usage[color] += 1
    return usage


def top_palette(color_usage: Counter[str], theme_colors: dict[str, str]) -> list[dict[str, Any]]:
    combined = Counter()
    combined.update({normalize_hex(k): 1 for k in theme_colors.values() if normalize_hex(k)})
    combined.update(color_usage)
    neutral = {"#FFFFFF", "#000000", "#F2F2F2", "#F5F5F5", "#FAFAFA"}
    rows = []
    for color, count in combined.most_common():
        if not color or color in neutral:
            continue
        rows.append({"hex": color, "count": int(count)})
        if len(rows) >= 10:
            break
    return rows


def extract_identity_candidates(slides: list[SlideRecord], common_assets: list[str]) -> dict[str, Any]:
    texts = []
    for slide in slides:
        texts.extend(slide.text_samples)
    joined = "\n".join(texts)
    orgs = sorted({m.group(1).strip() for m in IDENTITY_ORG_RE.finditer(joined)})
    depts = sorted({m.group(1).strip() for m in IDENTITY_DEPT_RE.finditer(joined)})
    logo_assets = [
        asset for asset in common_assets
        if re.search(r"(logo|emblem|badge|seal|mark|school|univ)", asset, re.IGNORECASE)
    ]
    if not logo_assets:
        logo_assets = common_assets[:3]
    return {
        "organizationNames": orgs[:8],
        "departmentNames": depts[:8],
        "logoAssetCandidates": logo_assets[:8],
    }


def choose_common_assets(asset_usage: Counter[str]) -> list[str]:
    common = [asset for asset, count in asset_usage.items() if count > 1]
    return sorted(common)




def rect_area(rect: dict[str, Any] | None) -> float:
    if not rect:
        return 0.0
    return max(0.0, float(rect.get("width", 0))) * max(0.0, float(rect.get("height", 0)))


def normalize_rect(rect: dict[str, Any] | None, slide_size: dict[str, Any] | None = None) -> dict[str, int] | None:
    if not rect:
        return None
    try:
        x = int(round(float(rect.get("x", 0))))
        y = int(round(float(rect.get("y", 0))))
        w = int(round(float(rect.get("width", 0))))
        h = int(round(float(rect.get("height", 0))))
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    if slide_size:
        max_w = int(slide_size.get("width_px") or 0)
        max_h = int(slide_size.get("height_px") or 0)
        if max_w > 0 and max_h > 0:
            x2 = min(max_w, x + w)
            y2 = min(max_h, y + h)
            x = max(0, x)
            y = max(0, y)
            w = max(0, x2 - x)
            h = max(0, y2 - y)
            if w <= 0 or h <= 0:
                return None
    return {"x": x, "y": y, "width": w, "height": h}


def union_rect(rects: list[dict[str, Any]], slide_size: dict[str, Any] | None = None) -> dict[str, int] | None:
    normalized = [rect for rect in (normalize_rect(item, slide_size) for item in rects) if rect]
    if not normalized:
        return None
    x1 = min(rect["x"] for rect in normalized)
    y1 = min(rect["y"] for rect in normalized)
    x2 = max(rect["x"] + rect["width"] for rect in normalized)
    y2 = max(rect["y"] + rect["height"] for rect in normalized)
    return normalize_rect({"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1}, slide_size)


def inset_rect(rect: dict[str, Any], inset: int, slide_size: dict[str, Any] | None = None) -> dict[str, int] | None:
    return normalize_rect(
        {
            "x": float(rect.get("x", 0)) + inset,
            "y": float(rect.get("y", 0)) + inset,
            "width": float(rect.get("width", 0)) - inset * 2,
            "height": float(rect.get("height", 0)) - inset * 2,
        },
        slide_size,
    )


def bottom_edge(rect: dict[str, Any] | None) -> float:
    if not rect:
        return 0.0
    return float(rect.get("y", 0)) + float(rect.get("height", 0))


def right_edge(rect: dict[str, Any] | None) -> float:
    if not rect:
        return 0.0
    return float(rect.get("x", 0)) + float(rect.get("width", 0))


def overlap_area(a: dict[str, Any] | None, b: dict[str, Any] | None) -> float:
    if not a or not b:
        return 0.0
    ax1, ay1 = float(a.get("x", 0)), float(a.get("y", 0))
    ax2 = ax1 + float(a.get("width", 0))
    ay2 = ay1 + float(a.get("height", 0))
    bx1, by1 = float(b.get("x", 0)), float(b.get("y", 0))
    bx2 = bx1 + float(b.get("width", 0))
    by2 = by1 + float(b.get("height", 0))
    width = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    height = max(0.0, min(ay2, by2) - max(ay1, by1))
    return width * height


def overlap_ratios(a: dict[str, Any], b: dict[str, Any]) -> tuple[float, float, float]:
    overlap = overlap_area(a.get("geometry"), b.get("geometry"))
    a_area = rect_area(a.get("geometry"))
    b_area = rect_area(b.get("geometry"))
    min_area = min(a_area, b_area) if a_area and b_area else 0.0
    return (
        overlap / a_area if a_area else 0.0,
        overlap / b_area if b_area else 0.0,
        overlap / min_area if min_area else 0.0,
    )


def has_unused_placeholder_text(texts: list[str] | tuple[str, ...] | None) -> bool:
    joined = " ".join(texts or []).strip().lower()
    return any(pattern.lower() in joined for pattern in UNUSED_PLACEHOLDER_PATTERNS)


def placeholder_role(ph: dict[str, Any] | None) -> str:
    if not ph:
        return ""
    ph_type = ph.get("type")
    if ph_type in PAGE_NUMBER_PLACEHOLDER_TYPES:
        return "page_number"
    if ph_type in TITLE_PLACEHOLDER_TYPES:
        return "title"
    if ph_type in BODY_PLACEHOLDER_TYPES:
        return "body"
    if ph_type in PICTURE_PLACEHOLDER_TYPES:
        return "picture"
    if ph_type in FOOTER_PLACEHOLDER_TYPES:
        return "footer"
    return str(ph_type or "placeholder")


def infer_element_role(record: dict[str, Any]) -> str:
    ph_role = placeholder_role(record.get("placeholder"))
    if ph_role:
        return ph_role
    name = str(record.get("name", "")).lower()
    texts = " ".join(record.get("textSamples", []) or [])
    text_l = texts.lower()
    if "logo" in name or "emblem" in name or "seal" in name:
        return "logo"
    if record.get("kind") == "picture" and re.search(r"(logo|emblem|seal|badge|school|univ)", name, re.I):
        return "logo"
    if IDENTITY_ORG_RE.search(texts):
        return "institution_name"
    if IDENTITY_DEPT_RE.search(texts):
        return "department_name"
    if record.get("kind") == "text_box" and re.search(r"(footer|citation|reference|doi|et al\.|journal)", text_l):
        return "footer"
    if record.get("kind") == "text_box":
        return "fixed_text" if record.get("editable") is False else "text"
    if record.get("kind") == "picture":
        return "picture"
    return "decorative_shape" if record.get("kind") == "shape" else str(record.get("kind", "unknown"))


def is_solid_shape(record: dict[str, Any]) -> bool:
    if record.get("kind") != "shape":
        return False
    style = record.get("style") or {}
    return bool(style.get("fill")) and not record.get("textSamples")


def allowed_overlap(a: dict[str, Any], b: dict[str, Any], ratios: tuple[float, float, float]) -> tuple[bool, str]:
    a_role = a.get("role") or infer_element_role(a)
    b_role = b.get("role") or infer_element_role(b)
    a_text = a.get("kind") == "text_box"
    b_text = b.get("kind") == "text_box"
    if a.get("unusedPlaceholder") or b.get("unusedPlaceholder"):
        return False, "unused_placeholder_must_be_removed"
    if a_role in PROTECTED_ROLES or b_role in PROTECTED_ROLES:
        return False, "protected_region_collision"
    if is_solid_shape(a) and b_text and ratios[1] >= 0.65:
        return True, "solid_shape_backplate_for_text"
    if is_solid_shape(b) and a_text and ratios[0] >= 0.65:
        return True, "solid_shape_backplate_for_text"
    if a_text and b_text:
        return False, "text_box_collision"
    if {a_role, b_role} & {"title", "page_number", "footer", "logo", "institution_name", "department_name"}:
        return False, "reserved_region_collision"
    return False, "independent_element_collision"


def build_overlap_audit(
    editable_elements: list[dict[str, Any]],
    protected_elements: list[dict[str, Any]] | None = None,
    min_ratio: float = 0.04,
) -> dict[str, Any]:
    elements = list(editable_elements or []) + list(protected_elements or [])
    allowed: list[dict[str, Any]] = []
    forbidden: list[dict[str, Any]] = []
    unused = [e for e in elements if e.get("unusedPlaceholder")]
    for i, left in enumerate(elements):
        for right in elements[i + 1:]:
            ratios = overlap_ratios(left, right)
            if max(ratios) < min_ratio:
                continue
            ok, reason = allowed_overlap(left, right, ratios)
            row = {
                "left": left.get("name") or left.get("role") or left.get("kind"),
                "right": right.get("name") or right.get("role") or right.get("kind"),
                "leftRole": left.get("role") or infer_element_role(left),
                "rightRole": right.get("role") or infer_element_role(right),
                "overlapRatioLeft": round(ratios[0], 4),
                "overlapRatioRight": round(ratios[1], 4),
                "overlapRatioMin": round(ratios[2], 4),
                "reason": reason,
            }
            if ok:
                allowed.append(row)
            else:
                forbidden.append(row)
    return {
        "status": "fail" if forbidden or unused else "pass",
        "allowedOverlaps": allowed,
        "forbiddenOverlaps": forbidden,
        "unusedPlaceholderElements": [
            {
                "name": e.get("name"),
                "role": e.get("role") or infer_element_role(e),
                "textPreview": e.get("textPreview"),
                "geometry": e.get("geometry"),
            }
            for e in unused
        ],
    }


def extract_fixed_elements(
    root: ET.Element | None,
    rels: dict[str, dict[str, str]],
    copied_assets: dict[str, str],
    theme_colors: dict[str, str],
    source: str,
    limit: int = 80,
) -> list[dict[str, Any]]:
    if root is None:
        return []
    sp_tree = root.find("p:cSld/p:spTree", NS)
    if sp_tree is None:
        return []
    elements: list[dict[str, Any]] = []
    for z_order, child in enumerate(list(sp_tree), start=1):
        tag = local_name(child)
        if tag in {"nvGrpSpPr", "grpSpPr"} or child.find(".//p:ph", NS) is not None:
            continue
        geometry = parse_element_xfrm_record(child)
        if geometry is None:
            continue
        record: dict[str, Any] = {"source": source, "editable": False, "zOrder": z_order, "geometry": geometry}
        c_nv_pr = child.find(".//p:cNvPr", NS)
        if c_nv_pr is not None:
            if c_nv_pr.attrib.get("name"):
                record["name"] = c_nv_pr.attrib["name"]
            if c_nv_pr.attrib.get("id"):
                record["id"] = c_nv_pr.attrib["id"]
        if tag == "sp":
            texts = extract_text_samples(child, limit=8)
            record["kind"] = "text_box" if texts else "shape"
            if texts:
                record["textSamples"] = texts
                record["textPreview"] = " ".join(texts)[:180]
            style = extract_shape_style(child, theme_colors)
            if style:
                record["style"] = style
        elif tag == "pic":
            record["kind"] = "picture"
            asset = extract_pic_asset(child, rels, copied_assets)
            if asset:
                record["asset"] = asset
        else:
            record["kind"] = tag or "unknown"
        record["role"] = infer_element_role(record)
        if record["role"] in PROTECTED_ROLES or record.get("kind") in {"picture", "text_box"}:
            elements.append(record)
        if len(elements) >= limit:
            break
    return elements


def build_layout_profile(placeholders: list[dict[str, Any]], protected_elements: list[dict[str, Any]]) -> dict[str, Any]:
    slots = []
    counts: Counter[str] = Counter()
    for idx, ph in enumerate(placeholders or []):
        role = placeholder_role(ph)
        if role:
            counts[role] += 1
        slots.append({
            "slotId": f"{role or 'placeholder'}:{idx}",
            "role": role or "placeholder",
            "type": ph.get("type"),
            "idx": ph.get("idx"),
            "geometry": ph.get("geometry"),
            "textStyle": ph.get("textStyle"),
        })
    if counts.get("picture") or counts.get("body") >= 2:
        layout_kind = "multi_content"
    elif counts.get("body") or counts.get("picture"):
        layout_kind = "title_content"
    elif counts.get("title") and sum(counts.values()) <= 2:
        layout_kind = "title_only"
    else:
        layout_kind = "free_or_decorative"
    return {
        "layoutKind": layout_kind,
        "slotCounts": dict(counts),
        "usableSlots": slots,
        "protectedRegions": [
            {"role": e.get("role"), "name": e.get("name"), "geometry": e.get("geometry"), "textPreview": e.get("textPreview")}
            for e in protected_elements or []
            if e.get("role") in PROTECTED_ROLES
        ],
    }


def _slot_from_placeholder(ph: dict[str, Any], source: str, idx: int) -> dict[str, Any] | None:
    role = placeholder_role(ph)
    if not role:
        return None
    return {"source": source, "slotId": f"{source}:{role}:{idx}", "role": role, "type": ph.get("type"), "idx": ph.get("idx"), "geometry": ph.get("geometry"), "textStyle": ph.get("textStyle")}


def resolve_page_number_slot(slide: SlideRecord, layout_by_path: dict[str, dict[str, Any]], master_by_path: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    sources = [
        ("slide", slide.placeholders),
        ("layout", (layout_by_path.get(slide.layout_path or "") or {}).get("placeholders", [])),
        ("master", (master_by_path.get(slide.master_path or "") or {}).get("placeholders", [])),
    ]
    for source, placeholders in sources:
        for idx, ph in enumerate(placeholders or []):
            if ph.get("type") in PAGE_NUMBER_PLACEHOLDER_TYPES:
                return _slot_from_placeholder(ph, source, idx)
    return None


def inherited_protected_elements(slide: SlideRecord, layout_by_path: dict[str, dict[str, Any]], master_by_path: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    protected: list[dict[str, Any]] = []
    master = master_by_path.get(slide.master_path or "")
    layout = layout_by_path.get(slide.layout_path or "")
    if master:
        protected.extend(master.get("protectedElements", []))
    if layout:
        protected.extend(layout.get("protectedElements", []))
    return protected


def build_editable_content_region(
    slide: SlideRecord,
    layout_by_path: dict[str, dict[str, Any]],
    master_by_path: dict[str, dict[str, Any]],
    slide_size: dict[str, Any],
) -> dict[str, Any]:
    """Derive the real insertion rectangle for generated content.

    User PPTX templates often reserve school name, logo, footer, and page-number
    zones in master/layout parts. Downstream generation should not draw into
    those areas. Prefer real content placeholders when available; otherwise
    derive a conservative canvas region from the protected regions.
    """
    protected = inherited_protected_elements(slide, layout_by_path, master_by_path)
    binding_slots: list[dict[str, Any]] = []
    layout = layout_by_path.get(slide.layout_path or "") or {}
    master = master_by_path.get(slide.master_path or "") or {}
    for source, placeholders in (
        ("slide", slide.placeholders),
        ("layout", layout.get("placeholders", [])),
        ("master", master.get("placeholders", [])),
    ):
        for idx, ph in enumerate(placeholders or []):
            slot = _slot_from_placeholder(ph, source, idx)
            if slot and slot.get("geometry"):
                binding_slots.append(slot)

    content_slots = [
        slot for slot in binding_slots
        if slot.get("role") in CONTENT_SLOT_ROLES and normalize_rect(slot.get("geometry"), slide_size)
    ]
    title_slots = [
        slot for slot in binding_slots
        if slot.get("role") in TITLE_SLOT_ROLES and normalize_rect(slot.get("geometry"), slide_size)
    ]

    available_regions: list[dict[str, Any]] = []
    for slot in content_slots:
        rect = inset_rect(slot["geometry"], 6, slide_size)
        if rect:
            available_regions.append({
                "source": slot["source"],
                "slotId": slot["slotId"],
                "role": slot["role"],
                "geometry": rect,
                "textStyle": slot.get("textStyle"),
            })

    if available_regions:
        primary = max(available_regions, key=lambda item: rect_area(item.get("geometry")))
        source = "placeholder_slots"
    else:
        width = int(slide_size.get("width_px") or 1280)
        height = int(slide_size.get("height_px") or 720)
        top_limit = DEFAULT_TITLE_ZONE
        bottom_limit = height - DEFAULT_FOOTER_ZONE
        for slot in title_slots:
            top_limit = max(top_limit, int(bottom_edge(slot.get("geometry"))) + 18)
        for item in protected:
            role = item.get("role")
            geom = normalize_rect(item.get("geometry"), slide_size)
            if not geom:
                continue
            if role in {"logo", "institution_name", "department_name"} and geom["y"] < height * 0.25:
                top_limit = max(top_limit, geom["y"] + geom["height"] + 18)
            if role in FOOTER_RESERVED_ROLES or geom["y"] > height * 0.78:
                bottom_limit = min(bottom_limit, geom["y"] - 18)
        fallback = normalize_rect(
            {
                "x": DEFAULT_CONTENT_MARGIN,
                "y": max(DEFAULT_CONTENT_MARGIN, top_limit),
                "width": width - DEFAULT_CONTENT_MARGIN * 2,
                "height": max(120, bottom_limit - max(DEFAULT_CONTENT_MARGIN, top_limit)),
            },
            slide_size,
        )
        primary = {
            "source": "derived_canvas_minus_protected_regions",
            "slotId": None,
            "role": "content",
            "geometry": fallback,
        }
        available_regions = [primary] if fallback else []
        source = "derived_canvas_minus_protected_regions"

    forbidden_regions = [
        {"role": item.get("role"), "name": item.get("name"), "geometry": normalize_rect(item.get("geometry"), slide_size), "textPreview": item.get("textPreview")}
        for item in protected
        if item.get("role") in PROTECTED_ROLES and normalize_rect(item.get("geometry"), slide_size)
    ]
    title_region = union_rect([slot["geometry"] for slot in title_slots], slide_size)
    footer_candidates = [
        item.get("geometry") for item in protected
        if item.get("role") in FOOTER_RESERVED_ROLES and item.get("geometry")
    ]
    footer_region = union_rect(footer_candidates, slide_size)
    primary_geometry = primary.get("geometry") if isinstance(primary, dict) else None
    return {
        "source": source,
        "primary": primary_geometry,
        "availableRegions": available_regions,
        "titleRegion": title_region,
        "footerRegion": footer_region,
        "forbiddenRegions": forbidden_regions,
        "rules": [
            "Fill availableRegions first; do not draw generated content outside primary unless another listed region is selected.",
            "Generated titles must stay in titleRegion or the title placeholder and must not overlap logo, institution_name, or department_name.",
            "Generated citations, bottom banners, and page numbers must stay in footerRegion or the explicit pageNumberSlot.",
        ],
    }


def build_template_binding(slide: SlideRecord, layout_by_path: dict[str, dict[str, Any]], master_by_path: dict[str, dict[str, Any]], slide_size: dict[str, Any] | None = None) -> dict[str, Any]:
    layout = layout_by_path.get(slide.layout_path or "") or {}
    master = master_by_path.get(slide.master_path or "") or {}
    binding = {
        "layoutPath": slide.layout_path,
        "masterPath": slide.master_path,
        "layoutKind": (layout.get("layoutProfile") or {}).get("layoutKind"),
        "usableSlots": (layout.get("layoutProfile") or {}).get("usableSlots", []),
        "protectedRegions": list((master.get("layoutProfile") or {}).get("protectedRegions", [])) + list((layout.get("layoutProfile") or {}).get("protectedRegions", [])),
        "pageNumberSlot": resolve_page_number_slot(slide, layout_by_path, master_by_path),
    }
    if slide_size:
        binding["editableContentRegion"] = build_editable_content_region(slide, layout_by_path, master_by_path, slide_size)
    return binding

def write_summary(output_path: Path, manifest: dict[str, Any]) -> None:
    """Render a short human digest derived from manifest.json.

    This intentionally stays terse: every fact already lives in manifest.json.
    The digest exists only so a reviewer can scan the workspace at a glance
    without parsing JSON.
    """
    source_name = manifest["source"]["name"]
    slide_size = manifest["slideSize"]
    theme = manifest["theme"]
    slides = manifest["slides"]
    layouts = manifest.get("layouts", [])
    masters = manifest.get("masters", [])
    common_assets = manifest["assets"]["commonAssets"]
    page_type_map = manifest.get("pageTypeCandidates", {})
    palette = manifest.get("palette", [])
    identity = manifest.get("identityCandidates", {})
    import_policy = manifest.get("importPolicy", {})

    lines: list[str] = [
        f"# Template Import Summary — {source_name}",
        "",
        "All facts are stored in `manifest.json`; this digest is for quick scanning only.",
        "",
        "## Canvas",
        f"- Size: {slide_size['width_px']} × {slide_size['height_px']} px",
        f"- Theme colors: {', '.join(sorted(theme['colors'].keys())) or 'none detected'}",
        f"- Theme fonts: {', '.join(f'{k}={v}' for k, v in theme['fonts'].items()) or 'none detected'}",
        f"- Dominant RGB palette: {', '.join(item['hex'] for item in palette[:6]) or 'none detected'}",
        f"- Organization candidates: {', '.join(identity.get('organizationNames', [])) or 'none detected'}",
        f"- Department candidates: {', '.join(identity.get('departmentNames', [])) or 'none detected'}",
        f"- Logo asset candidates: {', '.join(identity.get('logoAssetCandidates', [])) or 'none detected'}",
        "",
        "## Inventory",
        f"- Slides: {len(slides)}",
        f"- Layouts (unique): {len(layouts)}",
        f"- Masters (unique): {len(masters)}",
        f"- Reusable assets (used by ≥2 parts): {len(common_assets)}",
        "",
        "## Page-Type Candidates",
    ]
    if page_type_map:
        for ptype, indexes in page_type_map.items():
            lines.append(f"- {ptype}: slides {', '.join(str(i) for i in indexes)}")
    else:
        lines.append("- (none classified)")

    lines.extend(["", "## Layout Reuse"])
    if layouts:
        for layout in layouts:
            users = layout.get("usedBySlides", [])
            users_str = ", ".join(str(i) for i in users) if users else "n/a"
            lines.append(f"- {layout['name']} → slides {users_str}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Master Reuse"])
    if masters:
        for master in masters:
            users = master.get("usedBySlides", [])
            users_str = ", ".join(str(i) for i in users) if users else "n/a"
            lines.append(f"- {master['name']} → slides {users_str}")
    else:
        lines.append("- (none)")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_manifest(pptx_path: Path, output_dir: Path) -> dict[str, Any]:
    with zipfile.ZipFile(pptx_path, "r") as zf:
        presentation_root = load_xml_from_zip(zf, "ppt/presentation.xml")
        if presentation_root is None:
            raise RuntimeError("Invalid PPTX: missing ppt/presentation.xml")

        slide_size = {"width_emu": 0, "height_emu": 0, "width_px": 0, "height_px": 0}
        sld_sz = presentation_root.find("p:sldSz", NS)
        if sld_sz is not None:
            width_emu = int(sld_sz.attrib.get("cx", "0"))
            height_emu = int(sld_sz.attrib.get("cy", "0"))
            slide_size = {
                "width_emu": width_emu,
                "height_emu": height_emu,
                "width_px": emu_to_pixels(width_emu),
                "height_px": emu_to_pixels(height_emu),
            }

        presentation_rels = parse_relationships(zf, "ppt/presentation.xml")
        slide_parts: list[str] = []
        for sld_id in presentation_root.findall("p:sldIdLst/p:sldId", NS):
            rel_id = sld_id.attrib.get(f"{{{NS['r']}}}id")
            rel = presentation_rels.get(rel_id or "")
            if rel and rel["type"] == SLIDE_REL:
                slide_parts.append(rel["target"])

        master_parts: list[str] = []
        for master_id in presentation_root.findall("p:sldMasterIdLst/p:sldMasterId", NS):
            rel_id = master_id.attrib.get(f"{{{NS['r']}}}id")
            rel = presentation_rels.get(rel_id or "")
            if rel and rel["type"] == MASTER_REL and rel["target"] not in master_parts:
                master_parts.append(rel["target"])

        master_roots: dict[str, ET.Element | None] = {}
        master_rels_map: dict[str, dict[str, dict[str, str]]] = {}
        master_theme_path: dict[str, str | None] = {}
        layout_parts: list[str] = []
        layout_parent: dict[str, str | None] = {}
        for master_path in master_parts:
            master_root = load_xml_from_zip(zf, master_path)
            master_rels = parse_relationships(zf, master_path)
            master_roots[master_path] = master_root
            master_rels_map[master_path] = master_rels
            master_theme_path[master_path] = resolve_first_rel(master_rels, THEME_REL)
            if master_root is None:
                continue
            for layout_id in master_root.findall("p:sldLayoutIdLst/p:sldLayoutId", NS):
                rel_id = layout_id.attrib.get(f"{{{NS['r']}}}id")
                rel = master_rels.get(rel_id or "")
                if not rel or rel["type"] != LAYOUT_REL:
                    continue
                layout_path = rel["target"]
                if layout_path not in layout_parent:
                    layout_parent[layout_path] = master_path
                    layout_parts.append(layout_path)

        asset_dir = output_dir / "assets"
        if asset_dir.exists():
            shutil.rmtree(asset_dir)
        asset_dir.mkdir(parents=True, exist_ok=True)

        copied_assets: dict[str, str] = {}
        for info in zf.infolist():
            if not info.filename.startswith("ppt/media/") or info.is_dir():
                continue
            original_name = PurePosixPath(info.filename).name
            safe_name = sanitize_filename(original_name)
            destination = asset_dir / safe_name
            stem = destination.stem
            suffix = destination.suffix
            counter = 2
            while destination.exists():
                destination = asset_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            with zf.open(info.filename) as src, open(destination, "wb") as dst:
                shutil.copyfileobj(src, dst)
            copied_assets[info.filename] = destination.name

        slide_records: list[SlideRecord] = []
        asset_usage: Counter[str] = Counter()
        layout_usage: defaultdict[str, list[int]] = defaultdict(list)
        master_usage: defaultdict[str, list[int]] = defaultdict(list)
        layout_cache: dict[str, dict[str, Any]] = {}
        master_cache: dict[str, dict[str, Any]] = {}

        theme_summary = {"colors": {}, "fonts": {}}
        color_usage: Counter[str] = Counter()

        for index, slide_path in enumerate(slide_parts, 1):
            slide_root = load_xml_from_zip(zf, slide_path)
            slide_rels = parse_relationships(zf, slide_path)

            layout_path = None
            for rel in slide_rels.values():
                if rel["type"] == LAYOUT_REL:
                    layout_path = rel["target"]
                    break

            layout_root = load_xml_from_zip(zf, layout_path) if layout_path else None
            layout_rels = parse_relationships(zf, layout_path) if layout_path else {}

            master_path = None
            for rel in layout_rels.values():
                if rel["type"] == MASTER_REL:
                    master_path = rel["target"]
                    break

            master_root = load_xml_from_zip(zf, master_path) if master_path else None
            master_rels = parse_relationships(zf, master_path) if master_path else {}

            theme_path = None
            for rel in master_rels.values():
                if rel["type"] == THEME_REL:
                    theme_path = rel["target"]
                    break
            if theme_path and not theme_summary["colors"] and not theme_summary["fonts"]:
                theme_summary = parse_theme(load_xml_from_zip(zf, theme_path))
            active_theme = parse_theme(load_xml_from_zip(zf, theme_path)) if theme_path else theme_summary
            theme_colors = active_theme.get("colors", {})
            color_usage.update(extract_color_usage(slide_root, theme_colors))
            color_usage.update(extract_color_usage(layout_root, theme_colors))
            color_usage.update(extract_color_usage(master_root, theme_colors))

            bg_asset = None
            bg_source = None
            for label, root, rels in (
                ("slide", slide_root, slide_rels),
                ("layout", layout_root, layout_rels),
                ("master", master_root, master_rels),
            ):
                candidate = detect_background_asset(root, rels)
                if candidate:
                    bg_asset = candidate
                    bg_source = label
                    break

            image_targets = extract_image_targets(slide_root, slide_rels)
            texts = extract_text_samples(slide_root)
            placeholders = extract_placeholders(slide_root)
            editable_elements = extract_slide_editable_elements(
                slide_root,
                slide_rels,
                copied_assets,
                theme_colors,
            )
            shape_count = count_slide_shapes(slide_root)
            page_type = classify_slide(index, len(slide_parts), texts, len(image_targets), shape_count)

            resolved_bg = copied_assets.get(bg_asset, PurePosixPath(bg_asset).name if bg_asset else None)
            resolved_images = [
                copied_assets.get(target, PurePosixPath(target).name)
                for target in image_targets
            ]

            if resolved_bg:
                asset_usage[resolved_bg] += 1
            for asset_name in resolved_images:
                asset_usage[asset_name] += 1

            if layout_path:
                if layout_path not in layout_parent:
                    layout_parent[layout_path] = master_path
                    layout_parts.append(layout_path)
                layout_usage[layout_path].append(index)
                if layout_path not in layout_cache:
                    layout_cache[layout_path] = {
                        "root": layout_root,
                        "rels": layout_rels,
                        "master_path": master_path,
                    }
            if master_path:
                if master_path not in master_parts:
                    master_parts.append(master_path)
                    master_roots[master_path] = master_root
                    master_rels_map[master_path] = master_rels
                    master_theme_path[master_path] = theme_path
                master_usage[master_path].append(index)
                if master_path not in master_cache:
                    master_cache[master_path] = {
                        "root": master_root,
                        "rels": master_rels,
                        "theme_path": theme_path,
                    }

            slide_records.append(
                SlideRecord(
                    index=index,
                    name=PurePosixPath(slide_path).name,
                    slide_path=slide_path,
                    layout_path=layout_path,
                    master_path=master_path,
                    background_asset=resolved_bg,
                    background_source=bg_source,
                    image_assets=resolved_images,
                    text_samples=texts,
                    text_count=len(texts),
                    shape_count=shape_count,
                    page_type=page_type,
                    svg_file=slide_svg_filename(index),
                    flat_svg_file=slide_svg_filename(index),
                    placeholders=placeholders,
                    editable_elements=editable_elements,
                )
            )

        for layout_path in layout_parts:
            if layout_path in layout_cache:
                continue
            layout_root = load_xml_from_zip(zf, layout_path)
            layout_rels = parse_relationships(zf, layout_path)
            layout_cache[layout_path] = {
                "root": layout_root,
                "rels": layout_rels,
                "master_path": layout_parent.get(layout_path),
            }

        for master_path in master_parts:
            if master_path in master_cache:
                continue
            master_cache[master_path] = {
                "root": master_roots.get(master_path),
                "rels": master_rels_map.get(master_path, {}),
                "theme_path": master_theme_path.get(master_path),
            }

        page_type_map: dict[str, list[int]] = defaultdict(list)
        for slide in slide_records:
            page_type_map[slide.page_type].append(slide.index)

        layout_records = [
            summarize_part_record(
                part_path=layout_path,
                root=layout_cache[layout_path]["root"],
                rels=layout_cache[layout_path]["rels"],
                copied_assets=copied_assets,
                used_by_slides=layout_usage[layout_path],
                parent_path=layout_cache[layout_path]["master_path"],
                svg_file=part_svg_filename("layout", seq, layout_path),
            )
            for seq, layout_path in enumerate(layout_parts, start=1)
            if layout_path in layout_cache
        ]
        master_records = [
            summarize_part_record(
                part_path=master_path,
                root=master_cache[master_path]["root"],
                rels=master_cache[master_path]["rels"],
                copied_assets=copied_assets,
                used_by_slides=master_usage[master_path],
                theme_path=master_cache[master_path]["theme_path"],
                svg_file=part_svg_filename("master", seq, master_path),
                theme=parse_theme(load_xml_from_zip(zf, master_cache[master_path]["theme_path"]))
                if master_cache[master_path]["theme_path"] else {"colors": {}, "fonts": {}},
            )
            for seq, master_path in enumerate(master_parts, start=1)
            if master_path in master_cache
        ]
        layouts_top = [item for item in layout_records if item]
        masters_top = [item for item in master_records if item]

        layout_by_path = {item["path"]: item for item in layouts_top}
        master_by_path = {item["path"]: item for item in masters_top}
        asset_usage = Counter()
        for slide in slide_records:
            per_slide_assets: set[str] = set(slide.image_assets)
            if slide.background_asset:
                per_slide_assets.add(slide.background_asset)
            layout_record = layout_by_path.get(slide.layout_path or "")
            if layout_record:
                if layout_record.get("backgroundAsset"):
                    per_slide_assets.add(layout_record["backgroundAsset"])
                per_slide_assets.update(layout_record.get("imageAssets", []))
            master_record = master_by_path.get(slide.master_path or "")
            if master_record:
                if master_record.get("backgroundAsset"):
                    per_slide_assets.add(master_record["backgroundAsset"])
                per_slide_assets.update(master_record.get("imageAssets", []))
            for asset in per_slide_assets:
                if asset:
                    asset_usage[asset] += 1

        common_assets = choose_common_assets(asset_usage)
        if not theme_summary["colors"] and not theme_summary["fonts"] and masters_top:
            theme_summary = masters_top[0].get("theme") or {"colors": {}, "fonts": {}}
        palette = top_palette(color_usage, theme_summary.get("colors", {}))
        identity = extract_identity_candidates(slide_records, common_assets)

        manifest = {
            "source": {
                "pptx": str(pptx_path),
                "name": pptx_path.name,
            },
            "slideSize": slide_size,
            "theme": theme_summary,
            "colorUsage": dict(color_usage.most_common()),
            "palette": palette,
            "identityCandidates": identity,
            "importPolicy": {
                "editableScope": "fill_master_layout_placeholders_and_existing_slide_local_slots",
                "masterLayoutUse": "authoritative_slots_and_protected_regions",
                "fillExistingSlotsOnly": True,
                "allowExtraGeneratedShapes": False,
                "allowExtraGeneratedTextBoxes": False,
                "allowExtraGeneratedImageFrames": False,
                "removeUnusedPlaceholderPrompts": True,
                "doNotDuplicateInheritedFixedElements": True,
                "userTemplateStylePriority": "highest_when_source_is_user_pptx",
                "pageNumberPosition": "follow_slide_layout_master_sldNum_slot",
            },
            "assets": {
                "exportDir": "assets",
                "commonAssets": common_assets,
                "allAssets": sorted(copied_assets.values()),
                "assetMap": copied_assets,
            },
            "pageTypeCandidates": dict(sorted(page_type_map.items())),
            "layouts": layouts_top,
            "masters": masters_top,
            "layoutProfiles": {
                item["name"]: item.get("layoutProfile", {})
                for item in layouts_top
            },
            "slides": [
                {
                    "index": slide.index,
                    "name": slide.name,
                    "svgFile": slide.svg_file,
                    "flatSvgFile": slide.flat_svg_file,
                    "editableElements": slide.editable_elements,
                    "placeholders": slide.placeholders,
                    "templateBinding": build_template_binding(slide, layout_by_path, master_by_path, slide_size),
                    "editableContentRegion": build_editable_content_region(slide, layout_by_path, master_by_path, slide_size),
                    "pageNumberSlot": resolve_page_number_slot(slide, layout_by_path, master_by_path),
                    "overlapAudit": build_overlap_audit(
                        slide.editable_elements,
                        inherited_protected_elements(slide, layout_by_path, master_by_path),
                    ),
                    "unusedPlaceholderElements": [
                        elem for elem in slide.editable_elements
                        if elem.get("unusedPlaceholder")
                    ],
                    "slidePath": slide.slide_path,
                    "layoutPath": slide.layout_path,
                    "masterPath": slide.master_path,
                    "backgroundAsset": slide.background_asset,
                    "backgroundSource": slide.background_source,
                    "imageAssets": slide.image_assets,
                    "textSamples": slide.text_samples,
                    "textCount": slide.text_count,
                    "shapeCount": slide.shape_count,
                    "pageType": slide.page_type,
                }
                for slide in slide_records
            ],
        }

        write_summary(output_dir / "summary.md", manifest)
        return manifest

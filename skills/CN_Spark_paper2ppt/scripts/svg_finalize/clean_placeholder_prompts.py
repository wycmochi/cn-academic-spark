#!/usr/bin/env python3
"""Remove unused PowerPoint placeholder prompts from generated SVG files.

This cleanup is intentionally narrow. It removes visible template residue such
as "Click to edit body text" / "单击此处编辑正文内容" and untouched placeholder guide
groups emitted by the PPTX import path. It does not remove filled placeholder
groups that contain real slide content.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

PROMPT_TEXTS = {
    # English PowerPoint / WPS prompts.
    "Click to edit body text",
    "Click to edit Master title style",
    "Click to edit Master text styles",
    "Click to edit title",
    "Click to edit subtitle",
    "Click to add text",
    "Click to add title",
    "Click to add subtitle",
    "Click to add picture",
    "Click icon to add picture",
    "Click to add chart",
    "Click to add table",
    "Click to add SmartArt Graphic",
    "Click to add media clip",
    "Insert picture",
    "Picture placeholder",
    "Presenter / course name",
    "Presenter/course name",
    # Chinese PowerPoint / WPS prompts.
    "单击此处编辑正文内容",
    "单击此处编辑母版标题样式",
    "单击此处编辑母版文本样式",
    "单击此处编辑主标题",
    "单击此处编辑副标题",
    "单击此处添加标题",
    "单击此处添加副标题",
    "单击此处添加文本",
    "单击图标添加图片",
    "单击此处添加图片",
    "插入图片",
    "插入图片(填充)",
    "图片占位符",
    "演讲者/课程名称",
    "演讲者 / 课程名称",
    "演讲者/课程名",
    "演讲者 / 课程名",
}
PROMPT_TEXTS_NORMALIZED = {" ".join(text.lower().split()) for text in PROMPT_TEXTS}
PROMPT_TEXTS_COMPACT = {re.sub(r"\s+", "", text) for text in PROMPT_TEXTS_NORMALIZED}
PROMPT_PREFIXES_NORMALIZED = (
    "click to edit master ",
    "click to edit subtitle ",
    "click to edit title ",
    "click to edit text ",
)
LEADING_MARK_RE = re.compile(r"^[\s\-\u2013\u2014\u2022\u25cf\u00b7*]+")
GUIDE_LABEL_RE = re.compile(r"^ph(?:\s+[a-z0-9_.:=\-]+)*$", re.IGNORECASE)


def local_name(tag: str) -> str:
    """Return the namespace-free SVG tag name."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def normalize_text(text: str | None) -> str:
    """Collapse whitespace for robust prompt matching."""
    return " ".join((text or "").split()).strip()


def element_text(elem: ET.Element) -> str:
    """Read all descendant text content from an element."""
    return normalize_text("".join(elem.itertext()))


def is_prompt_text(text: str | None) -> bool:
    """Return true when text is a known unused PPT placeholder prompt."""
    normalized = normalize_text(text)
    if not normalized:
        return False
    folded = LEADING_MARK_RE.sub("", normalized.lower()).strip()
    compact = re.sub(r"\s+", "", folded)
    if folded in PROMPT_TEXTS_NORMALIZED or compact in PROMPT_TEXTS_COMPACT:
        return True
    if any(folded.startswith(prefix) for prefix in PROMPT_PREFIXES_NORMALIZED):
        return True

    # Robust Chinese prompt pattern: catches common PPT / WPS variants without
    # deleting real academic text. A real slide sentence almost never combines
    # "单击" with edit/add verbs and placeholder nouns.
    if "单击" in normalized and any(v in normalized for v in ("编辑", "添加", "插入")):
        if any(noun in normalized for noun in ("标题", "副标题", "正文", "文本", "图片", "图表", "表格", "母版")):
            return True
    if "演讲者" in normalized and any(noun in normalized for noun in ("课程", "姓名", "名称", "名字")):
        return True
    if "占位符" in normalized and any(noun in normalized for noun in ("图片", "文本", "标题")):
        return True
    return False


def is_guide_label(text: str | None) -> bool:
    """Detect untouched placeholder guide labels such as 'ph body idx=1'."""
    normalized = normalize_text(text)
    return bool(normalized and GUIDE_LABEL_RE.match(normalized))


def descendant_text_elements(elem: ET.Element) -> list[ET.Element]:
    """Return descendant <text> nodes in document order."""
    return [child for child in elem.iter() if local_name(child.tag) == "text"]


def has_placeholder_guide_rect(elem: ET.Element) -> bool:
    """Detect the dashed rectangles emitted by pptx_to_svg placeholder guides."""
    for child in elem.iter():
        if local_name(child.tag) != "rect":
            continue
        stroke_dash = (child.get("stroke-dasharray") or "").strip()
        fill = (child.get("fill") or "").strip().upper()
        stroke = (child.get("stroke") or "").strip().upper()
        if stroke_dash:
            return True
        if fill == "#F8FAFC" and stroke == "#94A3B8":
            return True
    return False


def texts_are_disposable(elem: ET.Element) -> bool:
    """True when every visible text node is a prompt or guide label."""
    texts = [element_text(text_el) for text_el in descendant_text_elements(elem)]
    texts = [text for text in texts if text]
    return bool(texts) and all(is_prompt_text(text) or is_guide_label(text) for text in texts)


def is_placeholder_guide_group(elem: ET.Element) -> bool:
    """Detect an untouched imported placeholder guide group."""
    if local_name(elem.tag) != "g":
        return False
    if "data-ph-type" not in elem.attrib:
        return False
    return has_placeholder_guide_rect(elem) and texts_are_disposable(elem)


def group_looks_like_shape(elem: ET.Element) -> bool:
    """Return true for SVG groups that correspond to one imported PPT shape."""
    if local_name(elem.tag) != "g":
        return False
    elem_id = elem.get("id") or ""
    name = (elem.get("data-name") or "").lower()
    if "data-ph-type" in elem.attrib:
        return True
    if "shape-" in elem_id:
        return True
    return "placeholder" in name or "占位" in name


def nearest_removable_group(
    elem: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
    root: ET.Element,
) -> ET.Element | None:
    """Find the nearest small shape group that contains only prompt content."""
    cur = parent_map.get(elem)
    while cur is not None and cur is not root:
        if group_looks_like_shape(cur) and texts_are_disposable(cur):
            return cur
        cur = parent_map.get(cur)
    return None


def element_depth(elem: ET.Element, parent_map: dict[ET.Element, ET.Element]) -> int:
    """Depth from root, used only for deterministic removals."""
    depth = 0
    cur = parent_map.get(elem)
    while cur is not None:
        depth += 1
        cur = parent_map.get(cur)
    return depth


def dedupe_targets(
    targets: list[ET.Element],
    parent_map: dict[ET.Element, ET.Element],
) -> list[ET.Element]:
    """Drop child removals when an ancestor is already scheduled."""
    target_set = set(targets)
    deduped: list[ET.Element] = []
    for target in targets:
        cur = parent_map.get(target)
        skip = False
        while cur is not None:
            if cur in target_set:
                skip = True
                break
            cur = parent_map.get(cur)
        if not skip and target not in deduped:
            deduped.append(target)
    return sorted(deduped, key=lambda e: element_depth(e, parent_map), reverse=True)


def prune_empty_groups(root: ET.Element) -> int:
    """Remove groups made empty by prompt cleanup."""
    removed = 0
    while True:
        parent_map = {child: parent for parent in root.iter() for child in list(parent)}
        empty_groups = []
        for elem in list(root.iter()):
            if elem is root or local_name(elem.tag) != "g":
                continue
            if list(elem):
                continue
            if normalize_text(elem.text) or normalize_text(elem.tail):
                continue
            empty_groups.append(elem)
        if not empty_groups:
            return removed
        for elem in empty_groups:
            parent = parent_map.get(elem)
            if parent is not None:
                parent.remove(elem)
                removed += 1


def cleanup_placeholder_prompts_in_svg(
    svg_path: Path,
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> int:
    """Remove unused placeholder prompts/guides from one SVG file."""
    try:
        tree = ET.parse(svg_path)
    except ET.ParseError as exc:
        if verbose:
            print(f"[ERROR] {svg_path}: {exc}")
        return 0

    root = tree.getroot()
    parent_map = {child: parent for parent in root.iter() for child in list(parent)}
    targets: list[ET.Element] = []

    for elem in list(root.iter()):
        if elem is root:
            continue
        if is_placeholder_guide_group(elem):
            targets.append(elem)
            continue
        if local_name(elem.tag) == "text" and is_prompt_text(element_text(elem)):
            group = nearest_removable_group(elem, parent_map, root)
            targets.append(group if group is not None else elem)

    targets = dedupe_targets(targets, parent_map)
    if not targets:
        if verbose:
            print(f"[OK] {svg_path.name}: no placeholder prompts")
        return 0

    if dry_run:
        if verbose:
            print(f"[PREVIEW] {svg_path.name}: would remove {len(targets)} placeholder item(s)")
        return len(targets)

    removed = 0
    for target in targets:
        parent = parent_map.get(target)
        if parent is None:
            continue
        parent.remove(target)
        removed += 1

    removed += prune_empty_groups(root)
    tree.write(svg_path, encoding="unicode", xml_declaration=False)
    if verbose:
        print(f"[OK] {svg_path.name}: removed {removed} placeholder item(s)")
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove unused PPT placeholder prompts from SVG files.")
    parser.add_argument("paths", nargs="+", type=Path, help="SVG file(s) or directories containing SVG files")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-file cleanup results")
    args = parser.parse_args()

    svg_files: list[Path] = []
    for path in args.paths:
        if path.is_dir():
            svg_files.extend(sorted(path.glob("*.svg")))
        else:
            svg_files.append(path)

    total = 0
    for svg_file in svg_files:
        total += cleanup_placeholder_prompts_in_svg(svg_file, dry_run=args.dry_run, verbose=args.verbose)
    print(f"Removed {total} placeholder item(s)" if not args.dry_run else f"Would remove {total} placeholder item(s)")


if __name__ == "__main__":
    main()
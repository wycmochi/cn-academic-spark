#!/usr/bin/env python3
"""Audit user-PPTX template slot usage and overlap risks from manifest.json.

The script is intentionally manifest-based: it does not guess slide design from
screenshots. It reads the factual import result produced by
`template_import/cli.py` and reports:
- forbidden overlaps between editable slide elements and protected master/layout regions;
- allowed overlaps such as solid shape backplates behind text;
- unused PowerPoint placeholder prompts that should be removed before export;
- missing page-number slots when a user template is expected to provide one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    return data


def rect_area(rect: dict[str, Any] | None) -> float:
    if not rect:
        return 0.0
    try:
        return max(0.0, float(rect.get("width", 0))) * max(0.0, float(rect.get("height", 0)))
    except (TypeError, ValueError):
        return 0.0


def overlap_ratio(a: dict[str, Any] | None, b: dict[str, Any] | None) -> float:
    if not a or not b:
        return 0.0
    try:
        ax1, ay1 = float(a.get("x", 0)), float(a.get("y", 0))
        aw, ah = float(a.get("width", 0)), float(a.get("height", 0))
        bx1, by1 = float(b.get("x", 0)), float(b.get("y", 0))
        bw, bh = float(b.get("width", 0)), float(b.get("height", 0))
    except (TypeError, ValueError):
        return 0.0
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh
    overlap = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(0.0, min(ay2, by2) - max(ay1, by1))
    min_area = min(rect_area(a), rect_area(b))
    return overlap / min_area if min_area else 0.0


def page_number_slot_count(slide: dict[str, Any]) -> int:
    seen: set[str] = set()

    def add_slot(slot: dict[str, Any] | None, source: str) -> None:
        if not slot:
            return
        geom = slot.get("geometry") or {}
        key = (
            f"{slot.get('source') or source}:"
            f"{slot.get('type') or slot.get('role')}:"
            f"{slot.get('idx')}:"
            f"{geom.get('x')}:{geom.get('y')}:{geom.get('width')}:{geom.get('height')}"
        )
        seen.add(key)

    for ph in slide.get("placeholders") or []:
        if ph.get("type") == "sldNum":
            add_slot(ph, "slide")
    binding = slide.get("templateBinding") or {}
    for slot in binding.get("usableSlots") or []:
        if slot.get("type") == "sldNum" or slot.get("role") == "page_number":
            add_slot(slot, slot.get("source") or "layout")
    add_slot(binding.get("pageNumberSlot"), "resolved")
    return len(seen)


def audit_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    slides = manifest.get("slides") or []
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    allowed_count = 0

    for slide in slides:
        slide_id = slide.get("index")
        audit = slide.get("overlapAudit") or {}
        forbidden = audit.get("forbiddenOverlaps") or []
        unused = audit.get("unusedPlaceholderElements") or []
        allowed_count += len(audit.get("allowedOverlaps") or [])
        if forbidden:
            failures.append({"slide": slide_id, "type": "forbidden_overlap", "items": forbidden})
        if unused:
            failures.append({"slide": slide_id, "type": "unused_placeholder", "items": unused})
        if not slide.get("pageNumberSlot"):
            warnings.append({"slide": slide_id, "type": "missing_page_number_slot"})
        if page_number_slot_count(slide) > 1:
            failures.append({
                "slide": slide_id,
                "type": "multiple_page_number_slots",
                "items": [slide.get("pageNumberSlot"), (slide.get("templateBinding") or {}).get("usableSlots", [])],
            })
        binding = slide.get("templateBinding") or {}
        if not binding.get("usableSlots"):
            warnings.append({"slide": slide_id, "type": "no_detected_layout_slots"})
        region = slide.get("editableContentRegion") or binding.get("editableContentRegion") or {}
        primary = region.get("primary")
        if not primary:
            failures.append({"slide": slide_id, "type": "missing_editable_content_region", "items": [region]})
        elif rect_area(primary) <= 0:
            failures.append({"slide": slide_id, "type": "invalid_editable_content_region", "items": [primary]})
        for forbidden_region in region.get("forbiddenRegions") or []:
            geom = forbidden_region.get("geometry")
            if overlap_ratio(primary, geom) >= 0.03:
                failures.append({
                    "slide": slide_id,
                    "type": "editable_region_overlaps_protected_region",
                    "items": [{"editable": primary, "protected": forbidden_region}],
                })

    return {
        "status": "fail" if failures else "pass",
        "slideCount": len(slides),
        "failureCount": len(failures),
        "warningCount": len(warnings),
        "allowedOverlapCount": allowed_count,
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PPTX template layout manifest for overlap and placeholder risks.")
    parser.add_argument("manifest", help="Path to manifest.json from template_import/cli.py")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when failures are found")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = load_manifest(manifest_path)
    report = audit_manifest(manifest)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Template layout audit: {report['status']}")
        print(f"Slides: {report['slideCount']}")
        print(f"Failures: {report['failureCount']}")
        print(f"Warnings: {report['warningCount']}")
        print(f"Allowed overlaps: {report['allowedOverlapCount']}")
        for item in report["failures"][:10]:
            print(f"[FAIL] slide {item['slide']}: {item['type']} ({len(item['items'])} item(s))")
        for item in report["warnings"][:10]:
            print(f"[WARN] slide {item['slide']}: {item['type']}")

    if args.strict and report["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

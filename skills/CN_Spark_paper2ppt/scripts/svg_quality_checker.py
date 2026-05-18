#!/usr/bin/env python3
"""
PPT Master - SVG Quality Check Tool

Checks whether SVG files comply with project technical specifications.

Usage:
    python3 scripts/svg_quality_checker.py <svg_file>
    python3 scripts/svg_quality_checker.py <directory>
    python3 scripts/svg_quality_checker.py --all examples
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import re
import base64
import json
import math
import html
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
from xml.etree import ElementTree as ET

try:
    from project_utils import CANVAS_FORMATS
    from error_helper import ErrorHelper
except ImportError:
    print("Warning: Unable to import dependency modules")
    CANVAS_FORMATS = {}
    ErrorHelper = None

try:
    from update_spec import parse_lock as _parse_spec_lock
except ImportError:
    _parse_spec_lock = None  # spec_lock drift check will be skipped

try:
    from svg_to_pptx.animation_config import (
        load_animation_config as _load_animation_config,
        validate_animation_config as _validate_animation_config,
    )
except ImportError:
    _load_animation_config = None
    _validate_animation_config = None



try:
    from svg_finalize.clean_placeholder_prompts import is_prompt_text as _is_ppt_placeholder_prompt
except ImportError:
    _is_ppt_placeholder_prompt = None


HEX_VALUE_RE = re.compile(r"#[0-9A-Fa-f]{3,8}")
POINT_TO_PX = 96.0 / 72.0
TEXT_BOX_SHAPE_INSET_PT = 5.0
TEXT_BOX_SHAPE_INSET_PX = TEXT_BOX_SHAPE_INSET_PT * POINT_TO_PX
TEXT_BOX_CENTER_TOLERANCE_PX = 10.0
TEXT_BOX_OVERLAP_RATIO_LIMIT = 0.03

# Ramp envelope for font-size drift detection.
# From design_spec_reference.md §IV — Font Size Hierarchy: the ramp spans
# from page-number floor (0.5x body) to cover-title ceiling (5.0x body).
# Intermediate px values within this envelope are permitted per
# executor-base.md §2.1 ("Executor may use an intermediate size ... provided
# the size's ratio to body falls within the corresponding role's band"); only
# values outside every band — i.e. outside this envelope — are drift.
RAMP_MIN_RATIO = 0.5
RAMP_MAX_RATIO = 5.0


def _parse_placeholders_fallback(block: str) -> Dict[str, Tuple[str, ...]]:
    """Tiny YAML-free reader for the documented ``placeholders:`` shape.

    Used only when PyYAML is unavailable. Recognized lines (indentation-aware,
    two-space indent assumed):

    .. code-block:: yaml

        placeholders:
          01_cover: ["{{TITLE}}", "{{LOGO}}"]
          03_content: []
          03a_content_two_col:
            - "{{LEFT_TITLE}}"
            - "{{RIGHT_TITLE}}"

    Anything outside this minimal grammar is silently skipped — designers who
    rely on advanced YAML should install pyyaml.
    """
    out: Dict[str, Tuple[str, ...]] = {}
    inline_re = re.compile(
        r"^\s{2}([A-Za-z0-9_]+)\s*:\s*\[(.*)\]\s*$"
    )
    empty_re = re.compile(r"^\s{2}([A-Za-z0-9_]+)\s*:\s*\[\s*\]\s*$")
    block_header_re = re.compile(r"^\s{2}([A-Za-z0-9_]+)\s*:\s*$")
    item_re = re.compile(r'^\s{4}-\s*"?([^"]+)"?\s*$')

    in_section = False
    current_block_key: str | None = None
    current_items: List[str] = []

    def _flush_block() -> None:
        nonlocal current_block_key, current_items
        if current_block_key is not None:
            out[current_block_key] = tuple(current_items)
            current_block_key = None
            current_items = []

    for line in block.splitlines():
        if line.startswith("placeholders:"):
            in_section = True
            continue
        if not in_section:
            continue

        # End of section: dedent to a non-key line.
        if line and not line.startswith(" "):
            _flush_block()
            in_section = False
            continue

        if current_block_key is not None:
            m = item_re.match(line)
            if m:
                value = m.group(1).strip().strip('"').strip("'")
                if value:
                    current_items.append(value)
                continue
            # Block ended.
            _flush_block()

        if empty_re.match(line):
            key = empty_re.match(line).group(1)
            out[key] = ()
            continue

        m = inline_re.match(line)
        if m:
            key, raw = m.group(1), m.group(2)
            items = [p.strip().strip('"').strip("'") for p in raw.split(",")]
            out[key] = tuple(item for item in items if item)
            continue

        m = block_header_re.match(line)
        if m:
            current_block_key = m.group(1)
            current_items = []
            continue

    _flush_block()
    return out


class SVGQualityChecker:
    """SVG quality checker"""

    # Default placeholder convention per page-type prefix. This is a *hint*,
    # not a hard contract: templates may define their own placeholder vocabulary
    # via `placeholders:` in design_spec.md frontmatter (see
    # references/template-designer.md §4). Missing default placeholders surface
    # as warnings, never errors — designers may legitimately swap
    # `{{THANK_YOU}}` for `{{CLOSING_MESSAGE}}`, omit `{{DATE}}` when irrelevant,
    # or build content variants with bespoke slot vocabularies.
    #
    # Variants reuse the parent type's expectation (`03a_content_two_col.svg`
    # is matched by the same `03_content` rules as `03_content.svg`).
    DEFAULT_PLACEHOLDER_CONVENTION = {
        "01_cover": ("{{TITLE}}",),  # only the title is universally expected
        "02_chapter": ("{{CHAPTER_TITLE}}",),
        "02_toc": (),  # TOC layouts vary too widely to assert anything
        "03_content": ("{{PAGE_TITLE}}",),
        "04_ending": (),  # ending pages legitimately use varied vocabularies
    }

    def __init__(self, *, template_mode: bool = False):
        self.template_mode = template_mode
        self.results = []
        self.summary = {
            'total': 0,
            'passed': 0,
            'warnings': 0,
            'errors': 0
        }
        self.issue_types = defaultdict(int)
        # spec_lock drift state (populated only when _parse_spec_lock is available
        # and a spec_lock.md is found near the SVG)
        self._lock_cache: Dict[Path, Dict] = {}
        self._drift_summary: Dict[str, Dict[str, set]] = {
            'colors': defaultdict(set),
            'fonts': defaultdict(set),
            'sizes': defaultdict(set),
        }
        self._lock_seen = False  # True once we locate at least one spec_lock.md
        self._source_manifest_cache: Dict[Path, Dict] = {}
        # Template-mode aggregation (populated by check_directory when
        # template_mode=True). Each entry is (severity, kind, message) where
        # severity is 'error' or 'warning'. Printed in print_summary.
        self._template_issues: List[Tuple[str, str, str]] = []
        self._animation_issues: List[Tuple[str, str]] = []
        self._project_issues: List[Tuple[str, str, str]] = []

    def check_file(self, svg_file: str, expected_format: str = None) -> Dict:
        """
        Check a single SVG file

        Args:
            svg_file: SVG file path
            expected_format: Expected canvas format (e.g., 'ppt169')

        Returns:
            Check result dictionary
        """
        svg_path = Path(svg_file)

        if not svg_path.exists():
            return {
                'file': str(svg_file),
                'exists': False,
                'errors': ['File does not exist'],
                'warnings': [],
                'passed': False
            }

        result = {
            'file': svg_path.name,
            'path': str(svg_path),
            'exists': True,
            'errors': [],
            'warnings': [],
            'info': {},
            'passed': True
        }

        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 0. Check XML well-formedness — every other check assumes the file
            # is valid XML.  Bail early on failure so the regex-based checks
            # below don't produce misleading errors on a broken document.
            if self._check_xml_well_formed(content, result):
                # 1. Check viewBox
                self._check_viewbox(content, result, expected_format)

                # 2. Check forbidden elements
                self._check_forbidden_elements(content, result)

                # 3. Check fonts
                self._check_fonts(content, result)

                # 4. Check width/height consistency with viewBox
                self._check_dimensions(content, result)

                # 5. Check text wrapping methods
                self._check_text_elements(content, result)

                # 5b. Enforce minimum readable font size for PPT body text.
                self._check_minimum_body_font_size(content, result)

                # 6. Check image references (file existence and resolution)
                self._check_image_references(content, svg_path, result)

                # 7. Check formula pages use rendered PNG formula images.
                self._check_formula_png_contract(content, result)

                # 8. Check unused PPT placeholder prompt residue.
                self._check_placeholder_prompt_residue(content, result)

                # 9. Check object-level animation anchor quality.
                self._check_animation_group_ids(content, result)

                # 10. Check block shadow contract.
                self._check_shape_block_shadow_contract(content, result)

                # 11. Check spec_lock drift (colors / font-family / font-size).
                #    Templates do not ship a spec_lock.md, so skip in template
                #    mode to avoid noise.
                if not self.template_mode:
                    self._check_spec_lock_drift(content, svg_path, result)

                # 12. Check web-sourced image attribution. Templates don't carry
                #    image_sources.json; skip in template mode.
                if not self.template_mode:
                    self._check_sourced_image_attribution(content, svg_path, result)

            # Determine pass/fail
            result['passed'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"Failed to read file: {e}")
            result['passed'] = False

        # Update statistics
        self.summary['total'] += 1
        if result['passed']:
            if result['warnings']:
                self.summary['warnings'] += 1
            else:
                self.summary['passed'] += 1
        else:
            self.summary['errors'] += 1

        # Categorize issue types
        for error in result['errors']:
            self.issue_types[self._categorize_issue(error)] += 1

        self.results.append(result)
        return result

    def _check_xml_well_formed(self, content: str, result: Dict) -> bool:
        """Check that the SVG content parses as well-formed XML.

        SVG is strict XML.  AI-generated decks frequently produce content that
        looks fine in HTML5-tolerant previews but fails strict XML parsing —
        common causes are HTML named entities (&nbsp; &mdash; &copy;…) and
        bare XML reserved characters in text (R&D, error < 5%).  Such pages
        cannot be exported to PPTX, so we surface them here as a hard error
        before any downstream check looks at them.

        Returns True when the document is well-formed; False otherwise.
        """
        try:
            ET.fromstring(content)
            return True
        except ET.ParseError as e:
            result['errors'].append(
                f"Invalid XML: {e} — SVG must be well-formed XML. "
                f"Use raw Unicode for typography (—, ©, →, NBSP); "
                f"escape XML reserved chars as &amp; &lt; &gt; &quot; &apos; "
                f"(see references/shared-standards.md §1)."
            )
            return False

    def _check_viewbox(self, content: str, result: Dict, expected_format: str = None):
        """Check viewBox attribute"""
        viewbox_match = re.search(r'viewBox="([^"]+)"', content)

        if not viewbox_match:
            result['errors'].append("Missing viewBox attribute")
            return

        viewbox = viewbox_match.group(1)
        result['info']['viewbox'] = viewbox

        # Check format
        if not re.match(r'0 0 \d+ \d+', viewbox):
            result['warnings'].append(f"Unusual viewBox format: {viewbox}")

        # Check if it matches expected format
        if expected_format and expected_format in CANVAS_FORMATS:
            expected_viewbox = CANVAS_FORMATS[expected_format]['viewbox']
            if viewbox != expected_viewbox:
                result['errors'].append(
                    f"viewBox mismatch: expected '{expected_viewbox}', got '{viewbox}'"
                )

    def _check_forbidden_elements(self, content: str, result: Dict):
        """Check forbidden elements (blocklist)"""
        content_lower = content.lower()

        # ============================================================
        # Forbidden elements blocklist - PPT incompatible
        # ============================================================

        # Clipping / masking
        # clipPath is allowed on <image> elements and on pptx_to_svg-generated
        # nested crop <svg data-pptx-crop="1"> wrappers. Both map back to
        # DrawingML picture geometry in the native converter.
        if '<clippath' in content_lower:
            # clip-path on non-image elements → error
            clip_on_non_image = re.search(
                r'<(?!image\b)(?!svg\b[^>]*\bdata-pptx-crop\s*=\s*["\']1["\'])\w+[^>]*\bclip-path\s*=',
                content,
                re.IGNORECASE,
            )
            if clip_on_non_image:
                result['errors'].append(
                    "clip-path is only allowed on <image> elements or "
                    "pptx_to_svg crop wrappers — for shapes, draw the target "
                    "shape directly instead of clipping")
            # Check that every clip-path reference has a matching <clipPath> def
            clip_refs = re.findall(r'clip-path\s*=\s*["\']url\(#([^)]+)\)', content)
            for ref_id in clip_refs:
                if f'id="{ref_id}"' not in content and f"id='{ref_id}'" not in content:
                    result['errors'].append(
                        f"clip-path references #{ref_id} but no matching "
                        f"<clipPath id=\"{ref_id}\"> definition found")
        if '<mask' in content_lower:
            result['errors'].append("Detected forbidden <mask> element (PPT does not support SVG masks)")

        # Style system
        if '<style' in content_lower:
            result['errors'].append("Detected forbidden <style> element (use inline attributes instead)")
        if re.search(r'\bclass\s*=', content):
            result['errors'].append("Detected forbidden class attribute (use inline styles instead)")
        # id attribute: only report error when <style> also exists (id is harmful only with CSS selectors)
        # id inside <defs> for linearGradient/filter etc. is required, Inkscape also auto-adds id to elements,
        # standalone id attributes have no impact on PPT export
        if '<style' in content_lower and re.search(r'\bid\s*=', content):
            result['errors'].append(
                "Detected id attribute used with <style> (CSS selectors forbidden, use inline styles instead)"
            )
        if re.search(r'<\?xml-stylesheet\b', content_lower):
            result['errors'].append("Detected forbidden xml-stylesheet (external CSS references forbidden)")
        if re.search(r'<link[^>]*rel\s*=\s*["\']stylesheet["\']', content_lower):
            result['errors'].append("Detected forbidden <link rel=\"stylesheet\"> (external CSS references forbidden)")
        if re.search(r'@import\s+', content_lower):
            result['errors'].append("Detected forbidden @import (external CSS references forbidden)")

        # Structure / nesting
        if '<foreignobject' in content_lower:
            result['errors'].append(
                "Detected forbidden <foreignObject> element (use <tspan> for manual line breaks)")
        has_symbol = '<symbol' in content_lower
        has_use = re.search(r'<use\b', content_lower) is not None
        if has_symbol and has_use:
            result['errors'].append("Detected forbidden <symbol> + <use> complex usage (use basic shapes or simple <use> instead)")
        # marker-start / marker-end are conditionally allowed (see shared-standards.md §1.1).
        # The converter maps qualifying <marker> defs to native DrawingML <a:headEnd>/<a:tailEnd>.
        # We only warn when a marker is used without an obvious <defs> definition in the same file.
        if re.search(r'\bmarker-(?:start|end)\s*=\s*["\']url\(#([^)]+)\)', content_lower):
            if '<marker' not in content_lower:
                result['errors'].append(
                    "Detected marker-start/marker-end referencing a marker id, "
                    "but no <marker> element found in the file")

        # Text / fonts
        if '<textpath' in content_lower:
            result['errors'].append("Detected forbidden <textPath> element (path text is incompatible with PPT)")
        if '@font-face' in content_lower:
            result['errors'].append("Detected forbidden @font-face (use system font stack)")

        # Animation / interaction
        if re.search(r'<animate', content_lower):
            result['errors'].append("Detected forbidden SMIL animation element <animate*> (SVG animations are not exported)")
        if re.search(r'<set\b', content_lower):
            result['errors'].append("Detected forbidden SMIL animation element <set> (SVG animations are not exported)")
        if '<script' in content_lower:
            result['errors'].append("Detected forbidden <script> element (scripts and event handlers forbidden)")
        if re.search(r'\bon\w+\s*=', content):  # onclick, onload etc.
            result['errors'].append("Detected forbidden event attributes (e.g., onclick, onload)")

        # Other discouraged elements
        if '<iframe' in content_lower:
            result['errors'].append("Detected <iframe> element (should not appear in SVG)")
        if re.search(r'rgba\s*\(', content_lower):
            result['errors'].append("Detected forbidden rgba() color (use fill-opacity/stroke-opacity instead)")
        if re.search(r'<g[^>]*\sopacity\s*=', content_lower):
            result['errors'].append("Detected forbidden <g opacity> (set opacity on each child element individually)")
        if re.search(r'<image[^>]*\sopacity\s*=', content_lower):
            result['errors'].append("Detected forbidden <image opacity> (use overlay mask approach)")

    def _check_fonts(self, content: str, result: Dict):
        """Check font usage.

        PPTX stores a single `typeface` per run with no runtime fallback, so every
        stack must END with a cross-platform pre-installed family. See
        strategist.md §g "PPT-safe font discipline".
        """
        font_matches = re.findall(
            r'font-family[:\s]*["\']([^"\']+)["\']', content, re.IGNORECASE)

        if not font_matches:
            return

        result['info']['fonts'] = list(set(font_matches))

        # Pre-installed on Windows + macOS out of the box (plus their direct
        # FONT_FALLBACK_WIN mappings). A stack whose last concrete family is in
        # this set survives the PPTX round-trip on any viewer machine.
        ppt_safe_tail = {
            'microsoft yahei', 'simhei', 'simsun', 'kaiti', 'fangsong',
            'pingfang sc', 'heiti sc', 'songti sc', 'stsong',
            'arial', 'arial black', 'calibri', 'segoe ui', 'verdana',
            'helvetica', 'helvetica neue', 'tahoma', 'trebuchet ms',
            'times new roman', 'times', 'georgia', 'cambria', 'palatino',
            'consolas', 'courier new', 'menlo', 'monaco',
            'impact',
        }

        for font_family in font_matches:
            # Drop the generic CSS fallback (sans-serif / serif / monospace)
            # and inspect the last concrete family.
            parts = [p.strip().strip('"').strip("'").lower()
                     for p in font_family.split(',')]
            parts = [p for p in parts
                     if p and p not in ('sans-serif', 'serif', 'monospace',
                                        'cursive', 'fantasy', 'system-ui')]
            if not parts:
                continue
            tail = parts[-1]
            if tail not in ppt_safe_tail:
                result['warnings'].append(
                    f"Font stack does not end on a PPT-safe family "
                    f"(expected e.g. Microsoft YaHei / SimSun / Arial / "
                    f"Times New Roman / Consolas): {font_family}"
                )
                break

    def _check_dimensions(self, content: str, result: Dict):
        """Check width/height consistency with viewBox"""
        width_match = re.search(r'width="(\d+)"', content)
        height_match = re.search(r'height="(\d+)"', content)

        if width_match and height_match:
            width = width_match.group(1)
            height = height_match.group(1)
            result['info']['dimensions'] = f"{width}x{height}"

            # Check consistency with viewBox
            if 'viewbox' in result['info']:
                viewbox_parts = result['info']['viewbox'].split()
                if len(viewbox_parts) == 4:
                    vb_width, vb_height = viewbox_parts[2], viewbox_parts[3]
                    if width != vb_width or height != vb_height:
                        result['warnings'].append(
                            f"width/height ({width}x{height}) does not match viewBox "
                            f"({vb_width}x{vb_height})"
                        )

    def _check_text_elements(self, content: str, result: Dict):
        """Check text elements and wrapping methods"""
        # Count text and tspan elements
        text_count = content.count('<text')
        tspan_count = content.count('<tspan')

        result['info']['text_elements'] = text_count
        result['info']['tspan_elements'] = tspan_count

        # Check for overly long single-line text (may need wrapping)
        text_matches = re.findall(r'<text[^>]*>([^<]{100,})</text>', content)
        if text_matches:
            result['warnings'].append(
                f"Detected {len(text_matches)} potentially overly long single-line text(s) (consider using tspan for wrapping)"
            )

        self._check_textbox_contract(content, result)

    def _check_textbox_contract(self, content: str, result: Dict):
        """Detect fragile text authoring that turns into bad PPT text boxes."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return

        svg_ns = "{http://www.w3.org/2000/svg}"
        text_nodes = [node for node in root.iter() if node.tag == f"{svg_ns}text"]

        def _num(node: ET.Element, name: str) -> float | None:
            raw = node.attrib.get(name)
            if raw is None:
                return None
            match = re.match(r"\s*([-+]?(?:\d*\.\d+|\d+\.?))", raw)
            if not match:
                return None
            try:
                return float(match.group(1))
            except ValueError:
                return None

        def _text(node: ET.Element) -> str:
            return html.unescape("".join(node.itertext())).strip()

        def _num_any(node: ET.Element, names: tuple[str, ...]) -> float | None:
            for name in names:
                value = _num(node, name)
                if value is not None:
                    return value
            return None

        def _ends_sentence(text: str) -> bool:
            return bool(re.search(r"[。！？!?；;：:，,、）)\]】》〉]$", text.strip()))

        def _ends_sentence(text: str) -> bool:
            stripped = text.strip()
            if not stripped:
                return False
            return stripped[-1] in {
                ".", ",", ";", ":", "!", "?", ")", "]",
                "\u3002", "\uFF0C", "\uFF1B", "\uFF1A", "\uFF01", "\uFF1F",
                "\u3001", "\uFF09", "\u3011", "\u300B", "\u3009",
            }

        try:
            canvas_w, canvas_h = self._svg_viewbox_size(root)
        except Exception:
            canvas_w, canvas_h = 1280.0, 720.0

        def _font_size(node: ET.Element) -> float:
            return _num(node, "font-size") or 16.0

        def _estimated_width(text: str, font_size: float) -> float:
            width = 0.0
            for ch in text:
                if ch == "\n":
                    continue
                if ch.isspace():
                    width += font_size * 0.35
                elif ord(ch) > 255:
                    width += font_size * 1.02
                else:
                    width += font_size * 0.56
            return width

        def _line_count(node: ET.Element) -> int:
            tspans = [
                child for child in node.iter()
                if child is not node and (child.tag.rsplit('}', 1)[-1] == 'tspan')
            ]
            line_tspans = [
                child for child in tspans
                if child.attrib.get("x") is not None
                or child.attrib.get("y") is not None
                or child.attrib.get("dy") is not None
            ]
            if line_tspans:
                return max(1, len(line_tspans))
            plain = _text(node)
            return max(1, plain.count("\n") + 1)

        def _declared_box(node: ET.Element) -> tuple[float, float, float, float] | None:
            raw = [
                node.attrib.get("data-box-x") or node.attrib.get("data-textbox-x"),
                node.attrib.get("data-box-y") or node.attrib.get("data-textbox-y"),
                node.attrib.get("data-box-width") or node.attrib.get("data-textbox-width"),
                node.attrib.get("data-box-height") or node.attrib.get("data-textbox-height"),
            ]
            if not all(value is not None for value in raw):
                return None
            try:
                x, y, w, h = [float(value) for value in raw]
            except (TypeError, ValueError):
                return None
            if w <= 0 or h <= 0:
                return None
            return x, y, w, h

        def _estimated_text_box(node: ET.Element) -> tuple[float, float, float, float] | None:
            declared = _declared_box(node)
            if declared is not None:
                return declared
            plain = _text(node)
            if not plain:
                return None
            x = _num(node, "x")
            y = _num(node, "y")
            if x is None or y is None:
                return None
            font_size = _font_size(node)
            lines = [line for line in plain.splitlines() if line.strip()] or [plain]
            width = max(_estimated_width(line, font_size) for line in lines)
            height = max(font_size * 1.25, _line_count(node) * font_size * 1.25)
            # SVG text y is the baseline, while DrawingML boxes are top-left.
            return x, y - font_size, max(1.0, width), height

        def _is_layout_text(node: ET.Element, text: str, box: tuple[float, float, float, float]) -> bool:
            attrs = " ".join(str(node.attrib.get(k, "")) for k in (
                "id", "data-role", "data-page-number", "data-footer", "data-citation",
            )).lower()
            if any(token in attrs for token in (
                "page-number", "pagenum", "sldnum", "footer", "citation",
                "reference", "logo", "school", "title", "subtitle",
                "header", "section",
            )):
                return True
            x, y, w, h = box
            compact = " ".join(text.split())
            if re.fullmatch(r"\d{1,2}(?:\s*/\s*\d{1,2})?", compact) and (y > canvas_h * 0.80 or x > canvas_w * 0.80):
                return True
            if y > canvas_h * 0.86 and h <= 32:
                return True
            return False

        def _shape_box_from_attrs(node: ET.Element) -> tuple[float, float, float, float] | None:
            x = _num_any(node, ("data-shape-x", "data-container-x"))
            y = _num_any(node, ("data-shape-y", "data-container-y"))
            w = _num_any(node, ("data-shape-width", "data-container-width"))
            h = _num_any(node, ("data-shape-height", "data-container-height"))
            if x is None or y is None or w is None or h is None or w <= 0 or h <= 0:
                return None
            return x, y, w, h

        def _box_inside(inner: tuple[float, float, float, float], outer: tuple[float, float, float, float], inset: float) -> bool:
            ix, iy, iw, ih = inner
            ox, oy, ow, oh = outer
            return (
                ix >= ox + inset - 0.5
                and iy >= oy + inset - 0.5
                and ix + iw <= ox + ow - inset + 0.5
                and iy + ih <= oy + oh - inset + 0.5
            )

        def _center_inside(box: tuple[float, float, float, float], shape: tuple[float, float, float, float]) -> bool:
            x, y, w, h = box
            sx, sy, sw, sh = shape
            cx, cy = x + w / 2, y + h / 2
            return sx <= cx <= sx + sw and sy <= cy <= sy + sh

        def _point_inside(x: float | None, y: float | None, shape: tuple[float, float, float, float]) -> bool:
            if x is None or y is None:
                return False
            sx, sy, sw, sh = shape
            return sx <= x <= sx + sw and sy <= y <= sy + sh

        visible_rects: list[tuple[str, tuple[float, float, float, float]]] = []
        for elem in root.iter():
            if elem.tag != f"{svg_ns}rect":
                continue
            x = _num(elem, "x") or 0.0
            y = _num(elem, "y") or 0.0
            w = _num(elem, "width") or 0.0
            h = _num(elem, "height") or 0.0
            if w < 60 or h < 32:
                continue
            is_background = x <= 1 and y <= 1 and w >= canvas_w - 2 and h >= canvas_h - 2
            if is_background:
                continue
            elem_id = elem.attrib.get("id", "").lower()
            if any(token in elem_id for token in ("background", "bg", "footer", "header", "logo", "page-number")):
                continue
            fill = (elem.attrib.get("fill") or "").strip().lower()
            stroke = (elem.attrib.get("stroke") or "").strip().lower()
            opacity = _num(elem, "opacity")
            fill_opacity = _num(elem, "fill-opacity")
            if fill in ("none", "transparent", "") and stroke in ("none", "transparent", ""):
                continue
            if opacity is not None and opacity <= 0.02:
                continue
            if fill_opacity is not None and fill_opacity <= 0.02 and stroke in ("none", "transparent", ""):
                continue
            visible_rects.append((elem.attrib.get("id", f"rect_{len(visible_rects)+1}"), (x, y, w, h)))

        text_boxes: list[dict[str, object]] = []
        for node in text_nodes:
            plain = _text(node)
            if not plain:
                continue
            box = _estimated_text_box(node)
            if box is None:
                continue
            text_boxes.append({
                "node": node,
                "text": plain,
                "box": box,
                "declared": _declared_box(node) is not None,
                "layout": _is_layout_text(node, plain, box),
            })

        # Explicit box contract: either all four attrs are present, or none.
        for node in text_nodes:
            box_attrs = [
                node.attrib.get("data-box-x") or node.attrib.get("data-textbox-x"),
                node.attrib.get("data-box-y") or node.attrib.get("data-textbox-y"),
                node.attrib.get("data-box-width") or node.attrib.get("data-textbox-width"),
                node.attrib.get("data-box-height") or node.attrib.get("data-textbox-height"),
            ]
            if any(v is not None for v in box_attrs) and not all(v is not None for v in box_attrs):
                result['errors'].append(
                    "Incomplete explicit text-box contract: use all four "
                    "data-box-x/y/width/height attributes on <text>."
                )
            if all(v is not None for v in box_attrs):
                try:
                    box_x, box_y, box_w, box_h = [float(v) for v in box_attrs]
                except (TypeError, ValueError):
                    result['errors'].append(
                        "Invalid explicit text-box contract: data-box-x/y/width/height "
                        "must be numeric SVG coordinates."
                    )
                    continue
                if box_w <= 0 or box_h <= 0:
                    result['errors'].append(
                        "Invalid explicit text-box contract: data-box-width and "
                        "data-box-height must be positive."
                    )
                    continue

                shape_x = _num_any(node, ("data-shape-x", "data-container-x"))
                shape_y = _num_any(node, ("data-shape-y", "data-container-y"))
                shape_w = _num_any(node, ("data-shape-width", "data-container-width"))
                shape_h = _num_any(node, ("data-shape-height", "data-container-height"))
                shape_values = (shape_x, shape_y, shape_w, shape_h)
                role_blob = " ".join(str(node.attrib.get(k, "")) for k in ("id", "class", "data-role")).lower()
                chrome_tokens = (
                    "page-number", "pagenum", "sldnum", "footer", "citation", "reference",
                    "logo", "school",
                )
                content_tokens = ("caption", "body", "label", "item", "node", "card", "bullet", "content")
                baseline_x = _num(node, "x")
                text_anchor = (node.attrib.get("text-anchor") or "start").lower()
                if (
                    not any(v is not None for v in shape_values)
                    and not any(token in role_blob for token in chrome_tokens)
                    and (
                        (box_w >= canvas_w * 0.78 and box_x <= 8 and text_anchor == "start" and baseline_x is not None and baseline_x >= box_x + 40)
                        or (box_w >= canvas_w * 0.94 and any(token in role_blob for token in content_tokens))
                    )
                ):
                    result['errors'].append(
                        "Suspicious explicit text-box contract: content text uses a full-slide "
                        "data-box frame. Put one module's text in one local text box, enable wrapping, "
                        f"and keep the text box at least {TEXT_BOX_SHAPE_INSET_PT:g}pt inside its background shape."
                    )

                font_size = _font_size(node)
                line_count = _line_count(node)
                estimated_width = _estimated_width(_text(node), font_size)
                wrap_enabled = (node.attrib.get("data-wrap") or node.attrib.get("data-text-wrap") or "").lower() in {"square", "true", "wrap"}
                if line_count == 1 and estimated_width > box_w * 1.10 and not wrap_enabled:
                    result['errors'].append(
                        "Text exceeds its declared data-box-width. Enable data-wrap=\"square\", "
                        "wrap it with line-break <tspan> elements, shorten it, or enlarge the "
                        "bounded shape before export."
                    )
                if wrap_enabled:
                    wrapped_lines = max(line_count, int(math.ceil(max(estimated_width, 1.0) / max(box_w, 1.0))))
                    estimated_height = max(font_size * 1.25, wrapped_lines * font_size * 1.25)
                else:
                    estimated_height = max(font_size * 1.25, line_count * font_size * 1.25)
                if estimated_height > box_h * 1.12:
                    result['errors'].append(
                        "Text exceeds its declared data-box-height. Reduce the line count, "
                        "font size, or use a taller slot/card."
                    )

                if any(v is not None for v in shape_values) and not all(v is not None for v in shape_values):
                    result['errors'].append(
                        "Incomplete text container contract: use all four "
                        "data-shape-x/y/width/height attributes when text sits inside a visible shape."
                    )
                elif all(v is not None for v in shape_values):
                    assert shape_x is not None and shape_y is not None and shape_w is not None and shape_h is not None
                    if shape_w <= 0 or shape_h <= 0:
                        result['errors'].append(
                            "Invalid text container contract: data-shape-width and "
                            "data-shape-height must be positive."
                        )
                    else:
                        inset = TEXT_BOX_SHAPE_INSET_PX
                        if (
                            box_x < shape_x + inset - 0.5
                            or box_y < shape_y + inset - 0.5
                            or box_x + box_w > shape_x + shape_w - inset + 0.5
                            or box_y + box_h > shape_y + shape_h - inset + 0.5
                        ):
                            result['errors'].append(
                                f"Text box must stay at least {TEXT_BOX_SHAPE_INSET_PT:g}pt "
                                f"({inset:.2f}px) inside its background shape. "
                                "Read text_box_shape_inset_px from spec_lock.md and keep data-box bounds "
                                "within data-shape bounds."
                            )
                        if (
                            abs((box_x + box_w / 2) - (shape_x + shape_w / 2)) > TEXT_BOX_CENTER_TOLERANCE_PX
                            or abs((box_y + box_h / 2) - (shape_y + shape_h / 2)) > TEXT_BOX_CENTER_TOLERANCE_PX
                        ):
                            result['errors'].append(
                                f"Text box is not centered in its background shape "
                                f"(tolerance {int(TEXT_BOX_CENTER_TOLERANCE_PX)}px). "
                                "Center data-box inside the declared data-shape frame."
                            )

        # Page-bound guard for unboxed text. Boxed text is checked against its
        # declared frame above.
        for node in text_nodes:
            if any(k in node.attrib for k in ("data-box-x", "data-textbox-x")):
                continue
            x = _num(node, "x")
            y = _num(node, "y")
            if x is None or y is None:
                continue
            font_size = _font_size(node)
            plain = _text(node)
            if not plain:
                continue
            estimated_width = _estimated_width(plain, font_size)
            if x < -2 or y < -2 or x + estimated_width > canvas_w + 8 or y + font_size * 1.25 > canvas_h + 8:
                result['errors'].append(
                    "Unboxed text appears to overflow the slide canvas. Use a bounded "
                    "data-box frame inside the content region or wrap the text."
                )

        # Automatic visible-shape containment: text visually placed inside a
        # card/shape must be bounded by that card with a fixed inset. This
        # catches pages where no data-shape contract was authored.
        for item in text_boxes:
            if item["layout"]:
                continue
            node = item["node"]
            assert isinstance(node, ET.Element)
            text = str(item["text"])
            box = item["box"]
            assert isinstance(box, tuple)
            shape_box = _shape_box_from_attrs(node)
            shape_label = "declared data-shape"
            if shape_box is None:
                candidates = [
                    (name, rect_box)
                    for name, rect_box in visible_rects
                    if (
                        _center_inside(box, rect_box)
                        or _point_inside(_num(node, "x"), _num(node, "y"), rect_box)
                        or self._rect_overlap_ratio(box, rect_box) >= 0.10
                    )
                ]
                if candidates:
                    # Choose the smallest containing card; it is usually the
                    # actual background shape instead of a larger section panel.
                    shape_label, shape_box = min(candidates, key=lambda item_pair: item_pair[1][2] * item_pair[1][3])
            if shape_box is None:
                continue
            if not _box_inside(box, shape_box, TEXT_BOX_SHAPE_INSET_PX):
                result['errors'].append(
                    f"Text box is not fully wrapped by its visible shape ({shape_label}). "
                    f"Keep every text boundary at least {TEXT_BOX_SHAPE_INSET_PT:g}pt "
                    f"({TEXT_BOX_SHAPE_INSET_PX:.2f}px) inside the shape boundary; "
                    "set data-box-* from the inset shape frame, not from split text coordinates."
                )

        # Text-to-text overlap guard. Ignore intentional tiny footer/page
        # labels and explicitly marked inline/tspan fragments; content boxes
        # should never overlap in the PPT body region.
        for left_idx, left in enumerate(text_boxes):
            if left["layout"]:
                continue
            left_box = left["box"]
            assert isinstance(left_box, tuple)
            left_text = str(left["text"])
            if not left_text.strip():
                continue
            for right in text_boxes[left_idx + 1:]:
                if right["layout"]:
                    continue
                right_box = right["box"]
                assert isinstance(right_box, tuple)
                ratio = self._rect_overlap_ratio(left_box, right_box)
                if ratio <= TEXT_BOX_OVERLAP_RATIO_LIMIT:
                    continue
                right_text = str(right["text"])
                if not right_text.strip():
                    continue
                result['errors'].append(
                    "Detected overlapping text boxes. Keep text modules in separate "
                    f"non-overlapping data-box frames (overlap ratio {ratio:.2f}). "
                    f"Samples: {left_text[:24]!r} / {right_text[:24]!r}"
                )
                break

        # Stacked fragment guard: many short text nodes on the same baseline are
        # usually a phrase split into separate text boxes. Inline formatting must
        # use one <text> with inline <tspan> runs instead.
        rows: dict[int, list[tuple[float, str]]] = defaultdict(list)
        for node in text_nodes:
            text = _text(node)
            if not text or len(text) > 28:
                continue
            if any(k in node.attrib for k in ("data-box-x", "data-textbox-x")):
                continue
            x = _num(node, "x")
            y = _num(node, "y")
            if x is None or y is None:
                continue
            rows[round(y)].append((x, text))

        for y_key, row in rows.items():
            row.sort()
            if len(row) < 2:
                continue
            for idx in range(len(row) - 1):
                left_x, left_text = row[idx]
                right_x, right_text = row[idx + 1]
                joined_pair = left_text + right_text
                same_sentence_split = (
                    right_x > left_x
                    and len(right_text) <= 3
                    and len(joined_pair) <= 42
                    and not _ends_sentence(left_text)
                    and not re.fullmatch(
                        r"[,.;:!?\uFF0C\u3002\uFF1B\uFF1A\uFF01\uFF1F\u3001\uFF09\)\]\u3011]",
                        right_text,
                    )
                )
                latin_fragment_split = (
                    len(row) >= 3
                    and len(joined_pair) <= 42
                    and any(re.search(r"[A-Za-z]", item[1]) for item in row)
                )
                if same_sentence_split or latin_fragment_split:
                    result['errors'].append(
                        "Detected likely split sentence fragments on one baseline "
                        f"(y~{y_key}: {joined_pair!r}). Keep a complete sentence in one "
                        "<text> element with inline <tspan> runs; do not split a final "
                        "character or word into a separate text box."
                    )
                    break
            continue
            joined = "".join(item[1] for item in row)
            if len(joined) <= 36 and any(re.search(r"[A-Za-z]", item[1]) for item in row):
                result['errors'].append(
                    "Detected likely stacked text fragments on one baseline "
                    f"(y≈{y_key}: {joined!r}). Use one <text> element with "
                    "inline <tspan> runs; do not split one phrase into "
                    "multiple adjacent text boxes."
                )


    def _check_minimum_body_font_size(self, content: str, result: Dict):
        """Body text must be readable: only citations/references and page numbers may be <12px."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return

        def _local(node: ET.Element) -> str:
            return node.tag.rsplit('}', 1)[-1] if isinstance(node.tag, str) else str(node.tag)

        def _num(raw: str | None) -> float | None:
            if raw is None:
                return None
            match = re.match(r"\s*([-+]?(?:\d*\.\d+|\d+\.?))", raw)
            if not match:
                return None
            try:
                return float(match.group(1))
            except ValueError:
                return None

        def _text(node: ET.Element) -> str:
            return html.unescape("".join(node.itertext())).strip()

        exempt_tokens = (
            "page-number", "pagenum", "sldnum", "slide-number",
            "citation", "reference", "references", "bibliography",
            "source", "doi", "footer-citation",
        )
        for node in root.iter():
            if _local(node) != "text":
                continue
            plain = _text(node)
            if not plain:
                continue
            marker = " ".join(str(node.attrib.get(k, "")) for k in ("id", "class", "data-role", "data-page-number", "data-citation", "data-footer")).lower()
            if any(token in marker for token in exempt_tokens):
                continue
            fs = _num(node.attrib.get("font-size"))
            if fs is not None and fs < 12.0:
                result['errors'].append(
                    f"Body text font-size {fs:g}px is below 12px. Only citation/reference footers and page numbers may be smaller."
                )

    def _check_image_references(self, content: str, svg_path: Path, result: Dict):
        """Check image file existence and resolution vs display size."""
        # Find all <image ...> elements (capture the full tag)
        img_tag_pattern = re.compile(r'<image\b([^>]*)/?>', re.IGNORECASE)

        svg_dir = svg_path.parent
        checked = set()

        for tag_match in img_tag_pattern.finditer(content):
            attrs = tag_match.group(1)

            # Extract href (prefer href over xlink:href)
            href_match = (
                re.search(r'\bhref="(?!data:)([^"]+)"', attrs) or
                re.search(r'\bxlink:href="(?!data:)([^"]+)"', attrs)
            )
            if not href_match:
                continue

            href = href_match.group(1)
            if self.template_mode and ('{{' in href or '}}' in href):
                continue
            if href in checked:
                continue
            checked.add(href)

            # Resolve path the same way finalize_svg.py and svg_to_pptx.py do:
            # first relative to the SVG directory, then relative to the project
            # root when SVGs live under svg_output/ or svg_final/.
            img_path = (svg_dir / href).resolve()
            if not img_path.exists():
                project_relative = (svg_dir.parent / href).resolve()
                if project_relative.exists():
                    img_path = project_relative

            if not img_path.exists():
                result['errors'].append(
                    f"Image file not found: {href} (resolved to {img_path})")
                continue

            # Check resolution vs display size
            w_match = re.search(r'\bwidth="([^"]+)"', attrs)
            h_match = re.search(r'\bheight="([^"]+)"', attrs)
            display_w_str = w_match.group(1) if w_match else None
            display_h_str = h_match.group(1) if h_match else None
            if not display_w_str or not display_h_str:
                continue

            try:
                display_w = float(display_w_str)
                display_h = float(display_h_str)
            except (ValueError, TypeError):
                continue

            try:
                from PIL import Image as PILImage
                with PILImage.open(img_path) as img:
                    actual_w, actual_h = img.size

                if actual_w < display_w or actual_h < display_h:
                    result['warnings'].append(
                        f"Image {href} is {actual_w}x{actual_h} but displayed at "
                        f"{int(display_w)}x{int(display_h)} — may appear blurry")
                elif actual_w > display_w * 4 and actual_h > display_h * 4:
                    result['warnings'].append(
                        f"Image {href} is {actual_w}x{actual_h} but displayed at "
                        f"{int(display_w)}x{int(display_h)} — consider downsizing "
                        f"to reduce file size")
            except ImportError:
                pass  # PIL not available, skip resolution check
            except Exception:
                pass  # Image unreadable, skip resolution check

    def _check_formula_png_contract(self, content: str, result: Dict):
        """Ensure displayed formulas use rendered PNG blocks, not SVG text boxes."""
        content_lower = content.lower()
        formula_page = any(token in content_lower for token in (
            'content_type="formula_step"',
            'content_type="formula_paragraph"',
            "content-type='formula_step'",
            "content-type='formula_paragraph'",
            'data-content-type="formula_block"',
            "data-content-type='formula_block'",
            'data-formula-page="true"',
            "data-formula-page='true'",
        ))
        formula_image = re.search(
            r'<image\b(?=[^>]*(?:data-formula-block-png\s*=\s*["\']true["\']|href\s*=\s*["\'][^"\']*images[/\\]formulas[/\\]formula_block_[^"\']+\.png["\']))',
            content,
            flags=re.IGNORECASE,
        )
        legacy_formula_image = re.search(
            r'<image\b[^>]*(?:data-formula-png\s*=\s*["\']true["\']|href\s*=\s*["\'][^"\']*images/formulas/[^"\']+\.png["\'])',
            content,
            flags=re.IGNORECASE,
        )
        if self.template_mode and '{{formula_block_png_href}}' in content:
            return

        if formula_page and not formula_image:
            result['errors'].append(
                "Formula page is missing a rendered formula block PNG image. "
                "Render formula role, equation, and interpretation with "
                "scripts/latex_formula_to_png.py --block-json and embed it as "
                "<image data-formula-png=\"true\" data-formula-block-png=\"true\">."
            )
        elif legacy_formula_image and not formula_image:
            result['warnings'].append(
                "Detected a legacy formula PNG without data-formula-block-png. "
                "Formula title, equation, and variable explanation should be one block PNG."
            )

        formula_block_images = re.findall(
            r'<image\b(?=[^>]*(?:data-formula-block-png\s*=\s*["\']true["\']|href\s*=\s*["\'][^"\']*images[/\\]formulas[/\\]formula_block_[^"\']+\.png["\']))',
            content,
            flags=re.IGNORECASE,
        )
        if formula_page and len(formula_block_images) > 5:
            result['errors'].append(
                f"Formula page contains {len(formula_block_images)} formula block PNGs; "
                "the maximum is 5 per slide. Split formulas across additional pages."
            )
        separator_count = len(re.findall(r'data-formula-separator\s*=\s*["\']true["\']', content, flags=re.IGNORECASE))
        required_separators = max(0, len(formula_block_images) - 1)
        if formula_page and formula_block_images and separator_count < required_separators:
            result['errors'].append(
                "Adjacent formula blocks must be separated by gray 1.5pt dashed lines "
                "with data-formula-separator=\"true\"."
            )

        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            root = None

        formula_boxes: list[tuple[str, tuple[float, float, float, float]]] = []
        separator_lines: list[ET.Element] = []
        if root is not None:
            for elem in root.iter():
                tag = elem.tag.rsplit('}', 1)[-1] if '}' in elem.tag else elem.tag
                if tag == 'image':
                    attrs = " ".join(str(elem.attrib.get(k, "")) for k in (
                        'id', 'href', f'{{http://www.w3.org/1999/xlink}}href',
                        'data-formula-png', 'data-formula-block-png'
                    )).lower()
                    is_formula = (
                        elem.attrib.get('data-formula-block-png', '').lower() == 'true'
                        or 'images/formulas/formula_block_' in attrs
                        or elem.attrib.get('data-formula-png', '').lower() == 'true'
                    )
                    if is_formula:
                        href = elem.attrib.get('href') or elem.attrib.get('{http://www.w3.org/1999/xlink}href') or ""
                        if '{{' in href or '}}' in href or not href.strip():
                            result['errors'].append(
                                "Formula PNG image still has an unresolved formula_block_png_href placeholder."
                            )
                        if href and not (
                            href.startswith('data:image/png;base64,')
                            or re.search(r'images[/\\]formulas[/\\]formula_block_[^/\\]+\.png$', href, re.IGNORECASE)
                            or re.search(r'images/formulas/formula_block_[^"\']+\.png', href, re.IGNORECASE)
                        ):
                            result['errors'].append(
                                f"Formula block image href must point to images/formulas/formula_block_*.png "
                                f"or an embedded PNG data URI; got {href!r}."
                            )
                        box = (
                            self._attr_float(elem, 'x'),
                            self._attr_float(elem, 'y'),
                            self._attr_float(elem, 'width'),
                            self._attr_float(elem, 'height'),
                        )
                        if box[2] <= 0 or box[3] <= 0:
                            result['errors'].append("Formula block PNG has a zero-sized image box.")
                        formula_boxes.append((elem.attrib.get('id') or f'formula_image_{len(formula_boxes)+1}', box))
                elif tag == 'line' and elem.attrib.get('data-formula-separator', '').lower() == 'true':
                    separator_lines.append(elem)

        if formula_page and formula_boxes:
            for i, (left_id, left_box) in enumerate(formula_boxes):
                for right_id, right_box in formula_boxes[i + 1:]:
                    if self._rect_overlap_ratio(left_box, right_box) > 0.02:
                        result['errors'].append(
                            f"Formula block PNGs overlap or stack ({left_id}, {right_id}). "
                            "Formula and text explanation, and formula blocks, must use separate non-overlapping boxes."
                        )

            bad_separator = False
            for line in separator_lines:
                stroke = (line.attrib.get('stroke') or '').strip().lower()
                stroke_width = self._attr_float(line, 'stroke-width', 0.0)
                dash = (line.attrib.get('stroke-dasharray') or '').strip()
                if stroke not in ('#a6a6a6', '#999999', '#9ca3af', '#94a3b8', 'gray', 'grey') or abs(stroke_width - 1.5) > 0.15 or not dash:
                    bad_separator = True
                    break
            if separator_lines and bad_separator:
                result['errors'].append(
                    "Formula separators must be gray 1.5pt dashed lines "
                    "(stroke #A6A6A6, stroke-width 1.5, stroke-dasharray 8 6)."
                )

        if root is not None:
            math_texts = []
            for elem in root.iter():
                tag = elem.tag.rsplit('}', 1)[-1] if '}' in elem.tag else elem.tag
                if tag == 'text':
                    plain = html.unescape(''.join(elem.itertext()))
                    if plain.strip():
                        math_texts.append(plain)
        else:
            math_texts = [
                html.unescape(re.sub(r'<[^>]+>', '', raw))
                for raw in re.findall(r'<text\b[^>]*>(.*?)</text>', content, flags=re.IGNORECASE | re.DOTALL)
            ]

        suspicious_samples: list[str] = []
        operator_chars = "=\u2211\u03a3\u222b\u220f\u221a\u2264\u2265\u2248\u2260\u00b1\u00d7\u00f7\u221e\u2202\u2207\u2208\u2209\u2282\u2286\u2283\u2287"
        relation_tokens = ("=", "\\", "_", "^", "\u2211", "\u222b", "\u2264", "\u2265", "\u2248")
        for plain in math_texts:
            compact = " ".join(plain.split())
            if len(compact) < 10:
                continue
            operator_score = sum(compact.count(ch) for ch in operator_chars)
            latex_score = len(re.findall(
                r'\\(?:frac|sum|int|prod|sqrt|alpha|beta|gamma|phi|theta|infty|partial|cdot|times|leq|geq|mathbb|mathbf|left|right)',
                compact,
            ))
            script_score = len(re.findall(r'[_^][A-Za-z0-9{]', compact))
            has_math_relation = any(token in compact for token in relation_tokens)
            looks_dense = (operator_score + latex_score + script_score >= 2 and (has_math_relation or len(compact) >= 18))
            if looks_dense or (latex_score and len(compact) >= 12):
                suspicious_samples.append(compact[:80])

        if suspicious_samples and not formula_image:
            sample = suspicious_samples[0]
            result['errors'].append(
                "Detected displayed equation-like SVG text without a formula block PNG. "
                "Complete formulas, formula titles, and variable explanations must be rendered "
                "with scripts/latex_formula_to_png.py --block-json and embedded as one PNG. "
                f"Sample text: {sample!r}"
            )

    def _check_placeholder_prompt_residue(self, content: str, result: Dict):
        """Fail final SVGs that still show unused PPT placeholder prompts."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return

        prompts: list[str] = []
        click = "\u5355\u51fb"
        edit_words = ("\u7f16\u8f91", "\u6dfb\u52a0", "\u63d2\u5165")
        presenter = "\u6f14\u8bb2\u8005"
        course = "\u8bfe\u7a0b"
        for elem in root.iter():
            tag = elem.tag.rsplit('}', 1)[-1] if '}' in elem.tag else elem.tag
            if tag != 'text':
                continue
            text_value = " ".join("".join(elem.itertext()).split())
            if not text_value:
                continue
            if _is_ppt_placeholder_prompt is not None:
                is_prompt = _is_ppt_placeholder_prompt(text_value)
            else:
                is_prompt = (
                    'click to ' in text_value.lower()
                    or (click in text_value and any(v in text_value for v in edit_words))
                    or (presenter in text_value and course in text_value)
                )
            if is_prompt:
                prompts.append(text_value)

        if prompts:
            sample = "; ".join(prompts[:3])
            result['errors'].append(
                "Unused PPT template placeholder prompt remains in the final SVG. "
                "Fill the template slot or run finalize_svg.py with cleanup-placeholders; "
                f"do not overlay new text on top of placeholder prompts. Sample: {sample}"
            )

    def _check_animation_group_ids(self, content: str, result: Dict):
        """Warn when visible top-level groups cannot be customized."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return

        non_visual = {'defs', 'title', 'desc', 'metadata', 'style'}
        for index, child in enumerate(list(root), start=1):
            tag = child.tag.split('}', 1)[-1]
            if tag in non_visual:
                continue
            if tag == 'g' and not child.get('id'):
                result['warnings'].append(
                    f"Top-level visible <g> #{index} has no id; "
                    "object-level animation config cannot reference it"
                )

    def _check_shape_block_shadow_contract(self, content: str, result: Dict):
        """Require declared content blocks to carry the standard external shadow."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return

        defs: dict[str, ET.Element] = {}
        for elem in root.iter():
            elem_id = elem.attrib.get('id')
            if elem_id:
                defs[elem_id] = elem

        for elem in root.iter():
            tag = elem.tag.rsplit('}', 1)[-1] if '}' in elem.tag else elem.tag
            if tag not in {'rect', 'path', 'polygon', 'g'}:
                continue
            marker = " ".join(
                str(elem.attrib.get(k, ""))
                for k in ('id', 'data-role', 'data-shape-block', 'data-block', 'class')
            ).lower()
            if 'shape-block' not in marker and 'content-block' not in marker:
                continue
            if any(token in marker for token in ('background', 'footer', 'header', 'logo', 'page-number')):
                continue
            filt = elem.attrib.get('filter', '')
            match = re.search(r'url\(#([^)]+)\)', filt)
            if not match:
                result['errors'].append(
                    "Shape block is missing the required external shadow. "
                    "Use filter=\"url(#themeBlockShadow)\" with the PPTX shadow parameters."
                )
                continue
            filter_elem = defs.get(match.group(1))
            if filter_elem is None:
                result['errors'].append(
                    f"Shape block references missing shadow filter #{match.group(1)}."
                )
                continue
            if (filter_elem.attrib.get('data-pptx-shadow') or '').lower() not in {'outer', 'shadow'}:
                result['errors'].append(
                    "Shape block shadow filter must set data-pptx-shadow=\"outer\"."
                )
                continue
            expected = {
                'data-pptx-shadow-transparency': 0.60,
                'data-pptx-shadow-size': 102.0,
                'data-pptx-shadow-blur-pt': 5.0,
                'data-pptx-shadow-angle': 0.0,
                'data-pptx-shadow-distance-pt': 0.0,
            }
            for attr, expected_value in expected.items():
                actual = self._attr_float(filter_elem, attr, -999999.0)
                if actual == -999999.0 or abs(actual - expected_value) > 0.05:
                    result['errors'].append(
                        "Shape block shadow parameters must match: transparency 60%, "
                        "size 102%, blur 5pt, angle 0, distance 0pt."
                    )
                    break

    def _get_spec_lock(self, svg_path: Path):
        """Locate and parse spec_lock.md near the SVG. Returns dict or None.

        Looks in svg_path.parent and svg_path.parent.parent (covers the two
        common layouts: SVG directly under <project>/ or under
        <project>/svg_output/). Results are cached per lock path.
        """
        if _parse_spec_lock is None:
            return None
        for candidate in (svg_path.parent / 'spec_lock.md',
                          svg_path.parent.parent / 'spec_lock.md'):
            if candidate in self._lock_cache:
                return self._lock_cache[candidate]
            if candidate.exists():
                try:
                    data = _parse_spec_lock(candidate)
                except Exception:
                    data = None
                self._lock_cache[candidate] = data
                if data is not None:
                    self._lock_seen = True
                return data
        return None

    def _check_spec_lock_drift(self, content: str, svg_path: Path, result: Dict):
        """Detect values used in the SVG that fall outside spec_lock.md.

        Covers colors (fill / stroke / stop-color), font-family, and font-size.
        Emits per-file warnings summarising the drift counts; exact drifting
        values are accumulated in self._drift_summary for the end-of-run
        aggregation. When spec_lock.md is missing, silently skip (consistent
        with executor-base.md §2.1's 'missing lock → warn and proceed' policy).
        """
        lock = self._get_spec_lock(svg_path)
        if lock is None:
            return

        # Build allow-sets from the lock
        allowed_colors = set()
        for v in lock.get('colors', {}).values():
            if HEX_VALUE_RE.fullmatch(v):
                allowed_colors.add(v.upper())

        typo = lock.get('typography', {})
        # Font families: default `font_family` plus any per-role `*_family`
        # override (title_family / body_family / emphasis_family / code_family,
        # per spec_lock_reference.md). Any of these is a legitimate declared
        # value; an SVG that uses any one of them is not drifting.
        allowed_fonts = set()
        if typo:
            default_font = typo.get('font_family', '').strip()
            if default_font:
                allowed_fonts.add(default_font)
            for k, v in typo.items():
                if k == 'font_family' or not k.endswith('_family'):
                    continue
                v_clean = v.strip()
                # Skip placeholder text like "same as body (omit if identical)"
                if not v_clean or v_clean.lower().startswith('same as'):
                    continue
                allowed_fonts.add(v_clean)

        # Sizes: declared slots are anchors; body is the ramp baseline.
        allowed_sizes = set()
        body_px = None
        for k, v in typo.items():
            if k == 'font_family' or k.endswith('_family'):
                continue
            allowed_sizes.add(self._normalize_size(v))
            if k == 'body':
                try:
                    body_px = float(self._normalize_size(v))
                except (ValueError, TypeError):
                    body_px = None

        # Scan SVG for used values
        color_drifts = set()
        for attr in ('fill', 'stroke', 'stop-color'):
            pattern = re.compile(rf'\b{attr}\s*=\s*["\'](#[0-9A-Fa-f]{{3,8}})["\']')
            for m in pattern.finditer(content):
                val = m.group(1).upper()
                if val not in allowed_colors:
                    color_drifts.add(val)

        font_drifts = set()
        for m in re.finditer(r'font-family\s*=\s*["\']([^"\']+)["\']', content):
            val = m.group(1).strip()
            if allowed_fonts and val not in allowed_fonts:
                font_drifts.add(val)

        size_drifts = set()
        for m in re.finditer(r'font-size\s*=\s*["\']([^"\']+)["\']', content):
            val = self._normalize_size(m.group(1))
            if not allowed_sizes or val in allowed_sizes:
                continue
            # Intermediate values are allowed when they sit inside the ramp
            # envelope (ratio to body within [RAMP_MIN_RATIO, RAMP_MAX_RATIO]).
            if body_px and body_px > 0:
                try:
                    ratio = float(val) / body_px
                    if RAMP_MIN_RATIO <= ratio <= RAMP_MAX_RATIO:
                        continue
                except ValueError:
                    pass
            size_drifts.add(val)

        # Record in run-wide aggregation
        fname = svg_path.name
        for v in color_drifts:
            self._drift_summary['colors'][v].add(fname)
        for v in font_drifts:
            self._drift_summary['fonts'][v].add(fname)
        for v in size_drifts:
            self._drift_summary['sizes'][v].add(fname)

        # Per-file warning (one condensed line; details live in summary)
        parts = []
        if color_drifts:
            parts.append(f"{len(color_drifts)} color(s)")
        if font_drifts:
            parts.append(f"{len(font_drifts)} font-family value(s)")
        if size_drifts:
            parts.append(f"{len(size_drifts)} font-size value(s)")
        if parts:
            result['warnings'].append(
                f"spec_lock drift: {', '.join(parts)} not in spec_lock.md "
                "(see drift summary for details)"
            )

    def _find_image_sources_manifest(self, svg_path: Path) -> Path | None:
        """Locate image_sources.json for a project SVG.

        Quality checks run primarily on <project>/svg_output/*.svg, but this
        also supports SVGs checked from project root or svg_final.
        """
        bases = (svg_path.parent, svg_path.parent.parent, svg_path.parent.parent.parent)
        for base in bases:
            candidate = base / 'images' / 'image_sources.json'
            if candidate.exists():
                return candidate
        return None

    def _load_image_sources_manifest(self, svg_path: Path) -> Dict:
        manifest_path = self._find_image_sources_manifest(svg_path)
        if manifest_path is None:
            return {}
        if manifest_path in self._source_manifest_cache:
            return self._source_manifest_cache[manifest_path]
        try:
            payload = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            payload = {}
        self._source_manifest_cache[manifest_path] = payload
        return payload

    def _check_sourced_image_attribution(self, content: str, svg_path: Path, result: Dict):
        """Require visible credit text for attribution-required web images.

        image_search.py records the legal tier in images/image_sources.json;
        Executor must render compact credit text into the SVG. This check
        prevents a quality-first CC BY / CC BY-SA image from silently reaching
        export without attribution.
        """
        manifest = self._load_image_sources_manifest(svg_path)
        items = manifest.get('items') or []
        if not items:
            return

        text_content = html.unescape(re.sub(r'<[^>]+>', ' ', content))
        text_content = re.sub(r'\s+', ' ', text_content)
        svg_stem = svg_path.stem

        for item in items:
            if not item.get('attribution_required') and item.get('license_tier') != 'attribution-required':
                continue

            filename = Path(str(item.get('filename') or '')).name
            slide = str(item.get('slide') or '').strip()
            referenced = bool(filename and filename in content)
            same_slide = bool(slide and slide == svg_stem)
            if not referenced and not same_slide:
                continue

            license_name = str(item.get('license_name') or '').upper()
            license_token = 'CC BY-SA' if 'BY-SA' in license_name else 'CC BY'
            has_credit = license_token in text_content.upper()
            if not has_credit:
                result['errors'].append(
                    f"Missing inline attribution for sourced image {filename or '(unknown)'} "
                    f"({license_token}). Add compact credit text per "
                    f"references/image-searcher.md §7."
                )

    @staticmethod
    def _normalize_size(value: str) -> str:
        """Normalize a font-size value for comparison: lowercase, strip spaces,
        strip trailing 'px'. Other units (em / rem / %) are kept as-is so that
        e.g. '1.5em' vs '24' stay distinct."""
        v = value.strip().lower()
        if v.endswith('px'):
            v = v[:-2].strip()
        return v

    def _categorize_issue(self, error_msg: str) -> str:
        """Categorize issue type"""
        if 'Invalid XML' in error_msg:
            return 'XML well-formedness'
        elif 'viewBox' in error_msg:
            return 'viewBox issues'
        elif 'foreignObject' in error_msg:
            return 'foreignObject'
        elif 'font' in error_msg.lower():
            return 'Font issues'
        else:
            return 'Other'

    def check_directory(self, directory: str, expected_format: str = None) -> List[Dict]:
        """
        Check all SVG files in a directory

        Args:
            directory: Directory path
            expected_format: Expected canvas format

        Returns:
            List of check results
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            print(f"[ERROR] Directory does not exist: {directory}")
            return []

        # Find all SVG files
        if dir_path.is_file():
            svg_files = [dir_path]
        else:
            if self.template_mode:
                # Template directories live at templates/layouts/<id>/.
                svg_files = sorted(dir_path.glob('*.svg'))
            else:
                svg_output = dir_path / \
                    'svg_output' if (
                        dir_path / 'svg_output').exists() else dir_path
                svg_files = sorted(svg_output.glob('*.svg'))

        if not svg_files:
            print(f"[WARN] No SVG files found")
            return []

        print(f"\n[SCAN] Checking {len(svg_files)} SVG file(s)...\n")

        for svg_file in svg_files:
            result = self.check_file(str(svg_file), expected_format)
            self._print_result(result)

        if self.template_mode and dir_path.is_dir():
            self._check_template_contract(dir_path, svg_files)
        elif dir_path.is_dir():
            self._check_animation_config_contract(dir_path)
            self._check_project_deck_contracts(dir_path, svg_files)

        return self.results

    def _check_project_deck_contracts(self, dir_path: Path, svg_files: List[Path]) -> None:
        """Project-level deck contract checks that need the full SVG set."""
        if not svg_files:
            return
        self._check_native_svg_source_safety(dir_path, svg_files)
        self._check_technicalroute_dual_output(svg_files)
        self._check_ai_image_assets_inserted(dir_path, svg_files)
        self._check_unique_page_numbers(svg_files)
        self._check_anchor_page_stacking(svg_files)
        self._check_summary_thanks_separation(svg_files)

    def _read_svg_text_for_project_check(self, svg_file: Path) -> tuple[str, str]:
        try:
            content = svg_file.read_text(encoding='utf-8')
        except OSError:
            return "", ""
        try:
            root = ET.fromstring(content)
            visible_text = " ".join("".join(elem.itertext()) for elem in root.iter())
            visible_text = " ".join(visible_text.split())
        except ET.ParseError:
            visible_text = re.sub(r'<[^>]+>', ' ', content)
            visible_text = " ".join(html.unescape(visible_text).split())
        return content, visible_text

    @staticmethod
    def _project_root_from_dir(dir_path: Path) -> Path:
        return dir_path if (dir_path / 'svg_output').exists() else dir_path.parent

    def _check_native_svg_source_safety(self, dir_path: Path, svg_files: List[Path]) -> None:
        """Block native export from SVGs that look like post-processed svg_final."""
        source_name = dir_path.name.lower() if dir_path.is_dir() else dir_path.parent.name.lower()
        pathified_counts: list[tuple[int, str]] = []
        transition_markers: list[str] = []
        for svg_file in svg_files:
            try:
                content = svg_file.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            path_count = len(re.findall(r'<path\b', content, re.IGNORECASE))
            rect_count = len(re.findall(r'<rect\b', content, re.IGNORECASE))
            line_count = len(re.findall(r'<line\b', content, re.IGNORECASE))
            if source_name == 'svg_final' and path_count > max(12, (rect_count + line_count) * 3):
                pathified_counts.append((path_count, svg_file.name))
            if re.search(r'data-slide-transition|<p:transition|transition\s*:', content, re.IGNORECASE):
                transition_markers.append(svg_file.name)

        if pathified_counts:
            pathified_counts.sort(reverse=True)
            sample = ", ".join(f"{name}:{count}" for count, name in pathified_counts[:5])
            self._project_issues.append((
                'error',
                'native_svg_final_pathified_source',
                "This directory looks like svg_final with pathified shapes. Do not export "
                "native DrawingML from svg_final; use svg_output so rounded rectangles and "
                f"lines remain preset DrawingML shapes. Worst files: {sample}."
            ))

        if source_name == 'svg_final' and transition_markers:
            self._project_issues.append((
                'error',
                'native_transition_risk',
                "svg_final contains transition markers. Native export should be regenerated "
                "from svg_output with -t none unless transitions were explicitly requested. "
                f"Files: {', '.join(transition_markers[:8])}."
            ))

    @staticmethod
    def _svg_viewbox_size(root: ET.Element) -> tuple[float, float]:
        viewbox = root.attrib.get('viewBox') or root.attrib.get('viewbox') or ""
        parts = viewbox.split()
        if len(parts) == 4:
            try:
                return float(parts[2]), float(parts[3])
            except ValueError:
                pass
        try:
            return float(root.attrib.get('width', '1280')), float(root.attrib.get('height', '720'))
        except ValueError:
            return 1280.0, 720.0

    @staticmethod
    def _attr_float(node: ET.Element, name: str, default: float = 0.0) -> float:
        raw = node.attrib.get(name)
        if raw is None:
            return default
        m = re.match(r"\s*([-+]?(?:\d*\.\d+|\d+\.?))", raw)
        if not m:
            return default
        try:
            return float(m.group(1))
        except ValueError:
            return default

    @staticmethod
    def _rect_overlap_ratio(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
        ax1, ay1, aw, ah = a
        bx1, by1, bw, bh = b
        ax2, ay2 = ax1 + aw, ay1 + ah
        bx2, by2 = bx1 + bw, by1 + bh
        overlap_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
        overlap_h = max(0.0, min(ay2, by2) - max(ay1, by1))
        overlap = overlap_w * overlap_h
        min_area = min(max(0.0, aw) * max(0.0, ah), max(0.0, bw) * max(0.0, bh))
        return overlap / min_area if min_area else 0.0

    def _check_ai_image_assets_inserted(self, dir_path: Path, svg_files: List[Path]) -> None:
        """Generated AI image files listed in project specs must appear in SVG pages."""
        project_root = self._project_root_from_dir(dir_path)
        spec_text = ""
        candidates = [project_root / 'spec_lock.md', project_root / 'design_spec.md']
        tech_root = project_root / 'technicalroute'
        if tech_root.exists():
            for candidate in tech_root.rglob('*'):
                if (
                    candidate.is_file()
                    and candidate.suffix.lower() in {'.md', '.yaml', '.yml', '.json', '.txt'}
                    and candidate.stat().st_size <= 1_000_000
                ):
                    candidates.append(candidate)
        for candidate in candidates:
            if candidate.exists():
                try:
                    spec_text += "\n" + candidate.read_text(encoding='utf-8')
                except OSError:
                    pass
        if not spec_text:
            return

        expected: set[str] = set()
        path_lines = list(re.finditer(r'\bpath\s*:\s*["\']?([^"\'\n|]+?\.(?:png|jpg|jpeg|webp))["\']?', spec_text, re.IGNORECASE))
        for match in path_lines:
            start = max(0, match.start() - 240)
            end = min(len(spec_text), match.end() + 240)
            context = spec_text[start:end].lower()
            if any(token in context for token in ('technicalroute_ai_png', 'ai_supporting_image', 'route_ai_', 'acquire via | ai', 'acquire via: ai', ' ai |')):
                expected.add(match.group(1).strip())
        for match in re.finditer(r'([A-Za-z0-9_./\\-]*(?:route_ai|ai_[A-Za-z0-9_-]+)[A-Za-z0-9_./\\-]*\.(?:png|jpg|jpeg|webp))', spec_text, re.IGNORECASE):
            expected.add(match.group(1).strip())
        for match in re.finditer(
            r'\broute_ai_image_path\s*[:=]\s*["\']?([^"\'\n|]+?\.(?:png|jpg|jpeg|webp))["\']?',
            spec_text,
            re.IGNORECASE,
        ):
            expected.add(match.group(1).strip())
        if tech_root.exists():
            for image in tech_root.rglob('*'):
                if image.is_file() and re.match(r'route_ai.*\.(?:png|jpg|jpeg|webp)$', image.name, re.IGNORECASE):
                    try:
                        expected.add(str(image.resolve().relative_to(project_root.resolve())))
                    except ValueError:
                        expected.add(str(image.resolve()))

        if not expected:
            return

        combined_svg = "\n".join(svg.read_text(encoding='utf-8', errors='replace') for svg in svg_files if svg.exists())
        combined_lower = combined_svg.lower()
        has_embedded_route_slide = (
            'id="technicalroute-ai-reference-image"' in combined_lower
            or "id='technicalroute-ai-reference-image'" in combined_lower
        ) and 'data:image/png;base64,' in combined_lower
        for raw_path in sorted(expected):
            normalized = raw_path.replace("\\", "/").strip()
            basename = Path(normalized).name
            if not basename:
                continue
            asset_path = (project_root / normalized).resolve()
            if not asset_path.exists():
                direct_path = Path(raw_path).expanduser()
                if direct_path.is_absolute() and direct_path.exists():
                    asset_path = direct_path.resolve()
                else:
                    self._project_issues.append((
                        'error',
                        'ai_image_missing_on_disk',
                        f"{basename}: spec/design declares an AI image path, but the file does not exist. "
                        "Run the AI image generation step and verify route_ai_image_path before creating PPTX."
                    ))
                    continue
            is_route_ai = 'route_ai' in basename.lower() or 'route_ai_image_path' in raw_path.lower()
            if is_route_ai and not has_embedded_route_slide:
                self._project_issues.append((
                    'error',
                    'technicalroute_ai_slide_missing',
                    f"{basename}: route_ai_image_path exists, but no SVG page embeds it as "
                    "<image id=\"technicalroute-ai-reference-image\" href=\"data:image/png;base64,...\">. "
                    "Run generate_route_image.py create-ai-slide and insert it as the next slide after Version A."
                ))
                continue
            stem = Path(basename).stem.lower()
            if (
                basename.lower() not in combined_lower
                and normalized.lower() not in combined_lower
                and f'data-ai-image-source="{basename.lower()}"' not in combined_lower
                and f"data-ai-image-source='{basename.lower()}'" not in combined_lower
                and f'data-ai-image-source="{stem}' not in combined_lower
                and f"data-ai-image-source='{stem}" not in combined_lower
            ):
                self._project_issues.append((
                    'error',
                    'ai_image_not_inserted',
                    f"{basename}: AI-generated image exists and is listed in spec/design files, "
                    "but no SVG page references it. Insert it with <image ...> or an embedded data URI "
                    "tagged with data-ai-image-source."
                ))

    def _check_unique_page_numbers(self, svg_files: List[Path]) -> None:
        """Only one visible page-number object may appear on each slide."""
        svg_ns = "{http://www.w3.org/2000/svg}"
        for svg_file in svg_files:
            content, _visible_text = self._read_svg_text_for_project_check(svg_file)
            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                continue
            width, height = self._svg_viewbox_size(root)
            candidates: list[str] = []
            for node in root.iter():
                if node.tag != f"{svg_ns}text":
                    continue
                text = " ".join("".join(node.itertext()).split())
                if not text:
                    continue
                x = self._attr_float(node, 'x')
                y = self._attr_float(node, 'y')
                fs = self._attr_float(node, 'font-size', 14.0)
                marker_attrs = " ".join(str(node.attrib.get(k, "")) for k in ('id', 'data-role', 'data-page-number')).lower()
                role_marker = any(token in marker_attrs for token in ('page-number', 'pagenum', 'page_num', 'sldnum'))
                numeric_marker = re.fullmatch(r'\d{1,2}(?:\s*/\s*\d{1,2})?', text) is not None
                footer_position = y >= height * 0.82 or x >= width * 0.78
                if role_marker or (numeric_marker and footer_position and fs <= 20):
                    candidates.append(text)
                repeated = re.fullmatch(r'(\d{1,2})\s+\1', text)
                if repeated and footer_position:
                    candidates.extend([repeated.group(1), repeated.group(1)])
            if len(candidates) > 1:
                self._project_issues.append((
                    'error',
                    'duplicate_page_number',
                    f"{svg_file.name}: detected multiple page-number candidates ({', '.join(candidates[:4])}). "
                    "Keep exactly one page number; in user-template mode use the slide/layout/master sldNum slot."
                ))

    def _check_anchor_page_stacking(self, svg_files: List[Path]) -> None:
        """First and last slides should not contain stacked large pictures/shapes."""
        if len(svg_files) < 2:
            return
        svg_ns = "{http://www.w3.org/2000/svg}"
        for svg_file in (svg_files[0], svg_files[-1]):
            content, _visible_text = self._read_svg_text_for_project_check(svg_file)
            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                continue
            width, height = self._svg_viewbox_size(root)
            slide_area = max(1.0, width * height)
            images: list[tuple[str, tuple[float, float, float, float]]] = []
            large_rects: list[tuple[str, tuple[float, float, float, float]]] = []
            for node in root.iter():
                tag = node.tag
                if tag == f"{svg_ns}image":
                    box = (
                        self._attr_float(node, 'x'),
                        self._attr_float(node, 'y'),
                        self._attr_float(node, 'width'),
                        self._attr_float(node, 'height'),
                    )
                    if box[2] * box[3] >= slide_area * 0.20:
                        images.append((node.attrib.get('id', 'image'), box))
                elif tag == f"{svg_ns}rect":
                    box = (
                        self._attr_float(node, 'x'),
                        self._attr_float(node, 'y'),
                        self._attr_float(node, 'width'),
                        self._attr_float(node, 'height'),
                    )
                    if box[2] * box[3] < slide_area * 0.20:
                        continue
                    elem_id = node.attrib.get('id', '').lower()
                    fill = (node.attrib.get('fill') or '').lower()
                    opacity = self._attr_float(node, 'fill-opacity', self._attr_float(node, 'opacity', 1.0))
                    is_background = box[0] <= 1 and box[1] <= 1 and box[2] >= width - 2 and box[3] >= height - 2
                    is_overlay = any(token in elem_id for token in ('overlay', 'scrim', 'shade', 'header', 'footer', 'background', 'bg'))
                    if is_background or is_overlay or opacity < 0.95:
                        continue
                    if fill in {'#fff', '#ffffff', 'white', '#f7f7f7', '#f8f8f8', '#f9f9f9'}:
                        large_rects.append((node.attrib.get('id', 'rect'), box))
            for left_i, (left_name, left_box) in enumerate(images):
                for right_name, right_box in images[left_i + 1:]:
                    if self._rect_overlap_ratio(left_box, right_box) >= 0.20:
                        self._project_issues.append((
                            'error',
                            'anchor_page_image_stack',
                            f"{svg_file.name}: first/last slide has overlapping large images ({left_name}, {right_name}). "
                            "Cover and thank-you pages should use one dominant visual layer."
                        ))
            for image_name, image_box in images:
                for rect_name, rect_box in large_rects:
                    if self._rect_overlap_ratio(image_box, rect_box) >= 0.35:
                        self._project_issues.append((
                            'error',
                            'anchor_page_blank_shape_stack',
                            f"{svg_file.name}: first/last slide has a large image overlapped by a large blank shape ({image_name}, {rect_name}). "
                            "Remove the empty frame or use an intentional text overlay marked as overlay/scrim."
                        ))

    def _check_technicalroute_dual_output(self, svg_files: List[Path]) -> None:
        """Require every TechnicalRoute editable page to have a consecutive AI page."""
        infos: list[dict] = []
        for idx, svg_file in enumerate(svg_files):
            content, visible_text = self._read_svg_text_for_project_check(svg_file)
            lower = content.lower()
            text_lower = visible_text.lower()
            name_lower = svg_file.name.lower()
            explicit_template = any(token in lower or token in text_lower or token in name_lower for token in (
                'route_template',
                'editable template version',
                'data-route-version="a"',
                "data-route-version='a'",
                'technicalroute-template',
            ))
            route_page_marker = any(token in lower or token in text_lower or token in name_lower for token in (
                'technical_route',
                'technical-route',
                'research_route',
                'research-route',
                'method_route',
                'method-route',
                'whole_paper_workflow',
                'full-paper route',
                'full paper route',
                '技术路线',
                '技術路線',
                '全文技术路线',
                '全文技術路線',
                '研究路线',
                '研究路線',
            ))
            is_ai = any(token in lower or token in text_lower or token in name_lower for token in (
                'technicalroute-ai-reference-image',
                'route_ai',
                'ai reference version',
                'data-route-version="b"',
                "data-route-version='b'",
                'data-route-source="ai-reference"',
                "data-route-source='ai-reference'",
            ))
            is_template = (explicit_template or route_page_marker) and not is_ai
            template_and_ai_on_same_slide = explicit_template and is_ai
            if template_and_ai_on_same_slide:
                self._project_issues.append((
                    'error',
                    'technicalroute_versions_same_slide',
                    f"{svg_file.name}: TechnicalRoute Version A editable diagram and Version B AI PNG "
                    "must be separate consecutive slides, not two visuals on one slide."
                ))
            if is_ai:
                is_template = False
            infos.append({
                'idx': idx,
                'file': svg_file,
                'content': content,
                'lower': lower,
                'is_template': is_template,
                'is_ai': is_ai,
            })

        template_infos = [info for info in infos if info['is_template']]
        ai_infos = [info for info in infos if info['is_ai']]
        if not template_infos and not ai_infos:
            return
        if template_infos and not ai_infos:
            self._project_issues.append((
                'error',
                'technicalroute_missing_ai_page',
                "TechnicalRoute editable template page exists, but no Version B AI reference slide was found. "
                "Run generate_route_image.py run-ai-variant, verify route_ai_image_path, then run create-ai-slide."
            ))
            return

        for ai in ai_infos:
            image_tag = re.search(
                r'<image\b(?=[^>]*\bid\s*=\s*["\']technicalroute-ai-reference-image["\'])[^>]*>',
                ai['content'],
                flags=re.IGNORECASE | re.DOTALL,
            )
            href_match = None
            if image_tag:
                href_match = re.search(
                    r'(?:href|xlink:href)\s*=\s*["\']([^"\']+)["\']',
                    image_tag.group(0),
                    flags=re.IGNORECASE | re.DOTALL,
                )
            href = html.unescape(href_match.group(1)) if href_match else ""
            if not href.startswith('data:image/png;base64,'):
                self._project_issues.append((
                    'error',
                    'technicalroute_ai_not_embedded',
                    f"{ai['file'].name}: Version B route slide must embed PNG bytes with "
                    "<image id=\"technicalroute-ai-reference-image\" href=\"data:image/png;base64,...\">. "
                    "External or relative image href links are forbidden."
                ))
                continue
            payload = href.split(',', 1)[1]
            try:
                image_bytes = base64.b64decode(payload, validate=True)
            except Exception:
                self._project_issues.append((
                    'error',
                    'technicalroute_ai_invalid_png_data',
                    f"{ai['file'].name}: Version B route slide has invalid base64 image data."
                ))
                continue
            if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
                self._project_issues.append((
                    'error',
                    'technicalroute_ai_invalid_png_data',
                    f"{ai['file'].name}: Version B route slide data URI is not PNG bytes."
                ))

        ai_indices = {ai['idx'] for ai in ai_infos}
        for template in template_infos:
            if template['idx'] + 1 not in ai_indices:
                self._project_issues.append((
                    'error',
                    'technicalroute_not_consecutive',
                    f"{template['file'].name}: TechnicalRoute Version B AI reference slide must be the next SVG page."
                ))

    def _check_summary_thanks_separation(self, svg_files: List[Path]) -> None:
        """Prevent combining the summary page and thank-you/Q&A page."""
        summary_terms = ("\u603b\u7ed3", "summary", "conclusion", "outlook")
        thanks_terms = ("\u8c22\u8c22", "thank you", "thanks", "q&a", "questions")
        for svg_file in svg_files:
            _content, visible_text = self._read_svg_text_for_project_check(svg_file)
            text_lower = visible_text.lower()
            has_summary = any(term in text_lower or term in visible_text for term in summary_terms)
            has_thanks = any(term in text_lower or term in visible_text for term in thanks_terms)
            if has_summary and has_thanks:
                self._project_issues.append((
                    'error',
                    'summary_thanks_combined',
                    f"{svg_file.name}: summary/conclusion content and thank-you/Q&A content are on the same slide. "
                    "Create a standalone summary page and a separate final thank-you/Q&A page."
                ))

    def _check_animation_config_contract(self, dir_path: Path) -> None:
        """Project-level animations.json reference checks."""
        if _load_animation_config is None or _validate_animation_config is None:
            return
        project_path = dir_path if (dir_path / 'svg_output').exists() else dir_path.parent
        try:
            config = _load_animation_config(project_path)
        except Exception as exc:
            self._animation_issues.append(('error', f"animations.json is invalid: {exc}"))
            return
        if not config:
            return
        for warning in _validate_animation_config(project_path, config):
            self._animation_issues.append(('warning', warning))

    def _check_template_contract(self, dir_path: Path,
                                 svg_files: List[Path]) -> None:
        """Template-mode-only checks: roster ↔ design_spec consistency and
        per-page placeholder hints.

        - **Roster mismatch (orphan / missing)** is reported as an *error*: a
          stale roster will produce a wrong ``layouts_index.json`` entry.
        - **Placeholder gaps** are reported as *warnings*. Templates may
          legitimately omit conventional placeholders or swap them out (e.g.
          ``{{CLOSING_MESSAGE}}`` instead of ``{{THANK_YOU}}``), and a content
          variant may use a bespoke slot vocabulary. Designers can declare
          their own per-stem expectations via ``placeholders:`` frontmatter
          in ``design_spec.md`` to suppress these warnings explicitly.

        Issues are aggregated and printed in :py:meth:`print_summary` so the
        per-file report stays focused on intrinsic SVG validity.
        """
        spec_path = dir_path / 'design_spec.md'
        spec_text = spec_path.read_text(encoding='utf-8') if spec_path.exists() else ""
        spec_pages = self._extract_spec_roster(spec_text) if spec_text else []
        custom_contract = self._extract_frontmatter_placeholders(spec_text) if spec_text else {}

        on_disk = {p.stem for p in svg_files}

        if spec_pages:
            spec_set = set(spec_pages)
            orphan = sorted(on_disk - spec_set)
            missing = sorted(spec_set - on_disk)
            for page in orphan:
                self._template_issues.append((
                    'error',
                    'roster_orphan',
                    f"{page}.svg exists on disk but is not listed in design_spec.md Page Roster",
                ))
            for page in missing:
                self._template_issues.append((
                    'error',
                    'roster_missing',
                    f"design_spec.md Page Roster lists {page} but {page}.svg is missing on disk",
                ))
        elif spec_path.exists():
            # design_spec.md is present but the roster parser found nothing —
            # surface as a warning. Legacy specs may lack an explicit roster.
            self._template_issues.append((
                'warning',
                'roster_unknown',
                f"could not extract page roster from {spec_path.name}; "
                "skipping orphan/missing checks",
            ))
        else:
            self._template_issues.append((
                'error',
                'spec_missing',
                f"{spec_path.name} not found — required for every library template",
            ))

        # Per-file placeholder coverage. Variants reuse the parent type's set
        # (e.g. 03a_content_two_col.svg ↔ 03_content rules) unless the spec
        # frontmatter overrides that page (custom_contract takes precedence).
        for svg_file in svg_files:
            expected = self._lookup_template_contract(
                svg_file.stem, overrides=custom_contract,
            )
            if expected is None:
                continue  # extension pages or stems with no convention
            try:
                content = svg_file.read_text(encoding='utf-8')
            except OSError:
                continue
            for placeholder in expected:
                if placeholder not in content:
                    self._template_issues.append((
                        'warning',
                        'placeholder_hint',
                        f"{svg_file.name}: missing conventional placeholder {placeholder} "
                        "(declare 'placeholders:' frontmatter in design_spec.md to silence)",
                    ))

    @staticmethod
    def _extract_frontmatter_placeholders(spec_text: str) -> Dict[str, Tuple[str, ...]]:
        """Read the optional ``placeholders:`` map from design_spec.md frontmatter.

        Shape:

        .. code-block:: yaml

            placeholders:
              01_cover: ["{{TITLE}}", "{{BRAND_LOGO}}"]
              03_content: []        # explicitly assert "no expectation"
              03a_content_two_col:  # variant-specific override
                - "{{LEFT_TITLE}}"
                - "{{RIGHT_TITLE}}"

        Each key is a stem (full filename without ``.svg``) or page-type prefix
        (``01_cover``). An empty list silences the default convention for that
        stem; a populated list replaces the default. Stems / prefixes not
        listed fall back to ``DEFAULT_PLACEHOLDER_CONVENTION``.

        We parse with PyYAML when available; otherwise we fall back to a
        minimal regex that handles the documented shape.
        """
        if not spec_text.startswith("---\n"):
            return {}
        end = spec_text.find("\n---\n", 4)
        if end == -1:
            return {}
        block = spec_text[4:end]

        try:
            import yaml  # type: ignore
        except ImportError:
            return _parse_placeholders_fallback(block)

        try:
            data = yaml.safe_load(block) or {}
        except yaml.YAMLError:
            return {}
        if not isinstance(data, dict):
            return {}
        raw = data.get("placeholders")
        if not isinstance(raw, dict):
            return {}

        out: Dict[str, Tuple[str, ...]] = {}
        for stem, value in raw.items():
            if not isinstance(stem, str):
                continue
            if isinstance(value, list):
                out[stem] = tuple(str(v) for v in value)
            elif value is None:
                out[stem] = ()
        return out

    @staticmethod
    def _extract_spec_roster(spec_text: str) -> List[str]:
        """Best-effort: extract the page roster from design_spec.md.

        Templates do not share a uniform section index for the roster — the
        personality-only skeleton puts it at §V "Page Roster"; legacy specs use
        §VI "Page Roster" or bury filenames under §VII "Page Types" as
        ``### N. Cover Page (01_cover.svg)``. We match by title (any roman
        index), then fall back to scanning the whole document for any
        backtick-wrapped ``<stem>.svg`` reference.

        Returns the deduplicated stem list in document order. Empty result
        means we can't determine the roster confidently — caller should treat
        that as "skip orphan/missing checks", not as "no pages declared".
        """
        # Pass 1: explicit roster section, any roman numeral.
        section = re.search(
            r"^##\s+[IVX]+\.\s+(?:Page Roster|Page Structure|Pages|Page Types)\b.*?(?=^##\s+|\Z)",
            spec_text,
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        scope = section.group(0) if section else None

        # Pass 2: full document. We *only* trust this scan when the explicit
        # roster scan came up empty (no `<stem>.svg` references inside it) —
        # otherwise the explicit section's deliberate roster wins over loose
        # mentions elsewhere.
        if scope and re.search(r"[`\(][0-9A-Za-z_]+\.svg[`\)]", scope):
            text = scope
        else:
            text = spec_text

        stems: List[str] = []
        seen: set = set()
        # Accept backtick-quoted (`01_cover.svg`) and parenthesized
        # (01_cover.svg) forms — existing specs use either.
        svg_ref_re = re.compile(r"[`\(]([0-9A-Za-z_]+\.svg)[`\)]")
        for match in svg_ref_re.finditer(text):
            stem = match.group(1)[:-4]
            if stem in seen or not re.match(r"^\d", stem):
                continue
            seen.add(stem)
            stems.append(stem)

        # If the explicit §VI scan listed bare stems (without .svg), accept
        # those as fallback — but only when they were inside that section.
        if not stems and scope:
            for match in re.finditer(r"`([0-9]{2}[a-z]?_[A-Za-z0-9_]+)`", scope):
                stem = match.group(1)
                if stem in seen:
                    continue
                seen.add(stem)
                stems.append(stem)

        return stems

    @classmethod
    def _lookup_template_contract(
        cls, stem: str, *,
        overrides: Dict[str, Tuple[str, ...]] | None = None,
    ) -> Tuple[str, ...] | None:
        """Resolve a SVG stem to its expected placeholder set.

        Resolution order, first hit wins:
        1. ``overrides[stem]`` — frontmatter entry for the exact filename
        2. ``overrides[<page_type_prefix>]`` — frontmatter entry for the
           variant's parent type (e.g. ``03_content`` for
           ``03a_content_two_col``)
        3. ``DEFAULT_PLACEHOLDER_CONVENTION[<page_type_prefix>]``

        Returns ``None`` for stems with no matching convention or override —
        e.g. extension pages like ``05_section_break``. ``()`` (empty tuple)
        is a valid value meaning "no expected placeholders" — used to
        explicitly silence the default convention.
        """
        overrides = overrides or {}
        if stem in overrides:
            return overrides[stem]

        # Variant convention: <NN><letter>?_<rest>; strip the letter to find
        # the parent type prefix, e.g. "03a_content_two_col" -> "03_content".
        match = re.match(r"^(\d{2})([a-z])?_([a-z]+)", stem)
        if not match:
            return None
        num, _letter, kind = match.groups()
        key = f"{num}_{kind}"
        if key in overrides:
            return overrides[key]
        return cls.DEFAULT_PLACEHOLDER_CONVENTION.get(key)

    def _print_result(self, result: Dict):
        """Print check result for a single file"""
        if result['passed']:
            if result['warnings']:
                icon = "[WARN]"
                status = "Passed (with warnings)"
            else:
                icon = "[OK]"
                status = "Passed"
        else:
            icon = "[ERROR]"
            status = "Failed"

        print(f"{icon} {result['file']} - {status}")

        # Display basic info
        if result['info']:
            info_items = []
            if 'viewbox' in result['info']:
                info_items.append(f"viewBox: {result['info']['viewbox']}")
            if info_items:
                print(f"   {' | '.join(info_items)}")

        # Display errors
        if result['errors']:
            for error in result['errors']:
                print(f"   [ERROR] {error}")

        # Display warnings
        if result['warnings']:
            for warning in result['warnings'][:2]:  # Only show first 2 warnings
                print(f"   [WARN] {warning}")
            if len(result['warnings']) > 2:
                print(f"   ... and {len(result['warnings']) - 2} more warning(s)")

        print()

    def print_summary(self):
        """Print check summary"""
        # Aggregate project-level checks before printing totals so the summary
        # reflects deck-wide contracts, not only per-file SVG validity.
        self._print_drift_summary()
        self._print_template_summary()
        self._print_animation_summary()
        self._print_project_summary()

        print("=" * 80)
        print("[SUMMARY] Check Summary")
        print("=" * 80)

        print(f"\nTotal files: {self.summary['total']}")
        print(
            f"  [OK] Fully passed: {self.summary['passed']} ({self._percentage(self.summary['passed'])}%)")
        print(
            f"  [WARN] With warnings: {self.summary['warnings']} ({self._percentage(self.summary['warnings'])}%)")
        print(
            f"  [ERROR] With errors: {self.summary['errors']} ({self._percentage(self.summary['errors'])}%)")

        if self.issue_types:
            print(f"\nIssue categories:")
            for issue_type, count in sorted(self.issue_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {issue_type}: {count}")

        # Fix suggestions
        if self.summary['errors'] > 0 or self.summary['warnings'] > 0:
            print(f"\n[TIP] Common fixes:")
            print(f"  1. XML well-formedness: write typography as raw Unicode (—, ©, →, NBSP); escape XML reserved chars as &amp; &lt; &gt; &quot; &apos; — never use HTML named entities like &nbsp; &mdash; &copy;")
            print(f"  2. viewBox issues: Ensure consistency with canvas format (see references/canvas-formats.md)")
            print(f"  3. foreignObject: Use <text> + <tspan> for manual line breaks")
            print(f"  4. Font issues: end every font-family stack with a PPT-safe family (e.g. Microsoft YaHei / Arial / Consolas)")

    def _print_project_summary(self):
        """Print project-level deck contract issues."""
        if not self._project_issues:
            return

        errors = [item for item in self._project_issues if item[0] == 'error']
        warnings = [item for item in self._project_issues if item[0] == 'warning']
        self.summary['errors'] += len(errors)
        self.summary['warnings'] += len(warnings)
        for severity, kind, _msg in self._project_issues:
            self.issue_types[f'project_{kind}_{severity}'] += 1

        print("\n[PROJECT] Deck contract checks")
        for _severity, kind, msg in errors:
            print(f"  [ERROR] [{kind}] {msg}")
        for _severity, kind, msg in warnings:
            print(f"  [WARN] [{kind}] {msg}")
    def _print_animation_summary(self):
        """Print animations.json validation issues if present."""
        if not self._animation_issues:
            return

        errors = [item for item in self._animation_issues if item[0] == 'error']
        warnings = [item for item in self._animation_issues if item[0] == 'warning']
        self.summary['errors'] += len(errors)
        self.summary['warnings'] += len(warnings)
        for severity, _msg in self._animation_issues:
            self.issue_types[f'animation_config_{severity}'] += 1

        print("\n[ANIMATION] animations.json checks")
        for _severity, msg in errors:
            print(f"  [ERROR] {msg}")
        for _severity, msg in warnings:
            print(f"  [WARN] {msg}")

    def _print_template_summary(self):
        """Aggregate template-mode roster / placeholder issues at the bottom.

        Errors land under the ``errors`` summary count (so the exit signal
        from ``main`` agrees), warnings under ``warnings``. Both are listed
        per file so the user can act on them directly.
        """
        if not self._template_issues:
            return

        errors = [item for item in self._template_issues if item[0] == 'error']
        warnings = [item for item in self._template_issues if item[0] == 'warning']

        # Mirror into the global summary so downstream "0 errors" gates honor
        # template-mode issues.
        self.summary['errors'] += len(errors)
        self.summary['warnings'] += len(warnings)
        for severity, kind, _msg in self._template_issues:
            self.issue_types[f"template_{kind}"] += 1

        print("\n[TEMPLATE] Template mode checks")
        if errors:
            print(f"  Errors ({len(errors)}):")
            for _sev, kind, msg in errors:
                print(f"    [{kind}] {msg}")
        if warnings:
            print(f"  Warnings ({len(warnings)}):")
            for _sev, kind, msg in warnings:
                print(f"    [{kind}] {msg}")
        if not errors:
            print("  No structural roster issues. Placeholder hints above are advisory only;")
            print("  declare 'placeholders:' frontmatter in design_spec.md to silence them.")

    def _print_drift_summary(self):
        """Print spec_lock drift aggregation if any was observed.

        Values are sorted by file-count descending so frequent drift surfaces
        first. Frequent drift usually means spec_lock.md is missing entries
        the Strategist should have included; rare drift is more likely actual
        Executor drift and warrants SVG review.
        """
        if not self._lock_seen:
            return
        has_drift = any(self._drift_summary[cat] for cat in self._drift_summary)
        if not has_drift:
            print("\n[OK] spec_lock drift: none — all colors, fonts, and sizes are anchored to spec_lock.md")
            return

        print("\nspec_lock drift — values used outside spec_lock.md:")
        labels = [('colors', 'Colors'),
                  ('fonts', 'Font families'),
                  ('sizes', 'Font sizes')]
        for category, label in labels:
            items = self._drift_summary.get(category, {})
            if not items:
                continue
            entries = sorted(items.items(), key=lambda x: (-len(x[1]), x[0]))
            print(f"  {label}:")
            for val, files in entries:
                n = len(files)
                suffix = "file" if n == 1 else "files"
                print(f"    {val}  ({n} {suffix})")
        print(
            "Tip: frequent out-of-lock values usually mean spec_lock.md is missing\n"
            "     entries — extend the lock (scripts/update_spec.py or manual edit).\n"
            "     Rare ones are likely Executor drift — review the affected SVGs."
        )

    def _percentage(self, count: int) -> int:
        """Calculate file-level percentage, capped when deck-level issues are added."""
        if self.summary['total'] == 0:
            return 0
        return min(100, int(count / self.summary['total'] * 100))

    def export_report(self, output_file: str = 'svg_quality_report.txt'):
        """Export check report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("PPT Master SVG Quality Check Report\n")
            f.write("=" * 80 + "\n\n")

            for result in self.results:
                status = "[OK] Passed" if result['passed'] else "[ERROR] Failed"
                f.write(f"{status} - {result['file']}\n")
                f.write(f"Path: {result.get('path', 'N/A')}\n")

                if result['info']:
                    f.write(f"Info: {result['info']}\n")

                if result['errors']:
                    f.write(f"\nErrors:\n")
                    for error in result['errors']:
                        f.write(f"  - {error}\n")

                if result['warnings']:
                    f.write(f"\nWarnings:\n")
                    for warning in result['warnings']:
                        f.write(f"  - {warning}\n")

                f.write("\n" + "-" * 80 + "\n\n")

            # Write summary
            f.write("\n" + "=" * 80 + "\n")
            f.write("Check Summary\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total files: {self.summary['total']}\n")
            f.write(f"Fully passed: {self.summary['passed']}\n")
            f.write(f"With warnings: {self.summary['warnings']}\n")
            f.write(f"With errors: {self.summary['errors']}\n")

        print(f"\n[REPORT] Check report exported: {output_file}")


def print_usage() -> None:
    """Print CLI usage information."""
    print("PPT Master - SVG Quality Check Tool\n")
    print("Usage:")
    print("  python3 scripts/svg_quality_checker.py <svg_file>")
    print("  python3 scripts/svg_quality_checker.py <directory>")
    print("  python3 scripts/svg_quality_checker.py <template_dir> --template-mode")
    print("  python3 scripts/svg_quality_checker.py --all examples")
    print("\nExamples:")
    print("  python3 scripts/svg_quality_checker.py examples/project/svg_output/slide_01.svg")
    print("  python3 scripts/svg_quality_checker.py examples/project/svg_output")
    print("  python3 scripts/svg_quality_checker.py examples/project")
    print("  python3 scripts/svg_quality_checker.py templates/layouts/anthropic --template-mode")
    print("\nOptions:")
    print("  --format <ppt169|ppt43|...>   Expected canvas format")
    print("  --template-mode               Validate a templates/layouts/<id> directory:")
    print("                                  glob *.svg directly, skip spec_lock checks,")
    print("                                  enforce roster ↔ design_spec.md Page Roster consistency,")
    print("                                  and emit advisory placeholder-convention warnings.")


def main() -> None:
    """Run the CLI entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    if sys.argv[1] in {"-h", "--help", "help"}:
        print_usage()
        sys.exit(0)

    if sys.argv[1].startswith("--") and sys.argv[1] not in {"--all"}:
        print(f"[ERROR] Missing target before option: {sys.argv[1]}")
        print_usage()
        sys.exit(1)

    template_mode = '--template-mode' in sys.argv
    checker = SVGQualityChecker(template_mode=template_mode)

    # Parse arguments
    target = sys.argv[1]
    expected_format = None

    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            expected_format = sys.argv[idx + 1]

    # Execute check
    if target == '--all':
        # Check all example projects
        base_dir = sys.argv[2] if len(sys.argv) > 2 else 'examples'
        from project_utils import find_all_projects
        projects = find_all_projects(base_dir)

        for project in projects:
            print(f"\n{'=' * 80}")
            print(f"Checking project: {project.name}")
            print('=' * 80)
            checker.check_directory(str(project))
    else:
        checker.check_directory(target, expected_format)

    # Print summary
    checker.print_summary()

    # Export report (if specified)
    if '--export' in sys.argv:
        output_file = 'svg_quality_report.txt'
        if '--output' in sys.argv:
            idx = sys.argv.index('--output')
            if idx + 1 < len(sys.argv):
                output_file = sys.argv[idx + 1]
        checker.export_report(output_file)

    # Return exit code
    if checker.summary['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

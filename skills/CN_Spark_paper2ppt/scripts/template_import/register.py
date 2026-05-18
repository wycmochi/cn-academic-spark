#!/usr/bin/env python3
"""Register a layout template into the global template index.

Reads ``templates/layouts/<template_id>/design_spec.md`` (preferring its YAML
frontmatter when present, falling back to prose section values) and
synchronizes two derived indexes:

- ``templates/layouts/layouts_index.json`` — slim machine-readable map
- ``templates/layouts/README.md`` — human-facing "Quick Template Index" table

This script is the single source-of-truth bridge between a template's design
spec and the indexes. Run it after creating a new template (or after editing a
spec) and the indexes update automatically — no manual JSON / Markdown surgery.

Usage:
    python3 scripts/template_import/register.py <template_id>
    python3 scripts/template_import/register.py <template_id> --dry-run
    python3 scripts/template_import/register.py --rebuild-all

The last form rebuilds every entry from scratch, which is the recommended way
to repair index drift across many templates at once.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover — yaml is part of stdlib-adjacent deps
    yaml = None


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent.parent
LAYOUTS_DIR = SKILL_DIR / "templates" / "layouts"
INDEX_PATH = LAYOUTS_DIR / "layouts_index.json"
README_PATH = LAYOUTS_DIR / "README.md"

QUICK_INDEX_BEGIN = "<!-- quick-index:begin -->"
QUICK_INDEX_END = "<!-- quick-index:end -->"


def _print_text(text: str = "") -> None:
    """Print Unicode safely on Windows terminals with legacy encodings."""
    try:
        print(text)
    except UnicodeEncodeError:
        data = text.encode(sys.stdout.encoding or "utf-8", errors="backslashreplace")
        sys.stdout.buffer.write(data + b"\n")


# ---------------------------------------------------------------------------
# design_spec.md parsing
# ---------------------------------------------------------------------------

class SpecParseError(RuntimeError):
    """Raised when a design_spec.md cannot be turned into an index entry."""


def _read_spec(spec_path: Path) -> tuple[dict | None, str]:
    """Split YAML frontmatter from the body. Returns ``(frontmatter, body)``."""
    text = spec_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text

    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text

    fm_block = text[4:end]
    body = text[end + 5:]
    if yaml is None:
        raise SpecParseError(
            "design_spec.md has YAML frontmatter but PyYAML is not installed; "
            "install pyyaml or remove the frontmatter."
        )
    try:
        data = yaml.safe_load(fm_block) or {}
    except yaml.YAMLError as exc:
        raise SpecParseError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise SpecParseError("YAML frontmatter must be a mapping")
    return data, body


def _extract_section_field(body: str, section_title: str, labels: list[str]) -> str | None:
    """Find a field within the named section.

    Tolerates two layouts the existing specs use:

    1. Markdown table row: ``| **Label** | value |``
    2. Bullet list: ``- **Label**: value``

    Tries each label variant in order. Returns the first match or ``None``.
    """
    section_re = re.compile(
        rf"^##\s+{re.escape(section_title)}\b.*?(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    section_match = section_re.search(body)
    if section_match is None:
        return None
    section = section_match.group(0)

    for label in labels:
        # Table form
        row = re.search(
            rf"^\|\s*\*?\*?{re.escape(label)}\*?\*?\s*\|\s*(.+?)\s*\|",
            section,
            re.MULTILINE | re.IGNORECASE,
        )
        if row:
            return _clean_field_value(row.group(1))

        # Bullet form
        bullet = re.search(
            rf"^[-*]\s*\*?\*?{re.escape(label)}\*?\*?\s*[:：]\s*(.+?)\s*$",
            section,
            re.MULTILINE | re.IGNORECASE,
        )
        if bullet:
            return _clean_field_value(bullet.group(1))
    return None


def _clean_field_value(value: str) -> str:
    """Strip surrounding markdown decorations from an extracted field value."""
    value = value.strip()
    # Drop wrapping backticks / asterisks / underscores.
    value = re.sub(r"^[`*_]+", "", value)
    value = re.sub(r"[`*_]+$", "", value)
    return value.strip()


def _find_first_color(section: str) -> str | None:
    match = re.search(r"`(#[0-9A-Fa-f]{3,8})`", section)
    return match.group(1).upper() if match else None


def _normalize_hex(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip().lstrip("#").upper()
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if not re.fullmatch(r"[0-9A-F]{6}", raw):
        return None
    return f"#{raw}"


def _extract_primary_color(body: str) -> str | None:
    """Pull the first hex color out of the Color Scheme section (any roman index)."""
    section_match = re.search(
        r"^##\s+[IVX]+\.\s+Color Scheme\b.*?(?=^##\s+|\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    if section_match is None:
        return None
    return _find_first_color(section_match.group(0))


def _load_template_manifest(template_dir: Path, explicit_manifest: Path | None = None) -> dict | None:
    """Load PPTX import metadata when this template came from user PPTX."""
    candidates: list[Path] = []
    if explicit_manifest is not None:
        candidates.append(explicit_manifest)
    candidates.extend([
        template_dir / "manifest.json",
        template_dir / "source_manifest.json",
        template_dir / "template_import" / "manifest.json",
    ])
    for path in candidates:
        if path and path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                return data
    return None


def _manifest_palette(manifest: dict | None) -> list[str]:
    if not manifest:
        return []
    palette = manifest.get("palette")
    colors: list[str] = []
    if isinstance(palette, list):
        for item in palette:
            if isinstance(item, dict):
                color = _normalize_hex(str(item.get("hex", "")))
            else:
                color = _normalize_hex(str(item))
            if color and color not in colors:
                colors.append(color)
    theme_colors = (manifest.get("theme") or {}).get("colors") or {}
    if isinstance(theme_colors, dict):
        for value in theme_colors.values():
            color = _normalize_hex(str(value))
            if color and color not in colors:
                colors.append(color)
    return colors


def _manifest_identity(manifest: dict | None) -> dict:
    if not manifest:
        return {}
    identity = manifest.get("identityCandidates")
    return identity if isinstance(identity, dict) else {}



def _manifest_import_policy(manifest: dict | None) -> dict:
    if not manifest:
        return {}
    policy = manifest.get("importPolicy")
    return policy if isinstance(policy, dict) else {}


def _manifest_layout_profiles(manifest: dict | None) -> dict:
    if not manifest:
        return {}
    profiles = manifest.get("layoutProfiles")
    return profiles if isinstance(profiles, dict) else {}

def _split_keywords(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = re.split(r"[,，;；/、]", value)
        return [p.strip() for p in parts if p.strip()]
    return []


def _summary_from_use_cases(use_cases: str | None) -> str | None:
    if not use_cases:
        return None
    cleaned = use_cases.strip().rstrip(".")
    if not cleaned:
        return None
    return f"{cleaned}."


# ---------------------------------------------------------------------------
# Per-template extraction
# ---------------------------------------------------------------------------

def _list_pages(template_dir: Path) -> list[str]:
    return sorted(p.stem for p in template_dir.glob("*.svg"))


def _extract_entry(template_id: str, template_dir: Path, *, manifest_path: Path | None = None) -> dict:
    spec_path = template_dir / "design_spec.md"
    if not spec_path.exists():
        raise SpecParseError(f"missing design_spec.md in {template_dir}")

    frontmatter, body = _read_spec(spec_path)
    fm = frontmatter or {}

    summary = fm.get("summary")
    if not summary:
        summary = _summary_from_use_cases(
            _extract_section_field(
                body, "I. Template Overview", ["Use Cases", "Use cases"]
            )
        )
    summary = (summary or "").strip()

    keywords = _split_keywords(fm.get("keywords"))
    if not keywords:
        tone = _extract_section_field(
            body, "I. Template Overview", ["Design Tone", "Tone"]
        ) or ""
        keywords = _split_keywords(tone)[:5]

    manifest = _load_template_manifest(template_dir, manifest_path)
    manifest_palette = _manifest_palette(manifest)
    primary_color = (
        fm.get("primary_color")
        or (manifest_palette[0] if manifest_palette else None)
        or _extract_primary_color(body)
    )
    category = fm.get("category", "general")
    use_cases = (
        fm.get("use_cases")
        or _extract_section_field(
            body, "I. Template Overview", ["Use Cases", "Use cases"]
        )
        or ""
    )
    design_tone = (
        fm.get("design_tone")
        or _extract_section_field(
            body, "I. Template Overview", ["Design Tone", "Tone"]
        )
        or ""
    )

    pages = _list_pages(template_dir)

    entry = OrderedDict(
        summary=summary,
        keywords=keywords,
    )
    if primary_color:
        entry["primary_color"] = str(primary_color)
    if manifest_palette:
        entry["palette"] = manifest_palette
        entry["color_priority"] = "user_pptx_template_override"
        entry["template_priority"] = "user_pptx_template_override"
    identity = _manifest_identity(manifest)
    import_policy = _manifest_import_policy(manifest)
    layout_profiles = _manifest_layout_profiles(manifest)
    if manifest:
        entry["template_priority"] = "user_pptx_template_override"
    if identity:
        entry["identity_candidates"] = identity
    if import_policy:
        entry["import_policy"] = import_policy
    if layout_profiles:
        entry["layout_profiles"] = layout_profiles

    extras = OrderedDict(
        pages=pages,
        category=str(category),
        primary_color=str(primary_color or ""),
        use_cases=str(use_cases),
        design_tone=str(design_tone),
        palette=manifest_palette,
        color_priority="user_pptx_template_override" if manifest_palette else "",
        template_priority="user_pptx_template_override" if manifest else "",
        identity_candidates=identity,
        import_policy=import_policy,
        layout_profiles=layout_profiles,
    )
    return {"entry": entry, "extras": extras}


# ---------------------------------------------------------------------------
# Index writers
# ---------------------------------------------------------------------------

def _load_index() -> "OrderedDict[str, dict]":
    if not INDEX_PATH.exists():
        return OrderedDict()
    raw = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return OrderedDict(sorted(raw.items()))


def _write_index(data: "OrderedDict[str, dict]", *, dry_run: bool) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if dry_run:
        _print_text(f"--- {INDEX_PATH.name} (dry-run) ---")
        _print_text(payload)
        return
    INDEX_PATH.write_text(payload, encoding="utf-8")


def _render_quick_index_rows(
    items: Iterable[tuple[str, dict, dict]],
) -> list[str]:
    rows: list[str] = [
        "| Template Name | Category | Use Cases | Primary Color | Design Tone |",
        "|---------------|----------|-----------|---------------|-------------|",
    ]
    for tid, _, extras in items:
        cat = extras.get("category") or "general"
        use_cases = extras.get("use_cases") or "—"
        primary = extras.get("primary_color") or "—"
        if primary != "—":
            primary = f"`{primary}`"
        tone = extras.get("design_tone") or "—"
        rows.append(
            f"| `{tid}` | {cat.title()} | {use_cases} | {primary} | {tone} |"
        )
    return rows


def _patch_readme(
    items: list[tuple[str, dict, dict]],
    *,
    dry_run: bool,
) -> None:
    text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

    # Update header count
    new_total = len(items)
    text = re.sub(
        r"^# Page Layout Template Library \(\d+ Templates\)",
        f"# Page Layout Template Library ({new_total} Templates)",
        text,
        count=1,
        flags=re.MULTILINE,
    )

    rows = _render_quick_index_rows(items)
    block = "\n".join([QUICK_INDEX_BEGIN, *rows, QUICK_INDEX_END])

    if QUICK_INDEX_BEGIN in text and QUICK_INDEX_END in text:
        text = re.sub(
            re.escape(QUICK_INDEX_BEGIN) + r".*?" + re.escape(QUICK_INDEX_END),
            block,
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # Insert the auto-managed block after the "## Quick Template Index"
        # heading; if the heading is missing, append at end.
        anchor = "## Quick Template Index"
        if anchor in text:
            head, _, tail = text.partition(anchor)
            # Drop the legacy hand-maintained table that follows the anchor up
            # to the next "## " heading, then re-insert the managed block.
            tail_lines = tail.splitlines(keepends=True)
            keep_from = 0
            for idx, line in enumerate(tail_lines[1:], start=1):
                if line.startswith("## "):
                    keep_from = idx
                    break
            preserved_tail = "".join(tail_lines[keep_from:])
            text = (
                f"{head}{anchor}\n\n{block}\n\n{preserved_tail}"
            )
        else:
            text = f"{text.rstrip()}\n\n## Quick Template Index\n\n{block}\n"

    if dry_run:
        _print_text(f"--- {README_PATH.name} (dry-run) ---")
        _print_text(text)
        return
    README_PATH.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _enumerate_templates() -> list[str]:
    return sorted(
        p.name for p in LAYOUTS_DIR.iterdir()
        if p.is_dir() and p.name != "images" and (p / "design_spec.md").exists()
    )


def _print_completion_card(template_id: str, entry: dict, extras: dict) -> None:
    print()
    print("## Template Creation Complete")
    print()
    print(f"**Template Name**: {template_id}")
    print(f"**Template Path**: `templates/layouts/{template_id}/`")
    print(f"**Category**: {extras.get('category', 'general')}")
    primary = extras.get("primary_color") or "—"
    print(f"**Primary Color**: {primary}")
    if extras.get("palette"):
        print(f"**Template Palette Priority**: {extras.get('color_priority')}")
        print(f"**Template Design Priority**: {extras.get('template_priority')}")
        print(f"**Palette**: {', '.join(extras.get('palette', []))}")
    identity = extras.get("identity_candidates") or {}
    if identity:
        orgs = ", ".join(identity.get("organizationNames", [])) or "n/a"
        depts = ", ".join(identity.get("departmentNames", [])) or "n/a"
        logos = ", ".join(identity.get("logoAssetCandidates", [])) or "n/a"
        print(f"**Organization Candidates**: {orgs}")
        print(f"**Department Candidates**: {depts}")
        print(f"**Logo Asset Candidates**: {logos}")
    if extras.get("import_policy"):
        print(f"**Import Policy**: {extras.get('import_policy')}")
    if extras.get("layout_profiles"):
        print(f"**Layout Profiles**: {len(extras.get('layout_profiles', {}))} detected")
    print("**Index Registration**: Done")
    print()
    print("### Files Included")
    print()
    print("| File | Status |")
    print("|------|--------|")
    for page in extras.get("pages", []):
        print(f"| `{page}.svg` | Done |")
    print()


def main() -> int:
    """CLI entry: register one template (or rebuild all) into the index."""
    parser = argparse.ArgumentParser(
        description="Register / refresh layout templates in the global index."
    )
    parser.add_argument(
        "template_id",
        nargs="?",
        help="Template directory under templates/layouts/. Omit with --rebuild-all.",
    )
    parser.add_argument(
        "--rebuild-all",
        action="store_true",
        help="Rebuild every index entry from each template's design_spec.md.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be written without modifying any files.",
    )
    parser.add_argument(
        "--manifest",
        help=(
            "Optional manifest.json from template_import/cli.py. When present, "
            "its RGB palette, identity candidates, editable import policy, and user "
            "template design priority override guessed template colors and defaults."
        ),
    )
    args = parser.parse_args()

    if not args.template_id and not args.rebuild_all:
        parser.error("provide a template_id or use --rebuild-all")

    if args.rebuild_all:
        ids = _enumerate_templates()
    else:
        ids = [args.template_id]
        spec_dir = LAYOUTS_DIR / args.template_id
        if not spec_dir.is_dir():
            print(f"Error: template directory not found: {spec_dir}",
                  file=sys.stderr)
            return 1

    # Build entries for the requested ids.
    extracted: dict[str, dict] = {}
    explicit_manifest = Path(args.manifest).expanduser().resolve() if args.manifest else None
    if explicit_manifest and not explicit_manifest.exists():
        print(f"Error: manifest not found: {explicit_manifest}", file=sys.stderr)
        return 1
    for tid in ids:
        try:
            extracted[tid] = _extract_entry(
                tid,
                LAYOUTS_DIR / tid,
                manifest_path=explicit_manifest if not args.rebuild_all else None,
            )
        except SpecParseError as exc:
            print(f"Error: {tid}: {exc}", file=sys.stderr)
            return 1

    # Merge into the index (preserving sibling entries when single-template mode).
    if args.rebuild_all:
        index = OrderedDict(
            (tid, extracted[tid]["entry"]) for tid in sorted(extracted)
        )
    else:
        index = _load_index()
        for tid, payload in extracted.items():
            index[tid] = payload["entry"]
        index = OrderedDict(sorted(index.items()))

    _write_index(index, dry_run=args.dry_run)

    # README is rebuilt from the union of (current index) + (newly extracted
    # entries). For rebuild-all it is just the extracted set.
    if args.rebuild_all:
        readme_items: list[tuple[str, dict, dict]] = [
            (tid, extracted[tid]["entry"], extracted[tid]["extras"])
            for tid in sorted(extracted)
        ]
    else:
        readme_items = []
        all_extras: dict[str, dict] = {}
        for tid in index:
            if tid in extracted:
                all_extras[tid] = extracted[tid]["extras"]
            else:
                template_dir = LAYOUTS_DIR / tid
                if (template_dir / "design_spec.md").exists():
                    try:
                        all_extras[tid] = _extract_entry(tid, template_dir)["extras"]
                    except SpecParseError:
                        all_extras[tid] = {}
                else:
                    all_extras[tid] = {}
            readme_items.append((tid, index[tid], all_extras[tid]))

    _patch_readme(readme_items, dry_run=args.dry_run)

    if not args.dry_run and not args.rebuild_all:
        tid = args.template_id
        _print_completion_card(
            tid, extracted[tid]["entry"], extracted[tid]["extras"]
        )
        return 0

    print()
    print(
        f"[OK] {'Dry-run preview' if args.dry_run else 'Updated'}: "
        f"{len(extracted)} template(s) processed; "
        f"index now lists {len(index)} entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

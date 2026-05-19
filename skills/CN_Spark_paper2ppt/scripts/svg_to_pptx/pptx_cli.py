"""CLI entry point for svg_to_pptx."""

from __future__ import annotations

import sys
import shutil
import argparse
import json
import contextlib
import io
from datetime import datetime
from pathlib import Path

from .pptx_dimensions import CANVAS_FORMATS, get_project_info
from .pptx_discovery import find_svg_files, find_notes_files
from .pptx_builder import create_pptx_with_native_svg
from .pptx_narration import NARRATION_EXTENSIONS, find_narration_files, probe_audio_duration
from .pptx_slide_xml import TRANSITIONS
from .animation_config import load_animation_config, validate_animation_config
from notes_to_docx import write_notes_docx
from svg_quality_checker import SVGQualityChecker

try:
    from pptx_animations import ANIMATIONS as _ANIMATIONS
except ImportError:
    _ANIMATIONS = {}


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _is_final_svg_source(source: str | None) -> bool:
    if not source:
        return False
    normalized = source.replace("\\", "/").rstrip("/").lower()
    return normalized in {"final", "svg_final"} or normalized.endswith("/svg_final")


def _recorded_narration_on_click_slides(
    ref_files: list[Path],
    animation_config: dict | None,
    animation: str | None,
    animation_trigger: str,
    animation_cli_overrides: dict[str, bool],
) -> list[str]:
    """Return slides whose effective recorded-video animation trigger is on-click."""
    slides_cfg = _as_dict(_as_dict(animation_config).get('slides'))
    blocked: list[str] = []
    for svg_path in ref_files:
        slide_cfg = _as_dict(slides_cfg.get(svg_path.stem))
        anim_cfg = _as_dict(slide_cfg.get('animation'))

        slide_animation = animation
        if not animation_cli_overrides.get('animation') and 'effect' in anim_cfg:
            cfg_effect = str(anim_cfg.get('effect'))
            slide_animation = None if cfg_effect == 'none' else cfg_effect
        if slide_animation is None:
            continue

        slide_trigger = animation_trigger
        if not animation_cli_overrides.get('animation_trigger') and anim_cfg.get('trigger'):
            slide_trigger = str(anim_cfg.get('trigger'))
        if slide_trigger == 'on-click':
            blocked.append(svg_path.stem)
    return blocked


def _auto_repair_svg_output_layout(project_path: Path, *, verbose: bool) -> int:
    """Normalize raw svg_output text boxes before the quality gate.

    This is intentionally conservative: it only writes data-box contracts for
    text already placed inside visible SVG rectangles, preserving the original
    x/y instead of snapping every label to the full card. Remaining structural
    problems still fail the quality gate.
    """
    svg_dir = project_path / "svg_output"
    if not svg_dir.is_dir():
        return 0
    try:
        from xml.etree import ElementTree as ET
        from .drawingml_utils import SVG_NS
        from .tspan_flattener import flatten_positional_tspans
        from .textbox_normalizer import (
            merge_simple_multiline_tspans,
            normalize_text_boxes,
            reconcile_text_boxes_with_shapes,
        )
    except Exception:
        return 0
    ET.register_namespace("", SVG_NS)
    changed_files = 0
    for svg_path in sorted(svg_dir.glob("*.svg")):
        try:
            tree = ET.parse(str(svg_path))
            root = tree.getroot()
            changed = 0
            changed += merge_simple_multiline_tspans(root)
            changed += normalize_text_boxes(root)
            changed += reconcile_text_boxes_with_shapes(root)
            if flatten_positional_tspans(tree):
                changed += 1
                root = tree.getroot()
                changed += normalize_text_boxes(root)
                changed += reconcile_text_boxes_with_shapes(root)
            if changed:
                tree.write(str(svg_path), encoding="unicode", xml_declaration=False)
                changed_files += 1
        except Exception as exc:
            if verbose:
                print(f"  [warn] layout auto-repair skipped {svg_path.name}: {exc}")
    if verbose and changed_files:
        print(f"  Layout auto-repair: normalized text boxes in {changed_files} SVG file(s)")
    return changed_files


def _run_svg_quality_gate(
    project_path: Path,
    *,
    expected_format: str | None,
    verbose: bool,
    auto_repair_layout: bool = True,
) -> None:
    if auto_repair_layout:
        _auto_repair_svg_output_layout(project_path, verbose=verbose)
    checker = SVGQualityChecker()
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        checker.check_directory(str(project_path), expected_format=expected_format)
        checker.print_summary()
    report = buffer.getvalue()
    if checker.summary.get('errors', 0) > 0:
        print("Error: SVG quality gate failed before PPTX export.", file=sys.stderr)
        if report:
            print(report, file=sys.stderr)
        sys.exit(1)
    if verbose and checker.summary.get('warnings', 0) > 0:
        print(f"  [warn] SVG quality gate: {checker.summary['warnings']} warning(s)")


def _load_direct_image_slides(project_path: Path, manifest_arg: str | None, *, verbose: bool) -> list[dict]:
    candidates: list[Path] = []
    if manifest_arg:
        manifest = Path(manifest_arg)
        candidates.append(manifest if manifest.is_absolute() else project_path / manifest)
    else:
        candidates.extend([
            project_path / "svg_output" / "_direct_image_slides.json",
            project_path / "_direct_image_slides.json",
            project_path / "technicalroute" / "_direct_image_slides.json",
        ])

    slides: list[dict] = []
    for manifest in candidates:
        if not manifest.is_file():
            continue
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        raw_slides = data.get("slides", data) if isinstance(data, dict) else data
        if not isinstance(raw_slides, list):
            raise ValueError(f"direct image slide manifest must contain a list: {manifest}")
        for item in raw_slides:
            if not isinstance(item, dict):
                continue
            image_value = item.get("image_path") or item.get("path")
            if not image_value:
                continue
            image_path = Path(str(image_value)).expanduser()
            if not image_path.is_absolute():
                image_path = (manifest.parent / image_path).resolve()
            if not image_path.is_file():
                raise FileNotFoundError(f"direct image slide not found: {image_path}")
            normalized = dict(item)
            normalized["image_path"] = str(image_path)
            slides.append(normalized)
        if verbose and slides:
            print(f"  Direct image slide manifest: {manifest} ({len(slides)} slide(s))")
        break
    return slides


def main() -> None:
    """CLI entry point for the SVG to PPTX conversion tool."""
    transition_choices = (
        ['none'] + (list(TRANSITIONS.keys()) if TRANSITIONS
                    else ['fade', 'push', 'wipe', 'split', 'strips', 'cover', 'random'])
    )

    animation_choices = (
        ['none'] + (list(_ANIMATIONS.keys()) if _ANIMATIONS
                    else ['fade', 'fly', 'zoom', 'appear'])
        + ['mixed', 'random']
    )

    parser = argparse.ArgumentParser(
        description='PPT Master - SVG to PPTX Tool (Office Compatibility Mode)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Examples:
    %(prog)s examples/ppt169_demo             # Default: native editable PPTX from svg_output/
    %(prog)s examples/ppt169_demo --only native   # Explicit native editable shapes version
    %(prog)s examples/ppt169_demo --only legacy --allow-legacy-image-pptx   # Diagnostic SVG-image version
    %(prog)s examples/ppt169_demo -o out.pptx     # Explicit native output path

    # Enable transition / change transition effect (default: no transition)
    %(prog)s examples/ppt169_demo -t push --transition-duration 1.0

SVG source directory (-s):
    output   - svg_output (original version)
    final    - svg_final (post-processed; legacy SVG-reference output only)
    <any>    - Specify a subdirectory name directly

    Native DrawingML export always protects itself from svg_final because
    svg_final may contain pathified rounded rectangles / lines that become
    large <a:custGeom> blocks in PPTX. If -s final is passed with --only native,
    native export automatically falls back to svg_output/.

Transition effects (-t/--transition):
    {', '.join(transition_choices)}

Per-element entrance animation (-a/--animation, native shapes mode):
    {', '.join(animation_choices)}
    Notes: applied to top-level <g id="..."> SVG groups in z-order. Default is
           "mixed" (auto-vary effects per group). Start mode set by
           --animation-trigger, matching PowerPoint's Start dropdown:
             on-click              one presenter click per group
             with-previous         all groups start together on slide entry
             after-previous (default)  cascade on slide entry;
                                       gap = --animation-stagger seconds
           mixed uses a curated visible-effect sequence across the deck; random samples
           from the same visible-effect pool. Use "-a none" to disable.

Compatibility mode (enabled by default):
    - Automatically generates PNG fallback images, SVG embedded as extension
    - Compatible with all Office versions (including Office LTSC 2021)
    - Newer Office still displays SVG (editable), older versions display PNG
    - Requires svglib: pip install svglib reportlab
    - Use --no-compat to disable (only Office 2019+ supported)

Speaker notes:
    - Automatically reads Markdown notes files from the notes/ directory
    - Supports two naming conventions:
      1. Match by filename (recommended): 01_cover.md corresponds to 01_cover.svg
      2. Match by index: slide01.md corresponds to the 1st SVG (backward compatible)
    - Default: write a separate speaker-notes DOCX under exports/
    - PPTX notes are always stripped for openability; use the DOCX for speaker notes
    - Use --no-notes to disable DOCX notes export

Recorded narration:
    %(prog)s examples/ppt169_demo -s final --recorded-narration audio
    - Keeps notes as a separate DOCX; PPTX notes are not embedded
    - Prepares PowerPoint recorded timings and narrations
    - Requires one m4a/mp3/wav file per slide
    - Embeds per-slide audio matched by SVG filename / slide number
    - Sets slide auto-advance from audio duration so video export can use
      "recorded timings and narrations"
    - Rejects on-click object animations; use after-previous or with-previous
    %(prog)s examples/ppt169_demo --narration-audio-dir audio
    - Lower-level audio embedding: embeds matched files but allows partial matches
    - Use only when you do not need a complete recorded-timings export
''',
    )

    parser.add_argument('project_path', type=str, help='Project directory path')
    parser.add_argument('-o', '--output', type=str, default=None, help='Output file path')
    parser.add_argument('-s', '--source', type=str, default=None,
                        help='SVG source directory. Default: native reads '
                             'svg_output/ (high-fidelity, preserves icons / '
                             'preserveAspectRatio / rx-ry); legacy reads '
                             'svg_final/ (PPT-internal SVG parser fallback). '
                             'For native DrawingML, final/svg_final is refused '
                             'and svg_output is used instead.')
    parser.add_argument('-f', '--format', type=str,
                        choices=list(CANVAS_FORMATS.keys()), default=None,
                        help='Specify canvas format')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    parser.add_argument('--no-auto-repair-layout', action='store_true',
                        help='Disable conservative svg_output text-box repair before export quality gate')
    parser.add_argument('--direct-image-slides', type=str, default=None,
                        help='Optional JSON manifest for direct PPTX picture slides. Default: <project>/svg_output/_direct_image_slides.json when present.')

    parser.add_argument('--no-compat', action='store_true',
                        help='Disable Office compatibility mode (pure SVG only, requires Office 2019+)')

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--only', type=str, choices=['native', 'legacy'], default=None,
                            help='Only generate one version: native (editable shapes) or legacy (SVG image)')
    mode_group.add_argument('--native', action='store_true', default=False,
                            help='(Deprecated, now default) Convert SVG to native DrawingML shapes')
    parser.add_argument('--allow-legacy-image-pptx', action='store_true', default=False,
                        help='Explicitly allow legacy SVG-image PPTX export. Academic decks must stay native/editable by default.')

    def non_negative_float(value: str) -> float:
        try:
            number = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"must be a number: {value}") from exc
        if number < 0:
            raise argparse.ArgumentTypeError("must be non-negative")
        return number

    parser.add_argument('-t', '--transition', type=str, choices=transition_choices, default=None,
                        help='Page transition effect (default: none; enable only when explicitly requested)')
    parser.add_argument('--transition-duration', type=non_negative_float, default=None,
                        help='Transition duration in seconds (default: 0.4)')
    parser.add_argument('--auto-advance', type=non_negative_float, default=None,
                        help='Auto-advance interval in seconds (default: manual advance)')

    parser.add_argument('-a', '--animation', type=str, choices=animation_choices,
                        default=None,
                        help='Per-element entrance animation (native shapes mode '
                             'only). Pick a single effect, "mixed" (auto-vary per '
                             'element, default), "random", or "none" to disable.')
    parser.add_argument('--animation-duration', type=non_negative_float, default=None,
                        help='Per-element entrance duration in seconds (default: 0.4)')
    parser.add_argument('--animation-trigger', type=str,
                        choices=['on-click', 'with-previous', 'after-previous'],
                        default=None,
                        help='Per-element Start mode (matches PowerPoint Start dropdown): '
                             '"on-click" (one click per element), '
                             '"with-previous" (all start together on slide entry), '
                             '"after-previous" (default, cascade after the previous element).')
    parser.add_argument('--animation-stagger', type=non_negative_float, default=None,
                        help='Delay between elements in --animation-trigger=after-previous '
                             '(seconds, default 0.5). Ignored in other modes.')
    parser.add_argument('--animation-config', type=str, default=None,
                        help='Optional per-slide/per-object animation config. '
                             'Default: <project>/animations.json when present.')

    parser.add_argument('--no-notes', action='store_true',
                        help='Disable speaker notes DOCX export')
    parser.add_argument('--embed-notes', action='store_true',
                        help='Deprecated/no-op: PPTX notes are stripped for openability; speaker notes stay in DOCX.')
    parser.add_argument('--narration-audio-dir', type=str, default=None,
                        help='Low-level audio embedding from this directory; allows partial matches')
    parser.add_argument('--use-narration-timings', action='store_true',
                        help='Set slide auto-advance timings from narration audio durations')
    parser.add_argument('--recorded-narration', type=str, default=None,
                        help='Prepare PowerPoint recorded timings and narrations from a complete audio directory')
    parser.add_argument('--narration-padding', type=float, default=0.5,
                        help='Seconds to add after each narration before auto-advance (default: 0.5)')

    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    try:
        project_info = get_project_info(str(project_path))
        project_name = project_info.get('name', project_path.name)
        detected_format = project_info.get('format')
    except Exception:
        project_name = project_path.name
        detected_format = None

    canvas_format = args.format
    if canvas_format is None and detected_format and detected_format != 'unknown':
        canvas_format = detected_format

    # Determine which versions to generate. Default is native-only:
    # legacy SVG-reference PPTX is intentionally image-only and must be an
    # explicit diagnostic opt-in, never the normal academic deliverable.
    only_mode = args.only
    if only_mode == 'legacy' and not args.allow_legacy_image_pptx:
        parser.error(
            "--only legacy creates image-only PPTX and is disabled by default. "
            "Use --allow-legacy-image-pptx only for diagnostic snapshots; "
            "academic decks must use native editable DrawingML."
        )
    gen_native = only_mode in (None, 'native')
    gen_legacy = only_mode == 'legacy'

    # --native flag (deprecated) maps to --only native
    if args.native and only_mode is None:
        gen_legacy = False

    # Pipeline split: native pptx gets the high-fidelity svg_output/ source
    # (icons, preserveAspectRatio, rounded-rect rx/ry are all preserved by the
    # converter); legacy pptx still needs svg_final/ because PowerPoint's
    # internal SVG parser cannot handle <use data-icon> or honour
    # preserveAspectRatio. An explicit -s overrides both branches so callers
    # can keep the previous single-source behaviour for unusual workflows.
    explicit_source = args.source is not None
    if explicit_source and _is_final_svg_source(args.source) and gen_native:
        print(
            "  Warning: native DrawingML export cannot use svg_final/-s final; "
            "using svg_output to avoid pathified shapes and excessive custom geometry."
        )
        native_source = 'output'
    else:
        native_source = args.source if explicit_source else 'output'
    legacy_source = args.source if explicit_source else 'final'

    native_files: list[Path] = []
    legacy_files: list[Path] = []
    native_source_dir = ''
    legacy_source_dir = ''

    if gen_native:
        native_files, native_source_dir = find_svg_files(project_path, native_source)
    if gen_legacy:
        legacy_files, legacy_source_dir = find_svg_files(project_path, legacy_source)

    # Reference list for cross-product lookups (notes / narration matching).
    # native_files and legacy_files share filenames because svg_final/ is
    # copytree'd from svg_output/, so either list works for matching.
    ref_files = native_files or legacy_files
    if not ref_files:
        print("Error: No SVG files found")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_dir: Path | None = None
    if args.output:
        output_base = Path(args.output)
        native_path = output_base
        stem = output_base.stem
        legacy_path = output_base.parent / f"{stem}_svg{output_base.suffix}"
    else:
        exports_dir = project_path / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        native_path = exports_dir / f"{project_name}_{timestamp}.pptx"
        legacy_path = exports_dir / f"{project_name}_{timestamp}_svg.pptx"

        if gen_legacy:
            backup_dir = project_path / "backup" / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)
            legacy_path = backup_dir / f"{project_name}_svg.pptx"

    native_path.parent.mkdir(parents=True, exist_ok=True)
    if gen_legacy:
        legacy_path.parent.mkdir(parents=True, exist_ok=True)

    verbose = not args.quiet

    enable_notes = bool(args.embed_notes and not args.no_notes)
    export_notes_docx = not args.no_notes
    notes: dict[str, str] = {}
    if enable_notes or export_notes_docx:
        notes = find_notes_files(project_path, ref_files)
    if export_notes_docx and notes:
        try:
            docx_path = write_notes_docx(project_path)
            if verbose:
                print(f"  Speaker notes DOCX: {docx_path}")
        except Exception as exc:
            print(f"  [warn] Speaker notes DOCX export failed: {exc}")
    elif export_notes_docx and verbose:
        print("  Speaker notes DOCX: no matching notes found")

    narration_audio: dict[str, Path] = {}
    narration_audio_dir_arg = args.recorded_narration or args.narration_audio_dir
    use_narration_timings = args.use_narration_timings or bool(args.recorded_narration)
    if narration_audio_dir_arg:
        narration_audio_dir = Path(narration_audio_dir_arg)
        if not narration_audio_dir.is_absolute():
            narration_audio_dir = project_path / narration_audio_dir
        if args.recorded_narration and not narration_audio_dir.is_dir():
            print(
                f"Error: Recorded narration directory does not exist: {narration_audio_dir}",
                file=sys.stderr,
            )
            sys.exit(1)
        narration_audio = find_narration_files(narration_audio_dir, ref_files)
        if verbose:
            print(f"  Narration audio directory: {narration_audio_dir}")
            print(f"  Narration audio matched: {len(narration_audio)}/{len(ref_files)} slide(s)")
        if args.recorded_narration:
            missing = [path.stem for path in ref_files if path.stem not in narration_audio]
            if missing:
                print(
                    "Error: Recorded narration requires one supported audio file per slide. "
                    f"Matched {len(narration_audio)}/{len(ref_files)} slide(s). "
                    f"Supported extensions: {', '.join(NARRATION_EXTENSIONS)}",
                    file=sys.stderr,
                )
                for stem in missing[:20]:
                    print(f"  Missing audio for: {stem}", file=sys.stderr)
                if len(missing) > 20:
                    print(f"  ... and {len(missing) - 20} more", file=sys.stderr)
                sys.exit(1)
            unreadable = [
                f"{stem}: {audio_path}"
                for stem, audio_path in sorted(narration_audio.items())
                if probe_audio_duration(audio_path) is None
            ]
            if unreadable:
                print(
                    "Error: Recorded narration requires readable audio durations. "
                    "Install ffprobe/ffmpeg or replace the listed audio files.",
                    file=sys.stderr,
                )
                for item in unreadable[:20]:
                    print(f"  {item}", file=sys.stderr)
                if len(unreadable) > 20:
                    print(f"  ... and {len(unreadable) - 20} more", file=sys.stderr)
                sys.exit(1)
        elif narration_audio_dir_arg and verbose:
            missing = [path.stem for path in ref_files if path.stem not in narration_audio]
            if missing:
                print(
                    f"  [warn] Narration audio matched {len(narration_audio)}/{len(ref_files)} slide(s); "
                    "unmatched slides will export without audio."
                )

    if args.animation_config:
        config_path = Path(args.animation_config)
        if not config_path.is_absolute():
            config_path = project_path / config_path
        if not config_path.exists():
            print(f"Error: Animation config does not exist: {config_path}")
            sys.exit(1)

    try:
        animation_config = load_animation_config(project_path, args.animation_config)
    except Exception as exc:
        print(f"Error: Failed to load animation config: {exc}")
        sys.exit(1)
    if animation_config and verbose:
        config_label = args.animation_config or str(project_path / 'animations.json')
        print(f"  Animation config: {config_label}")
        for warning in validate_animation_config(project_path, animation_config):
            print(f"  [warn] {warning}")

    defaults = animation_config.get('defaults', {}) if animation_config else {}
    transition_defaults = defaults.get('transition', {}) if isinstance(defaults, dict) else {}
    animation_defaults = defaults.get('animation', {}) if isinstance(defaults, dict) else {}

    transition_arg = args.transition
    transition_effect = transition_arg if transition_arg is not None else transition_defaults.get('effect', 'none')
    transition = None if transition_effect == 'none' else transition_effect
    transition_duration = (
        args.transition_duration
        if args.transition_duration is not None
        else float(transition_defaults.get('duration', 0.4))
    )

    animation_arg = args.animation
    animation_effect = (
        animation_arg
        if animation_arg is not None
        else animation_defaults.get('effect', 'mixed')
    )
    animation = None if animation_effect == 'none' else animation_effect
    animation_duration = (
        args.animation_duration
        if args.animation_duration is not None
        else float(animation_defaults.get('duration', 0.4))
    )
    animation_stagger = (
        args.animation_stagger
        if args.animation_stagger is not None
        else float(animation_defaults.get('stagger', 0.5))
    )
    animation_trigger = (
        args.animation_trigger
        if args.animation_trigger is not None
        else animation_defaults.get('trigger', 'after-previous')
    )

    animation_cli_overrides = {
        'transition': args.transition is not None,
        'transition_duration': args.transition_duration is not None,
        'auto_advance': args.auto_advance is not None,
        'animation': args.animation is not None,
        'animation_duration': args.animation_duration is not None,
        'animation_stagger': args.animation_stagger is not None,
        'animation_trigger': args.animation_trigger is not None,
    }

    if args.recorded_narration and gen_native:
        on_click_slides = _recorded_narration_on_click_slides(
            ref_files,
            animation_config,
            animation,
            animation_trigger,
            animation_cli_overrides,
        )
        if on_click_slides:
            print(
                "Error: --recorded-narration cannot be used with on-click object animations. "
                "Use --animation-trigger after-previous or --animation-trigger with-previous.",
                file=sys.stderr,
            )
            for slide in on_click_slides[:20]:
                print(f"  on-click trigger: {slide}", file=sys.stderr)
            if len(on_click_slides) > 20:
                print(f"  ... and {len(on_click_slides) - 20} more", file=sys.stderr)
            sys.exit(1)

    try:
        direct_image_slides = _load_direct_image_slides(project_path, args.direct_image_slides, verbose=verbose)
    except Exception as exc:
        print(f"Error: Failed to load direct image slides: {exc}", file=sys.stderr)
        sys.exit(1)

    _run_svg_quality_gate(
        project_path,
        expected_format=canvas_format,
        verbose=verbose,
        auto_repair_layout=not args.no_auto_repair_layout,
    )

    # svg_files is per-product (native vs legacy may now read different
    # directories); everything else is shared.
    shared_kwargs = dict(
        canvas_format=canvas_format,
        verbose=verbose,
        transition=transition,
        transition_duration=transition_duration,
        auto_advance=args.auto_advance,
        use_compat_mode=not args.no_compat,
        notes=notes,
        enable_notes=enable_notes,
        animation=animation,
        animation_duration=animation_duration,
        animation_stagger=animation_stagger,
        animation_trigger=animation_trigger,
        animation_config=animation_config,
        animation_cli_overrides=animation_cli_overrides,
        narration_audio=narration_audio,
        use_narration_timings=use_narration_timings,
        narration_padding=args.narration_padding,
        direct_image_slides=direct_image_slides,
    )

    success = True

    # --- Native shapes version (primary) ---
    if gen_native:
        if verbose:
            print("PPT Master - SVG to PPTX Tool")
            print("=" * 50)
            print(f"  Project path: {project_path}")
            print(f"  SVG directory: {native_source_dir}")
            print(f"  Output file: {native_path}")
            print()

        ok = create_pptx_with_native_svg(
            output_path=native_path,
            use_native_shapes=True,
            svg_files=native_files,
            **shared_kwargs,
        )
        success = success and ok

    # --- SVG image reference version ---
    if gen_legacy:
        if verbose:
            if gen_native:
                print()
                print("-" * 50)
            print("PPT Master - SVG to PPTX Tool (SVG Reference)")
            print("=" * 50)
            print(f"  Project path: {project_path}")
            print(f"  SVG directory: {legacy_source_dir}")
            print(f"  Output file: {legacy_path}")
            print()

        ok = create_pptx_with_native_svg(
            output_path=legacy_path,
            use_native_shapes=False,
            svg_files=legacy_files,
            **shared_kwargs,
        )
        success = success and ok

        if ok and backup_dir is not None:
            svg_output_src = project_path / "svg_output"
            if svg_output_src.is_dir():
                svg_output_dst = backup_dir / "svg_output"
                try:
                    shutil.copytree(svg_output_src, svg_output_dst)
                    if verbose:
                        print(f"  svg_output backup: {svg_output_dst}")
                except Exception as exc:
                    if verbose:
                        print(f"  [warn] svg_output backup skipped: {exc}")
            elif verbose:
                print(f"  [info] svg_output/ not found, backup skipped")

    sys.exit(0 if success else 1)

---
description: Import or create reusable academic PPT layout templates, especially user-provided PPTX templates, with manifest-based placeholder contracts and validation gates.
---

# Create Template Workflow
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在用户上传 PPT/PPTX/SVG/截图并要求加入 templates 库或作为后续 PPT 复用模板时读取；它规定模板导入、分析、确认、重建、注册、验证的上下游流程，并强制用户 PPTX 模板按母版/版式占位符填充，避免元素重叠和无效占位符残留。

> Role invoked: `references/template-designer.md`.

Generate or register a reusable template package under `templates/layouts/<template_id>/`. This workflow is for global reusable template assets, not one-off project slide editing.

For user-provided PPTX templates, the goal is not to perfectly duplicate every visible object. The goal is to extract the editable master/layout contract, identity regions, palette, typography, page-number slots, and layout profiles so later decks can fill the template's own placeholders safely.

## Process Overview

```text
Reference Intake & Analysis -> Fact-Based Brief Proposal -> User Confirmation Gate -> Create / Import Template Package -> Validate Layout Contract -> Register Index -> Output
```

No final template directory may be created, no final `design_spec.md` may be written, and `templates/layouts/layouts_index.json` must not be modified until the Step 3 confirmation gate emits `[TEMPLATE_BRIEF_CONFIRMED]`. Temporary analysis workspaces produced by `scripts/template_import/cli.py` are allowed before that gate because they are not final library assets.

## Scope And Trigger

| Trigger | Action |
|---|---|
| User uploads a PPTX and asks to reuse it as a template | Run the PPTX import branch and register a reusable user template. |
| User asks to add a template to `templates/layouts` | Run this workflow. |
| User provides existing SVG layouts to convert into a template package | Run the SVG branch. |
| User provides screenshots / PDF pages as template references | Run the visual-reference branch. |
| User asks for visual changes to an already generated deck | Do not run; use `visual-edit.md` or direct SVG editing. |
| User only selects an existing template for a deck | Do not run; return to SKILL.md Step 3. |

## Step 0 - Path And Command Conventions

All commands are relative to the `CN_Spark_paper2ppt` skill directory unless an absolute path is explicitly supplied.

| Artifact | Path |
|---|---|
| Template library | `templates/layouts/` |
| Template index | `templates/layouts/layouts_index.json` |
| Template role reference | `references/template-designer.md` |
| Import helper | `scripts/template_import/cli.py` |
| Layout guard | `scripts/template_import/layout_guard.py` |
| Registrar | `scripts/template_import/register.py` |
| SVG checker | `scripts/svg_quality_checker.py` |

Always prefer repository scripts over ad hoc conversion. If a command signature is uncertain, run `python scripts/<name>.py --help` and follow the local script, not external documentation.

## Step 1 - Reference Intake And Analysis

Branch by the reference source.

| Type | User supplied | Read / tool path | Supported modes |
|---|---|---|---|
| A | `.pptx` / `.ppt` template | `scripts/template_import/cli.py` -> manifest + layered SVG + flat SVG + assets | `placeholder_fill` / `fidelity_reference` / `mirror_reference` |
| B | Existing SVG template folder or project `svg_output/` | Read SVGs plus `design_spec.md` / `spec_lock.md` if present | `standard` / `fidelity_reference` / `mirror_reference` |
| C | Screenshots, images, PDF pages | Visual inspection + optional conversion | `standard` only |
| D | Verbal template description only | User brief | `standard` only |

`placeholder_fill` is the preferred mode for user PPTX templates in this skill. It produces a reusable template whose master/layout placeholders and protected regions are the downstream contract. `mirror_reference` is allowed only when the user explicitly asks for a visual reference library page set; mirror pages are not suitable for automatic academic deck generation because they do not provide editable placeholder contracts.

### 1A. PPTX Reference Import

Run:

```bash
python3 scripts/template_import/cli.py "<reference_template.pptx>" -o "<workspace>" --inheritance-mode both
```

Expected workspace:

| Output | Use |
|---|---|
| `manifest.json` | Factual source of slide size, theme colors, fonts, assets, masters, layouts, placeholders, page-number slots, protected elements, layout profiles, overlap audits, and identity candidates. |
| `summary.md` | Quick orientation only. Do not treat it as canonical. |
| `assets/` | Reusable extracted images and identity assets. |
| `svg/master_*.svg` | Shared master structure, fixed chrome, logo/name/footer/page-number zones, and placeholder guides. |
| `svg/layout_*.svg` | Layout-level slots and page geometry. |
| `svg/slide_NN.svg` | Slide-local editable examples only; use as evidence of how slots were filled. |
| `svg/inheritance.json` | Slide -> layout -> master mapping. |
| `svg-flat/slide_NN.svg` | Human preview of what PowerPoint displays; use for sanity checks, not as the main structural source. |

Hard read order before Step 2:

1. Read `manifest.json`.
2. Read every `svg/master_*.svg`.
3. Read every `svg/layout_*.svg`.
4. Read `svg/inheritance.json`.
5. Inspect `assets/`.
6. Read every `svg/slide_NN.svg`.
7. Use `svg-flat/slide_NN.svg` only for visual comparison.
8. Use `summary.md` only as orientation.

Hard read proof: Step 2 must list the master, layout, and slide filenames that were read. If many files exist, list counts plus representative filenames and state that the full set was scanned.

Interpretation rules:

- `manifest.json` is authoritative for factual metadata.
- `svg/master_*.svg` and `svg/layout_*.svg` are authoritative for reusable structure.
- `svg/slide_NN.svg` provides examples of ordinary editable content, not additional fixed chrome.
- `svg-flat/slide_NN.svg` is a preview, not a source for duplicated master/layout elements.
- Do not re-create master-only shapes as slide-local objects.
- Do not duplicate fixed school logo, school name, department name, footer, page number, or master placeholders as overlapping slide-local text/shape boxes.
- Use `manifest.slides[*].editableContentRegion` or `templateBinding.editableContentRegion` to determine the true writable content area. This region must exclude school name, logo, header chrome, footer marks, page-number slots, citation footer, and bottom banners.

After import, run the guard before registration:

```bash
python3 scripts/template_import/layout_guard.py "<workspace>/manifest.json"
```

Use `--strict` only after the template package is believed to be ready, because the first pass may intentionally surface issues to repair.

If `editableContentRegion.primary` is missing, zero-sized, or overlaps a protected region, the template is not ready for downstream academic deck generation. Fix the source contract or choose another imported layout.

### 1B. Existing SVG Assets

Read every `*.svg` and any companion `design_spec.md`, `spec_lock.md`, or manifest-like metadata. Extract root `viewBox`, dominant colors, fonts, repeated chrome, placeholder strings, image references, existing asset paths, and likely page types. If existing SVGs already form a valid template package, prefer registering and documenting them over rebuilding from scratch.

### 1C. Image / Screenshot / PDF References

Use visual inspection only for style and composition. Do not claim exact HEX colors, font names, placeholder geometry, or editability unless they are separately extracted from source files. Label these values as `[suggested]` in Step 2.

### 1D. No Reference Source

All required fields are user decisions or AI suggestions. Do not invent brand assets, school marks, or exact colors.

## Step 2 - Fact-Based Brief Proposal

Before writing final files, present one brief proposal with provenance labels.

| Label | Meaning |
|---|---|
| `[fact]` | Extracted from manifest, SVG, file metadata, or existing spec. |
| `[suggested]` | Inferred from visual analysis or academic use case. |
| `[decision]` | User must choose or explicitly accept. |

Required brief fields:

| Field | Requirement |
|---|---|
| `template_id` | ASCII filesystem-safe slug; must match directory and index key. |
| Display name | Human-readable template name. |
| Category | `academic`, `brand`, `general`, `scenario`, `government`, or `special`. |
| Applicable academic scenarios | Defense, group meeting, journal club, proposal, course report, literature review, etc. |
| Canvas format | Usually `ppt169`; derive from manifest/SVG when possible. |
| Template mode | Prefer `placeholder_fill` for PPTX. |
| Replication / fidelity intent | `standard`, `fidelity_reference`, or `mirror_reference` with limitations. |
| Theme color and palette | HEX RGB; mark source and priority. |
| Font system | Font families and size bands from manifest when available. |
| Identity candidates | Logo, school name, college / lab name, and protected positions. |
| Page-number source | slide / layout / master / fallback. |
| Layout profiles | Available slot types and best uses. |
| Asset list | Reusable extracted assets and intended names. |
| Keywords | 3-8 discovery tags for `layouts_index.json`. |
| Known risks | Missing media, overlap failures, weak placeholder coverage, incomplete layouts. |

For PPTX imports, include the workspace path, count/list of read master/layout/slide SVG files, top layout profiles, protected identity regions, `template_import/layout_guard.py` findings, and whether usable `sldNum` page-number placeholders exist.

## Step 3 - User Confirmation Gate

This step blocks final template creation.

1. Echo the finalized brief after corrections.
2. Confirm that the output is a reusable global template under `templates/layouts/<template_id>/`.
3. Confirm mode, canvas, and category.
4. Emit `[TEMPLATE_BRIEF_CONFIRMED]` on its own line.

Do not create or overwrite the final template directory before this marker. Do not register index entries before this marker.

## Step 4 - Create Or Update The Template Package

Precondition: `[TEMPLATE_BRIEF_CONFIRMED]` was emitted in the current task.

Create:

```bash
mkdir "templates/layouts/<template_id>"
```

If the directory exists, inspect it first. Do not overwrite existing SVGs, `design_spec.md`, `manifest.json`, or assets without confirmation unless the user explicitly asked to replace that template.

### 4A. User PPTX Placeholder-Fill Package

For PPTX templates, copy factual import outputs into the template package.

| Source | Destination |
|---|---|
| `<workspace>/manifest.json` | `templates/layouts/<template_id>/source_manifest.json` or `manifest.json` |
| `<workspace>/summary.md` | optional `template_import_summary.md` |
| `<workspace>/assets/*` | `templates/layouts/<template_id>/assets/` or stable local asset names |
| selected SVG references | keep only if they are needed as editable reference pages or previews |

Write `design_spec.md` with YAML frontmatter:

```yaml
---
template_id: <template_id>
category: academic
summary: <one-line discovery summary>
keywords: [academic, defense, user-pptx]
primary_color: "#RRGGBB"
canvas_format: ppt169
template_mode: placeholder_fill
replication_mode: standard
source_type: user_pptx
source_manifest: source_manifest.json
color_priority: user_pptx_template_override
template_priority: user_pptx_template_override
page_number_policy: follow_slide_layout_master_sldNum_slot
master_placeholder_fill_mode: true
fill_existing_slots_only: true
allow_extra_generated_shapes: false
allow_extra_generated_text_boxes: false
allow_extra_generated_image_frames: false
remove_unused_placeholder_prompts: true
---
```

The body must include Template Overview, Color Scheme, Typography, Protected Identity Regions, Page Number Rule, Layout Profile Table, Page Roster or Source Layout Roster, Slot Mapping Guidance, and Known Import Risks / Guard Results. Do not write generic SVG rules into the template's `design_spec.md`; keep only this template's personality and factual contract there.

### 4B. Master Placeholder Fill Mode Rules

For user PPTX templates, downstream deck generation must fill existing slots.

- Use master/layout placeholder geometry as the primary contract for title, subtitle, body, picture, chart, formula, footer, date, and page number placement.
- Add generated text, source figures, formula PNGs, charts, and route images into matching placeholders or existing slide-local slots.
- Do not create extra decorative shapes, free-floating text boxes, or image frames when a suitable slot exists.
- If a planned page needs a visual and the selected layout lacks a visual slot, choose another user-template layout first.
- Use the built-in template library only when no user-template layout fits; record `layout_source: fallback_template_library` in `design_spec.md` and `spec_lock.md`.
- Do not identify locked master shapes as editable content boxes.
- Remove empty PowerPoint prompt text before export with `finalize_svg.py` default cleanup.

### 4C. Layout Selection Contract

Every planned slide must select a source layout by matching content needs to manifest layout profiles.

| Page need | Prefer layout with |
|---|---|
| Cover | title, subtitle, logo / identity slot, minimal body content. |
| Agenda / section divider | large title or center-title slot, optional module marker. |
| Text + source figure | title + body + picture/content placeholder. |
| Figure-first result | title + large picture/content placeholder. |
| Formula page | title + wide content/body slot with enough height for formula PNG. |
| Comparison / matrix | title + two or more body/content slots. |
| TechnicalRoute A/B pages | title + large picture/content slot; avoid dense multi-column layouts. |
| Summary / implication | title + body/takeaway slot; no forced visual slot. |

Record per planned page in project `spec_lock.md`:

```yaml
page_layouts:
  07_model_results:
    layout_key: <manifest layout id or name>
    source: user_pptx_layout
    slot_map:
      title: <slot id>
      main_visual: <slot id>
      interpretation: <slot id>
    page_number_source: layout|master|slide|fallback
    overlap_audit: pass|needs_fix
```

### 4D. Protected Regions And Overlap Policy

Use `manifest.protectedElements`, `pageNumberSlot`, layout profiles, and `overlapAudit`.

Also use `manifest.slides[*].editableContentRegion` as the downstream insertion contract. Generated body content must stay inside `editableContentRegion.primary` or a named `availableRegions` slot. Title content must stay inside the title slot / `titleRegion`; citation, bottom banner, and page number must stay inside `footerRegion` or their explicit slots.

Allowed overlap:

- Solid-color backplate shape behind a text box when the text is intentionally inside the shape.
- Placeholder guide and filled content during intermediate editing only.

Forbidden overlap:

- Title with school name, college name, logo, page number, citation footer, or bottom banner.
- Independent text boxes stacked on top of one another.
- One semantic phrase split into multiple overlapping text boxes.
- Images, charts, formulas, route diagrams overlapping title/footer/logo/page-number zones.
- Empty placeholder prompt text or unused picture boxes in final SVG/PPTX.
- Generated content outside the declared editable content region unless a different listed slot is explicitly selected.

Before export, generated decks must run:

```bash
python3 scripts/finalize_svg.py <project_path>
```

The default `cleanup-placeholders` step removes unused PPT prompt text and untouched placeholder guide boxes.

### 4E. Page Number Rule

In user PPTX mode, page numbers follow the template's own slot.

Fallback order:

1. Slide-local `sldNum` placeholder.
2. Layout `sldNum` placeholder.
3. Master `sldNum` placeholder.
4. Built-in academic fallback only when no template page-number slot exists.

Do not force bottom-right placement when the user template has a page-number placeholder elsewhere.
Exactly one visible page number is allowed per slide. If a user-template `sldNum` slot exists, fill that slot and do not add any fallback page number.

### 4F. Anchor Page Stacking Rule

Cover and ending / acknowledgement pages may use one dominant background or hero image. Do not stack a source-paper figure over the authored cover / thanks visual, and do not place a large empty white shape over a large image. If a text readability overlay is needed, mark it as `overlay` or `scrim` and keep it visually intentional.

### 4G. Fidelity And Mirror Notes

Use `fidelity_reference` only when the user asks for high visual fidelity but still wants a reusable template. Preserve load-bearing cropped image wrappers and sprite-sheet geometry.

Use `mirror_reference` only when the user asks for a visual reference page library. Mirror pages are copied as visual references and should not be used as the default automatic academic deck template because they usually lack semantic placeholders.

## Step 5 - Validate Template Assets

Run:

```bash
python3 scripts/svg_quality_checker.py "templates/layouts/<template_id>" --template-mode --format <canvas_format>
```

For PPTX-derived templates, also run:

```bash
python3 scripts/template_import/layout_guard.py "templates/layouts/<template_id>/source_manifest.json" --strict
```

Validation checklist:

- `design_spec.md` exists and has YAML frontmatter.
- Directory name, `template_id`, and index key match exactly.
- `source_manifest.json` or `manifest.json` exists for user PPTX templates.
- Palette values are RGB HEX and marked as user-template priority.
- Layout profiles exist for multiple page needs when the source has them.
- Page-number source is recorded.
- Protected identity regions are recorded.
- No orphan SVG files versus Page Roster.
- Referenced asset files exist.
- Placeholder prompts are marked for removal before export.
- Guard failures are repaired or documented as known limitations.

Do not register until validation passes or the user explicitly accepts known limitations.

## Step 6 - Register Template In Library Index

Run for PPTX-derived templates:

```bash
python3 scripts/template_import/register.py <template_id> --manifest "templates/layouts/<template_id>/source_manifest.json"
```

Run for non-PPTX templates:

```bash
python3 scripts/template_import/register.py <template_id>
```

Expected effects:

- updates `templates/layouts/layouts_index.json`;
- records palette, identity candidates, import policy, and layout profiles when manifest data exists;
- refreshes any auto-managed quick index supported by the local script;
- prints a completion summary.

The index is for discovery. A template directory can still be used by direct path before registration, but it will not appear in normal template selection.

## Step 7 - Output Confirmation

Report template ID, path, source type, mode, manifest attachment, palette priority, page-number rule, read counts, layout profile count, validation / guard status, index status, and known limitations.

For user PPTX templates, explicitly state that downstream PPT generation must fill master/layout placeholders and must not create extra shapes or text boxes when suitable slots exist.

## Connection To Main Pipeline

This workflow is reachable from SKILL.md Step 3: `Template import or creation uses conditional-workflows/create-template.md`.

Downstream consumers:

| Consumer | What it reads |
|---|---|
| SKILL.md Step 3 | `templates/layouts/layouts_index.json`, template `design_spec.md`, manifest policy. |
| SKILL.md Step 6 | `spec_lock.md` page layouts, placeholder fill mode, page-number source. |
| `references/academic/executor-academic.md` | User PPTX template priority, protected regions, text stability. |
| `templates/design_spec_reference.md` | Required project-level layout fields. |
| `templates/spec_lock_reference.md` | Machine-readable template lock and no-overlap policy. |
| `scripts/finalize_svg.py` | Export-time placeholder cleanup. |

If any of these paths change, update this workflow and run a path check before shipping.

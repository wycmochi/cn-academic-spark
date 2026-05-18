# Design Spec Reference
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 4 写项目 design_spec.md 时读取；它提供中文学术 PPT 的人类可读设计说明骨架。

This is the human-readable design narrative for `<project_path>/design_spec.md`. It records rationale, audience, style, color choices, academic narrative structure, page roster, asset plan, and executor handoff details.

The machine-readable execution contract is `<project_path>/spec_lock.md`, generated from `templates/spec_lock_reference.md`. Keep both files synchronized; if they diverge during execution, `spec_lock.md` wins.

Use English section names and keys. Field values may be Chinese when they are final deck content.

If the selected template came from a user-provided PPTX, add a dedicated note in the template strategy: `source: user_pptx_template`, `priority: highest`, and list the extracted RGB HEX palette. Its aesthetic design and parameters override all built-in defaults unless the user explicitly asks otherwise. This includes master/layout placeholder geometry, title position, title box geometry, font family, font size, bold settings, title color, body font scale, logo position, footer rhythm, page-number position, and page density.

For user PPTX templates, use master-placeholder fill mode. Fill the template author's master/layout placeholders and existing slide-local slots; do not create extra free-floating shapes, text boxes, or image frames when a suitable slot exists. Master/layout fixed text, logo, school name, department name, page-number slot, and decorative chrome are protected regions that generated content must not overlap.

For user PPTX templates, copy the manifest-derived `editableContentRegion` into the project spec. It defines the true writable content box after excluding logo, school name, footer, page number, and authored chrome. Generated content must be centered inside that region, not inside the full slide.

## I. Project Information

| Item | Value |
|---|---|
| Project Name | `<project_name>` |
| Canvas Format | `ppt169` / `ppt43` / other confirmed format |
| Page Count | Confirmed page count |
| Academic Route | Route A / B / C / D |
| Paper Type | Discovery / Methods / Resource / Clinical / Materials / Review |
| Narrative Framework | `question-to-evidence` / `problem-to-solution` / `workflow-to-validation` / `design-to-inference` / `property-to-mechanism` / `evidence-map` |
| Target Audience | Defense committee / supervisor / group meeting / course instructor / seminar audience |
| Use Case | Thesis defense / paper presentation / proposal / literature review / course report |
| Source Material | List source files and converted Markdown path |
| Template Candidates | Top 3 from `templates/layouts/layouts_index.json`, including summary quote, matched keywords, rationale, and copy command |
| Selected Template | Template name, source, and whether it came from user PPTX |

If a user PPTX template is selected, include:
- `template_source: user_pptx`
- recognized school logo, school name, department / college name
- extracted palette as RGB HEX values
- extracted master/layout placeholder geometry, title geometry, title font size, title bold setting, title color, body font scale, logo position, footer rhythm, page-number position, and page density when detected
- per-page selected source layout and slot mapping
- per-page `editableContentRegion.primary`, `availableRegions`, `titleRegion`, `footerRegion`, and protected / forbidden regions from `manifest.json`
- overlap audit status and unused-placeholder cleanup notes
- note: "User PPTX template aesthetics and parameters have highest priority over academic defaults, TechnicalRoute defaults, and generic brand defaults."
- note: "Generated content must fill master/layout placeholders or existing slide-local slots; protected master/layout identity regions must not be overlapped."

## II. Canvas Specification

| Property | Value |
|---|---|
| Format | PPT 16:9 unless confirmed otherwise |
| Dimensions | `1280 x 720` for PPT 16:9 |
| viewBox | `0 0 1280 720` |
| Safe Margin | Usually 40-60 px; increase for dense Chinese academic text |
| Title Zone | Usually 56-88 px high, depending on template |
| Content Zone | Main evidence / figure / formula / route diagram area |
| Footer Zone | Citation footer, page number, bottom banner |
| Writable Region | In user PPTX template mode, the `editableContentRegion.primary` rectangle from the import manifest |

Academic pages must reserve footer space for citation markers and bottom banner text. Do not place charts, formulas, or captions into the footer zone.

## III. Visual Theme

### Theme Direction

Record:
- `style_goal`: concise academic, defense-ready, figure-first, template-faithful.
- `tone`: rigorous, readable, restrained.
- `visual_density`: dense / balanced / breathing. For academic paper-to-PPT body pages, default to `dense` unless the page is cover, divider, ending/Q&A, or a deliberate single-message anchor page.
- `template_inheritance`: strict / partial / free design.

### Color Strategy

| Role | HEX | Purpose |
|---|---|---|
| Background | `#......` | Slide background |
| Surface | `#......` | Light panels or figure backplates |
| Primary | `#......` | Section headers, main lines, key icons |
| Secondary | `#......` | Supporting structures |
| Accent | `#......` | Highlights and data emphasis |
| Accent Critical | `#A23B2A` | Bold key text, critical conclusion, warning / contradiction |
| Text | `#......` | Main text |
| Text Secondary | `#......` | Captions, footers, annotations |
| Border | `#......` | Dividers, table rules, node outlines |

Rules:
- The selected template palette wins over generic academic defaults.
- A user-provided PPTX template palette wins over every other palette when present.
- A user-provided PPTX template's detected title style, typography scale, placeholder geometry, logo position, footer rhythm, and page-number position win over built-in academic layout defaults when present.
- Use HEX RGB values only.
- Use 60-30-10 color balance on ordinary pages.
- Keep text contrast at or above 4.5:1.
- Important text may be bold and brick red (`#A23B2A` by default), but do not turn whole paragraphs red.
- TechnicalRoute pages inherit the deck palette unless the route-local lock explicitly maps variables differently.

### Gradient And Background Use

Gradients are optional and should be restrained. If used, specify SVG-compatible `<linearGradient>` or `<radialGradient>` definitions with `stop-opacity`; `rgba()` is forbidden.

Avoid decorative stock backgrounds. Academic decks should use source figures, formula renderings, complex table screenshots, data charts, or route diagrams as the visual center.

## IV. Typography System

### Font Plan

PPTX stores one typeface per run. Every stack must end with a cross-platform pre-installed font.

| Role | CJK | Latin | Fallback Tail |
|---|---|---|---|
| Title | Microsoft YaHei / SimHei / SimSun / KaiTi | Georgia / Cambria / Arial / Times New Roman | serif or sans-serif |
| Body | Microsoft YaHei / SimSun | Arial / Times New Roman | sans-serif or serif |
| Emphasis | Same as title or body | Same as title or body | same family class |
| Formula Label | Microsoft YaHei / SimSun | Times New Roman / Cambria | serif |
| Code / Algorithm | Microsoft YaHei | Consolas / Courier New | monospace |

Write exact per-role font stacks:
- `title_family: ...`
- `body_family: ...`
- `emphasis_family: ...`
- `formula_family: ...`
- `code_family: ...`

Academic defaults:
- Chinese academic oral deck: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Formal thesis / humanities: `SimSun, "Times New Roman", serif` for body, paired with a stronger title stack.
- Formula-heavy pages: render formula title, complete formula, and variable interpretation as one PNG via `scripts/latex_formula_to_png.py --block-json`.

### Font Size Ramp

All sizes use px in SVG. `body` is the baseline.

| Purpose | Ratio To Body | Example body=18 | Example body=22 | Weight |
|---|---:|---:|---:|---|
| Cover title | 2.5-5x | 45-90 | 55-110 | Bold / Heavy |
| Section opener | 2-2.5x | 36-45 | 44-55 | Bold |
| Page title | 1.5-2x | 27-36 | 33-44 | Bold |
| Subtitle | 1.2-1.5x | 22-27 | 26-33 | Semibold |
| Body | 1x | 18 | 22 | Regular |
| Caption / annotation | 0.7-0.85x | 13-15 | 15-19 | Regular |
| Footnote / citation | 0.5-0.65x | 9-12 | 11-14 | Regular |

Dense academic result pages usually use body 16-18 px. Presentation-friendly explanation pages usually use body 20-22 px.

## V. Layout Principles

### Page Structure

- Header area: page title, module number, optional small section marker. When a user PPTX template provides a title placeholder, fill that slot and keep it clear of school name and logo protected regions.
- Content area: one dominant evidence object whenever possible. User PPTX placeholder geometry is authoritative when present; choose a different source layout if the current layout lacks a suitable content or picture slot.
- Footer area: GB/T 7714 citation marker, bottom banner, page number. In user-template mode, generated page numbers follow the source master/layout page-number placeholder when present; otherwise use the built-in academic default.
- User-template writable area: use `editableContentRegion.primary` as the body content box and center the body content within it. Do not position content by eyeballing the full `1280 x 720` canvas.

### Layout Pattern Library

| Pattern | Suitable Academic Use |
|---|---|
| Figure-first split | Result slides with paper figure + interpretation |
| Formula + explanation | One formula block PNG containing role, formula, variable definitions, and intuition; prefer templates from `templates/formula/formula_templates_index.json` |
| Method pipeline | Algorithm / experimental procedure / data workflow |
| Evidence chain | Mechanism or causal evidence across 3-5 steps |
| Table screenshot + takeaway | Complex table too dense to redraw |
| Comparison matrix | Baselines, ablation, subgroup, sensitivity analysis |
| Full-width figure | Important source figure or route diagram |
| Text-light conclusion | Summary, implication, planning / outlook pages |
| Two-column reading | Literature review theme comparison |
| Timeline / milestone | Proposal plan and research schedule |

### Spacing And Shape Discipline

- Safe margin: 40-60 px.
- Built-in content boundary baseline: for PPT 16:9 use left/right/top/bottom margin 60 px, giving a `1160 x 600` content area unless a selected template or user-PPTX manifest overrides it. This mirrors the stable `LAYOUT_MARGINS` contract in `scripts/config.py`.
- Content block gap: 20-40 px.
- Icon-text gap: 8-14 px.
- Card padding: 16-28 px.
- Default shape radius: small; use `shape_radius.default_rx` from `spec_lock.md` (recommended 6 px).
- Do not stack multiple text boxes to form one phrase.
- Text box geometry must match its visible shape; when drawing SVG, use explicit `data-box-x`, `data-box-y`, `data-box-width`, and `data-box-height` for bounded text.
- For text inside visible shapes, also declare `data-shape-x`, `data-shape-y`, `data-shape-width`, and `data-shape-height`. The required inset is `text_box_shape_inset_pt: 5` (`text_box_shape_inset_px: 6.67` at 96 DPI); the text box must be centered within the shape within `10px` tolerance.
- Shape blocks use `rx="6"` by default and carry `themeBlockShadow`: transparency 60%, size 102%, blur 5pt, angle 0, distance 0pt. Do not apply this shadow to logos, citations, footers, page numbers, or full-slide backgrounds.
- Avoid nested cards. Use cards only for repeated items, callouts, and framed tools.

## VI. Icon Usage Specification

Use `templates/icons/` only after a single icon library is selected. Do not mix stylistic icon libraries in one deck.

Record:
- selected library
- stroke width if using outline icons
- approved icon inventory
- page usage

Academic decks may omit icons when figures, formulas, and charts already carry the slide.

## VII. Visualization Reference List

When pages need data visualization or structured diagrams, read `templates/charts/charts_index.json` and record:

```text
Catalog read: <N> templates / <M> categories
Runners-up considered: <key_A> (rejected: <reason>), <key_B> (rejected: <reason>), <key_C> (rejected: <reason>)
```

| Page | Visualization Type | Reference Template | Purpose | Source Evidence |
|---|---|---|---|---|
| P04 | `bar_chart` | `templates/charts/...` | Compare baseline results | Source table / figure |

If no chart template fits, write `no-template-match` and explain the custom layout.

## VIII. Image Resource List

Academic image priority:
1. Source figures extracted from the paper.
2. Source complex table screenshots when redrawing would distort the data.
3. Rendered formula block PNGs from LaTeX plus structured explanation JSON.
4. Self-drawn charts and route diagrams.
5. AI-generated or web-sourced supporting images only when they are necessary and clearly labeled.

| Filename | Dimensions | Ratio | Purpose | Type | Acquire Via | Status | Reference / Citation |
|---|---:|---:|---|---|---|---|---|
| `fig_03_method.png` | `...` | `...` | Method evidence | Source figure | user/source | Existing | `[Author, Year]` |
| `formula_block_01.png` | `...` | `...` | Core equation with interpretation | Formula block PNG | script | Pending | Source equation |
| `route_template_01.svg` | `1280x720` | `1.78` | TechnicalRoute A page | Editable SVG | internal | Pending | Source-grounded |
| `route_ai_01.png` | `1280x720` | `1.78` | TechnicalRoute B page | AI route image | ai | Pending | Custom_gallery + source |

High-priority visual coverage rule:
- Except TechnicalRoute pages, summary pages, and planning / implication pages, every slide must contain at least one meaningful image, source figure, complex table screenshot, chart, or mathematical formula.
- Decorative icons do not satisfy this rule.

## IX. Content Outline

Write pages grouped by numbered modules. Body slide titles must follow:

```text
<module_number> <module_title>: <slide_subtitle_or_evidence_conclusion>
```

For every page, include:
- `page_id`
- `module`
- `title`
- `content_type`
- `page_rhythm`: anchor / dense / breathing
- `layout_source`: template SVG basename or free design
- `chart_reference`: chart key or empty
- `visual_requirement`: source figure / formula / chart / table screenshot / route diagram / exempt
- `bottom_banner_text`
- `citation_footer`
- `speaker_note_goal`
- `editable_content_region` when using a user PPTX template

Example:

```markdown
#### Slide 07 - 4 Model Results: Variable Importance Ranking

- content_type: result_figure
- page_rhythm: dense
- layout_source: 03b_content_image_text
- visual_requirement: source figure or recreated chart
- chart_reference: bar_chart
- bottom_banner_text: Study title / journal / year
- citation_footer: [Author et al., Year]
- editable_content_region: "{x: 60, y: 118, width: 1160, height: 522} or manifest slot id"
- Content:
  - Main claim.
  - Figure interpretation.
  - Limitation or caveat.
```

TechnicalRoute pages must appear as two consecutive pages:
- `<module_number> Research Route: Editable Template Version`
- `<module_number> Research Route: AI Reference Version`

## X. Speaker Notes Requirements

Record:
- total duration
- intended speaking style
- per-slide note file naming
- transitions between modules
- which figure, formula, or table should be explained aloud

Notes should support oral academic reporting, not duplicate slide text.

## XI. Technical Constraints Reminder

SVG generation must follow:
1. Use the confirmed `viewBox`.
2. Use `<rect>` backgrounds.
3. Use `<text>` and `<tspan>` for wrapped text; `<foreignObject>` is forbidden.
4. Use raw Unicode for typography and symbols; escape XML reserved characters.
5. Use `fill-opacity` / `stroke-opacity`; `rgba()` is forbidden.
6. Do not use `<style>`, `class`, `textPath`, `animate*`, `script`, `<iframe>`, or external CSS.
7. `<marker>` is allowed only through compatible definitions in `<defs>`.
8. `<clipPath>` is allowed only for images.
9. `<g opacity>` is forbidden; set opacity on child elements.
10. Text boxes must not overlap or stack unless intentionally layered as a title + subtitle with distinct y-positions. User-template pages must also pass the template overlap audit: title, logo, school name, footer, page number, image, chart, and formula regions must not collide.
11. Formula images must be transparent PNGs generated from LaTeX and explanation JSON whenever possible. Formula title, complete equation, and variable explanations must not be drawn as ordinary text boxes; formula SVG pages must reference `<image data-formula-png="true" data-formula-block-png="true">`, use at most five formula blocks per slide, and separate blocks with gray 1.5pt dashed lines.
12. Every referenced asset path must exist before final export.

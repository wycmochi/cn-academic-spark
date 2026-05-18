# Image Template Draw Prompt
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 生成 A 模板可编辑版时读取；它指导 agent 选择 technicalroute-template 中的 SVG 骨架并用 content.yaml 装配为可编辑路线图。

This file defines Version A: the editable template SVG route diagram. Version A is always generated when the deck needs a TechnicalRoute page, even when Version B AI reference generation also succeeds.

The output must remain editable after SVG to PPTX conversion. Do not rasterize the whole route diagram.

## Required Inputs

- `<route_workdir>/contract.md`: frozen argument and acceptance gate.
- `<route_workdir>/content.yaml`: source-grounded route content.
- `<route_workdir>/spec_lock.md`: route-specific execution lock.
- `templates/technicalroute/templates/templates_index.json`: editable SVG skeleton catalog.
- `references/technicalroute/content-schema.md`: field contract.
- `references/technicalroute/shape-recipes.md`: shape primitives and drawing rules.
- `references/technicalroute/color-typography.md`: inherited deck palette, typography, and radius rules.
- Optional `templates/technicalroute/Custom_gallery/`: style anchors only.

## Selection Chain

1. Read the diagram contract and determine `archetype` plus `sub_variant`.
2. Read the matching archetype reference:
   - `archetype-thinking.md`
   - `archetype-method.md`
   - `archetype-workflow.md`
3. Inspect `templates_index.json`.
4. Use Custom_gallery only as a style and structure hint; never copy its text.
5. Select the best template and write all mapping details into route `spec_lock.md`.
6. Run `generate_route_image.py assemble`.

## Template Selection Score

Choose the template with the strongest fit across:
- `diagram_type`: research route, method framework, thinking map, full-paper workflow, or concept framework.
- `archetype`: `workflow`, `method`, or `thinking`.
- `sub_variant`: selected by the contract or archetype heuristic.
- structural capacity: node count, lane count, stage count, formula count, feedback loops, branches, convergence, or comparison.
- text capacity: each source label fits in one declared slot.
- deck compatibility: palette, typography, bottom banner, citation footer, and modest corner radius.
- PPT conversion safety: simple SVG primitives and editable text.

Never choose a template only because it looks decorative. The selected skeleton must express the paper's actual logic.

## `spec_lock.md` Sections Required For Assemble

Write or update these Markdown sections before running `assemble`. The `assemble` parser reads only `## section` headers and `- key: value` rows. Do not put machine-readable rows inside fenced YAML blocks in the generated route `spec_lock.md`.

```markdown
## source_choice
- template_key: pipeline_with_stages
- template_reason: matches a 4-stage source-grounded workflow
- archetype: workflow
- sub_variant: horizontal-pipeline
- reference_mode: literature
- gallery_ref_1: templates/technicalroute/Custom_gallery/transportation/review-process.jpg

## slot_map
- title: content.yaml.title
- subtitle: content.yaml.subtitle
- columns[0].label: content.yaml.columns[0].label
- columns[1].label: content.yaml.columns[1].label
- columns[2].label: content.yaml.columns[2].label

## color_var_map
- --route-primary: colors.primary
- --route-secondary: colors.secondary
- --route-accent: colors.accent
- --route-muted: colors.muted
- --route-surface: colors.surface
- --route-text: colors.text

## colors
- primary: #1F4E79
- secondary: #2E7D32
- accent: #C00000
- muted: #888888
- surface: #F5F8FB
- text: #1A1A1A

## shape_radius
- node_rx: 6
- dense_node_rx: 3
- card_rx: 6

## glossary_preserve
- term_1: <verbatim term>

## forbidden
- no_gallery_text: No text copied from gallery_refs.
- no_unsupported_content: No unsupported dataset, method, metric, citation, or author name.
```

The exact `slot_map` keys must match placeholder names in the selected template SVG after removing braces. For a template placeholder `{{columns[0].label}}`, write the key as `columns[0].label`, not `{{columns[0].label}}`.

`color_var_map` accepts raw CSS variable names such as `--route-primary`. The script also accepts `var(--route-primary)` for compatibility.

## Slot Map Contract

Each semantic item maps to exactly one visual slot.

Rules:
- Do not split one phrase into several overlapping text boxes.
- Do not create stacked duplicate text boxes on the same node.
- Put all wrapped lines for one node inside one SVG `<text>` element with `<tspan>` rows.
- If a template lacks enough slots, select another template or simplify the content.
- If a label is too long, shorten the visible label and keep the full explanation in `detail`, speaker notes, or caption.
- Preserve glossary terms exactly.

## Template Guidance By Archetype

Thinking:
- `quad`: use icon grids, quadrant matrices, or concept panels.
- `cascade`: use hierarchy, pyramid, or vertical process templates.
- `twin`: use comparison tables, overlap diagrams, or two-column layouts.

Method:
- `core-steps`: use step lists, process flow, or module composition.
- `vertical-stack`: use layered architecture, vertical lists, or hierarchy.
- `formula-grid`: use `method-formula-grid`.
- `mechanism-block`: use input to mechanism to output templates.

Workflow:
- `horizontal-pipeline`: use `pipeline_with_stages`, `process_flow`, or `chevron_process`.
- `twin-track`: use a lane-capable template or adapt module composition.
- `funnel`: use convergent flow or module composition.
- `circular`: use `cycle_diagram`.

## Assembly Command

```bash
python3 scripts/technicalroute/generate_route_image.py assemble --spec-lock <route_workdir>/spec_lock.md --content <route_workdir>/content.yaml --out <route_workdir>/output/route_template_<id>.svg
```

Use `--template-key <key>` only when intentionally overriding `source_choice.template_key` during debugging.

## Output Requirements

- Output path is recorded as `route_template_svg_path`.
- Text remains editable.
- Shapes use modest rounded corners, normally `rx=6` or the value in route `spec_lock.md`.
- The diagram uses parent deck colors, with user PPTX template palette priority.
- There is enough whitespace around labels, arrows, and badges.
- All source labels are in the deck language, with English technical terms preserved when needed.
- The page can be converted to DrawingML without flattening the diagram.
- Version A is followed immediately by Version B in the final PPT.

## Custom_gallery Use

Custom_gallery may influence:
- panel count and grid rhythm;
- flow direction;
- connector style;
- node shape family;
- density;
- accent placement.

Custom_gallery must not supply:
- node text;
- formulas;
- dataset names;
- model names;
- author names;
- institution names;
- citations;
- numbers.

If a reference image contains a phrase that also appears in the user's source, the term must be sourced from `content.yaml` or `glossary_preserve`, not from the reference.

## Failure Handling

If assembly fails:
- Missing template key: choose a valid key from `templates_index.json`.
- Missing placeholder mapping: complete `slot_map`.
- Missing color variable: complete `color_var_map` and `colors`.
- Text overflow: shorten label, change template, or split the content into two route diagrams.
- No fitting template: choose the closest editable skeleton and record the compromise; do not silently replace Version A with only a PNG.

If a candidate SVG is visually suitable but contains no `{{placeholder}}` slots, do not treat a raw copy as a completed Version A. Either choose a placeholderized template, convert the candidate skeleton into a placeholderized route-local SVG, or manually write an editable SVG that follows the candidate structure and `content.yaml`. The final Version A must contain the paper-derived route content, not the template's demo text.


## Default Whole-Paper Workflow Template

For whole-paper 技术路线 / full-paper workflow pages, `templates/technicalroute/templates/pipeline_with_stages.svg` is the default first choice. Read `templates/technicalroute/templates/templates_index.json` first; when the contract archetype is `workflow` and the sub-variant is `horizontal-pipeline`, keep `template_key: pipeline_with_stages` unless the content explicitly requires a loop, chevron-only momentum, or a dated schedule.

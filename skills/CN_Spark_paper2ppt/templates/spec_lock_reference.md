# Spec Lock Reference
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 4 写项目 spec_lock.md 时读取；它提供执行器每页重读的机器可读锁定字段。

This is the author-time skeleton for `<project_path>/spec_lock.md`. The generated project file must be concise, machine-readable, and free of explanatory blockquotes. Executors must re-read project `spec_lock.md` before every SVG page.

When the selected template came from a user-provided PPTX, set `template_priority: user_pptx_template_override`, set `color_priority: user_pptx_template_override`, and copy the extracted RGB HEX palette into `user_template_palette`. The user PPTX design system overrides academic defaults, route-diagram defaults, and generic brand defaults, including master/layout placeholder geometry, title geometry, typography scale, font weight, color, logo position, footer rhythm, page-number position, and page density.

## canvas

```yaml
canvas:
  format: ppt169
  viewBox: "0 0 1280 720"
  width: 1280
  height: 720
  safe_margin:
    left: 50
    right: 50
    top: 42
    bottom: 48
  title_zone_height: 76
  footer_zone_height: 34
  content_bounds:
    x: 60
    y: 60
    width: 1160
    height: 600
```

Common values:
- PPT 16:9: `0 0 1280 720`
- PPT 4:3: `0 0 1024 768`
- PPT 16:9 stable content boundary from `scripts/config.py`: margin 60 px on all sides, content area `x=60, y=60, width=1160, height=600`. User PPTX `editableContentRegion` overrides this.

## template

```yaml
template:
  name: academic_defense
  source: built_in
  layout_root: templates/layouts/academic_defense
  strict_inheritance: true
  user_pptx_template: false
  identity_assets:
    school_logo: ""
    school_name: ""
    department_name: ""
```

If imported from user PPTX, set:

```yaml
template_priority: user_pptx_template_override
template:
  source: user_pptx
  user_pptx_template: true
  strict_inheritance: true
  editable_import_policy:
    master_placeholder_fill_mode: true
    fill_existing_slots_only: true
    allow_extra_generated_shapes: false
    allow_extra_generated_text_boxes: false
    allow_extra_generated_image_frames: false
    use_slide_local_examples_as_slot_evidence: true
    protect_master_layout_identity_regions: true
    remove_unused_placeholder_prompts: true
    master_layout_usage: authoritative_slots_and_protected_regions
    derive_editable_content_region_before_generation: true
  user_template_style_lock:
    title_geometry: inherit_when_detected
    title_font_size: inherit_when_detected
    title_bold: inherit_when_detected
    title_color: inherit_when_detected
    body_font_scale: inherit_when_detected
    placeholder_geometry: inherit_when_detected
    logo_position: inherit_when_detected
    footer_rhythm: inherit_when_detected
    page_number_position: follow_master_layout_sldNum_when_detected
  editable_content_region:
    P02:
      source: manifest
      primary: {x: 60, y: 118, width: 1160, height: 522}
      title_region: null
      footer_region: null
      forbidden_regions: []
```

## academic

```yaml
academic:
  route: A
  paper_type: methods_ai_tool_algorithm
  narrative_framework: problem_to_solution
  citation_style: GB_T_7714
  title_rule: "<module_number> <module_title>: <slide_subtitle_or_evidence_conclusion>"
  visual_coverage_exemptions:
    - technicalroute
    - summary
    - planning_implication
  bottom_banner_text: ""
```

Allowed route values:
- `A`: single academic paper
- `B`: course report / policy report / case analysis
- `C`: proposal / research plan / opening defense
- `D`: literature review / review synthesis

## colors

```yaml
colors:
  bg: "#FFFFFF"
  surface: "#F6F8FB"
  primary: "#1F3864"
  secondary: "#4472C4"
  accent: "#2F75B5"
  accent_secondary: "#70AD47"
  accent_critical: "#A23B2A"
  text: "#1F1F1F"
  text_secondary: "#595959"
  muted: "#888888"
  border: "#D9E2F3"
  formula: "#111111"
color_priority: default
user_template_palette: []
```

Color priority values:
- `user_pptx_template_override`: user PPTX template colors override all other defaults.
- `selected_template`: built-in selected template palette wins over generic academic defaults.
- `academic_default`: use the academic defaults above.
- `free_design`: Strategist-defined free palette.

Important text rule:
- Bold high-priority text and use `colors.accent_critical` only for a concise phrase, conclusion, contradiction, or warning.
- Do not use `accent_critical` as a full-page theme color.

## typography

```yaml
typography:
  font_family: "\"Microsoft YaHei\", \"PingFang SC\", Arial, sans-serif"
  title_family: "\"Microsoft YaHei\", \"PingFang SC\", Arial, sans-serif"
  body_family: "\"Microsoft YaHei\", \"PingFang SC\", Arial, sans-serif"
  emphasis_family: "Georgia, SimSun, serif"
  formula_family: "\"Times New Roman\", Cambria, SimSun, serif"
  code_family: "Consolas, \"Courier New\", monospace"
  body: 18
  title: 34
  subtitle: 24
  annotation: 14
  footnote: 11
```

Rules:
- All sizes are px.
- `body` is the baseline anchor.
- Keep page titles within the title zone; shrink only within the allowed ramp rather than splitting titles into multiple unrelated boxes.
- Mixed Chinese / Latin / numeric SVG text should use `<tspan>` segmentation.

## page_number

```yaml
page_number:
  source: default
  position: bottom_right
  x: 1234
  y: 688
  font_size: 9
  fill: "#888888"
  follow_user_template_slot: true
  fallback_position: bottom_right
  unique_per_slide: true
```

Rules:
- In user PPTX template mode, generated page numbers must follow the slide/layout/master `sldNum` placeholder when one exists.
- Fallback order: slide-local page-number placeholder, layout page-number placeholder, master page-number placeholder, then built-in bottom-right academic default.
- Do not invent a new page-number position when the user template already defines one.

## shape_radius

```yaml
shape_radius:
  default_rx: 6
  card_rx: 6
  callout_rx: 5
  node_rx: 6
  image_rx: 4
```

This is where the default shape corner radius is controlled. Use smaller values for serious academic decks. Increase only when the selected template's authored design requires it.

## text_box_contract

```yaml
text_box_contract:
  require_data_box: true
  forbid_stacked_fragments: true
  max_overlap_ratio: 0.08
  enforce_declared_box_fit: true
  forbid_canvas_overflow: true
  text_box_shape_inset_pt: 5
  text_box_shape_inset_px: 6.67
  text_box_center_tolerance_px: 10
  allow_title_subtitle_overlap: false
  wrap_strategy: single_text_element_with_tspans
  user_template_slot_fill_only: true
  remove_unused_placeholder_prompts: true
```

Executor rules:
- One semantic phrase belongs in one text element.
- Do not output fragments such as `High`, `betweenness, low`, `circuity` as three stacked boxes.
- Visible shape bounds and text box bounds must match.
- Use explicit `data-box-x`, `data-box-y`, `data-box-width`, and `data-box-height` when a text element is bounded by a shape.
- Also write `data-shape-x`, `data-shape-y`, `data-shape-width`, and `data-shape-height` for the visible background shape. The text box must be centered inside that shape and keep at least `5pt` (`6.67px` at 96 DPI) inset on every side.
- In user-template mode, fill existing master/layout placeholders and do not create additional floating text boxes or image boxes unless `layout_source: fallback_template_library` is explicitly selected.
- Remove unused placeholder prompts such as `Click to edit body text`, `Click to add title`, `单击编辑正文内容`, and `单击此处添加标题` before export.

## shape_block_shadow

```yaml
shape_block_shadow:
  required_on_shape_blocks: true
  filter_id: themeBlockShadow
  transparency: 0.60
  size_percent: 102
  blur_pt: 5
  angle_deg: 0
  distance_pt: 0
```

Define `themeBlockShadow` in each SVG and apply it to content cards, evidence blocks, formula cards, and diagram node blocks with `data-shape-block="true"`. Do not apply it to full-slide backgrounds, school logos, footers, citations, or page numbers.

## icons

```yaml
icons:
  library: chunk-filled
  stroke_width: null
  brand_library: ""
  inventory: []
```

Only one stylistic icon library is allowed. Add `simple-icons` only for real brand marks.

## images

```yaml
images:
  fig_01:
    path: images/fig_01.png
    usage: source_figure
    crop: meet
    citation: ""
  formula_block_01:
    path: images/formulas/formula_block_01.png
    usage: formula_block_png
    crop: meet
    citation: ""
```

Image usage values:
- `source_figure`
- `table_screenshot`
- `formula_png`
- `formula_block_png`
- `chart`
- `technicalroute_template_svg`
- `technicalroute_ai_png`
- `ai_supporting_image`
- `web_supporting_image`

Use `crop: meet` for data screenshots, formulas, charts, certificates, and dense diagrams. Use `crop: slice` only when losing edges is acceptable.

## formula_rendering

```yaml
formula_rendering:
  required_when_source_has_equations: true
  reference: references/academic/formula-rendering.md
  output_dir: images/formulas
  render_script: scripts/latex_formula_to_png.py
  complete_equation_as_png: true
  complete_interpretation_in_same_png: true
  require_data_formula_png_attr: true
  require_data_formula_block_png_attr: true
  forbid_complete_equation_text_boxes: true
  forbid_separate_variable_definition_text_boxes: true
  max_formula_blocks_per_slide: 5
  separator_required: true
  separator_stroke: "#A6A6A6"
  separator_stroke_width: 1.5
  separator_dasharray: "8 6"
```

Rules:
- Every formula page must use a rendered formula block PNG containing the role, equation, and variable interpretation.
- SVG text must not duplicate formula roles, `???`, or variable definitions that belong to the formula block.
- Each formula block PNG must appear in `images` with `usage: formula_block_png`.

## technicalroute

```yaml
technicalroute:
  required: false
  pages: []
```

When route diagrams are required:

```yaml
technicalroute:
  required: true
  pages:
    - id: route_01
      module_number: 3
      module_title: Research Route
      content_path: technicalroute/route_01/content.yaml
      spec_lock_path: technicalroute/route_01/spec_lock.md
      template_svg_path: technicalroute/route_01/output/route_template_01.svg
      ai_image_path: technicalroute/route_01/output/route_ai_01.png
      ppt_pages:
        template_version: P08
        ai_reference_version: P09
```

## page_rhythm

```yaml
page_rhythm:
  P01: anchor
  P02: dense
  P03: dense
  P04: breathing
```

Allowed values:
- `anchor`: cover, agenda, section opener, ending.
- `dense`: result, method, table, chart, multi-point evidence.
- `breathing`: single concept, implication, summary, transition.

Do not invent filler `breathing` pages. Every page must serve the academic narrative.

## page_layouts

```yaml
page_layouts:
  P01:
    layout_key: 01_cover
    source: built_in
  P02:
    layout_key: user_layout_02
    source: user_pptx
    slot_map:
      title: layout:title:0
      body: layout:body:1
      page_number: master:sldNum:0
  P07:
    layout_key: 03b_content_image_text
    source: built_in
```

For user PPTX templates, choose a suitable source layout per page based on content needs and available slots. Do not assign every page to the same layout by default. If no user layout fits, set `source: fallback_template_library` and select a compatible built-in layout.

## page_charts

```yaml
page_charts:
  P06: bar_chart
  P10: timeline_horizontal
```

Only include pages that use a real `templates/charts/` key. Do not list `no-template-match`.

## page_requirements

```yaml
page_requirements:
  P01:
    title: "Cover"
    content_type: cover
    visual_requirement: exempt
    citation_footer: ""
    bottom_banner_text: ""
  P07:
    title: "4 Model Results: Variable Importance Ranking"
    content_type: result_figure
    visual_requirement: source_figure_or_chart
    citation_footer: "[Author et al., Year]"
    bottom_banner_text: "Journal / Study / Presenter"
    formula_required: false
```

`visual_requirement` allowed values:
- `source_figure`
- `complex_table_screenshot`
- `formula_png`
- `formula_block_png`
- `chart`
- `technicalroute`
- `image_or_formula`
- `exempt`

Non-exempt pages must have at least one meaningful visual object.

## forbidden

```yaml
forbidden:
  - rgba()
  - "<style>"
  - "class"
  - "<foreignObject>"
  - "textPath"
  - "@font-face"
  - "<animate*>"
  - "<script>"
  - "<iframe>"
  - "<g opacity>"
  - "HTML named entities in text"
  - "stacked text fragments"
  - "unbounded text inside visible shapes"
  - "external technicalroute skill calls"
  - "editable overlays copied from master-only or layout-only objects"
  - "duplicated fixed template text or icons"
  - "unused PowerPoint placeholder prompts in final output"
  - "page numbers that ignore an available user-template sldNum slot"
  - "duplicate page numbers on one slide"
  - "text overflowing declared data-box bounds or slide canvas"
  - "AI-generated images listed in spec/design but not inserted into SVG/PPT"
  - "first/final slide large image or blank-shape stacking"
```

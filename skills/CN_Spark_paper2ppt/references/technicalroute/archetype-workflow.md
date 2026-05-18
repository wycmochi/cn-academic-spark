# TechnicalRoute Archetype Workflow
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 判定路线图为工作流型时读取；它组织数据处理、研究实施、资源构建或项目流程。

Use this archetype when the diagram must explain a complete research chain: source material to processing, method, validation, result, and output. It is the default choice for full-paper technical routes, dataset construction, experimental pipelines, resource-building workflows, and proposal implementation plans.

## Selection Gate

Choose `archetype: workflow` when at least one condition is true:
- The source describes a path from raw material or data to final output.
- There are two or more ordered stages with explicit information flow.
- Multiple inputs converge into a method, model, validation process, or product.
- A proposal or course report needs an implementation roadmap rather than a conceptual argument.

Switch away from workflow when:
- The page mainly explains why the study matters, with no data or method sequence. Use `archetype-thinking.md`.
- The page explains one model, algorithm, formula system, or mechanism. Use `archetype-method.md`.

## Sub-Variants

| sub_variant | Use when | Flow | Template hints |
|---|---|---|---|
| `horizontal-pipeline` | Classic data to process to method to result chain | strict left to right | `pipeline_with_stages`, `process_flow`, `chevron_process` |
| `twin-track` | Two parallel chains converge, such as qualitative plus quantitative, theory plus empirical, or data plus model | two tracks to one merge | choose a template that can hold two lanes; if none fits, use `module_composition` or AI Version B for the visual contrast |
| `funnel` | Many inputs narrow into one model, framework, decision, or output | left fan to center to right | `module_composition`, `client_server_flow`, or a carefully mapped `process_flow` |
| `circular` | Iteration, feedback, repeated calibration, or closed-loop governance is explicit in the source | clockwise or looped | `cycle_diagram` |

Heuristic:
- Default to `horizontal-pipeline`.
- Use `twin-track` only when both tracks remain meaningful before convergence.
- Use `funnel` when the key message is filtering or integration.
- Use `circular` only when the source explicitly states feedback, iteration, or repeated cycles.

## Content Fields

Workflow diagrams may use the generic `nodes`, `edges`, and `lanes` fields from `content-schema.md`, plus the following structured fields when they better match the selected sub-variant:

```yaml
archetype: workflow
sub_variant: horizontal-pipeline | twin-track | funnel | circular
title: ""
subtitle: ""
density: dense
columns:
  - id: C1
    label: ""
    items:
      - name: ""
        source: ""
        logo_hint: ""
    blocks:
      - name: ""
        kind: tool | algorithm | dataset | concept | validation | output
        visual_hint: cylinder_stack | tree | network | heatmap | bar | line | shap | map | document_stack
        sub_label: ""
    arrow_label: ""
tracks:
  - id: TA
    label: ""
    blocks: []
confluence:
  label: ""
  visual_hint: diamond | circle | merge_box
output:
  label: ""
inputs: []
core:
  label: ""
  visual_hint: black_box | neural_net | decision_tree | rule_set | synthesis
stages:
  - id: S1
    label: ""
    icon_hint: ""
```

Each item must be grounded in the uploaded source, user notes, or confirmed `design_spec.md`. Do not add a stage only to make the route look balanced.

## Visual Rules

- Use column or stage titles as short bold labels, normally 14-16 px in a 1280 x 720 SVG.
- Use stage cards, lane surfaces, data-stack icons, small charts, or model glyphs as professional visual summaries. Do not use emoji.
- Use transition arrows between columns. For `horizontal-pipeline`, arrows should carry short italic muted labels when the relation is not obvious.
- Use a dense but controlled composition. Workflow diagrams may fill more canvas than thinking diagrams, but labels cannot overlap connectors.
- Keep connector weight consistent. Use heavier arrows only for the main flow.
- Use no more than four semantic color roles: primary, secondary, accent, muted. Accent must carry meaning.
- Keep ordinary node corners modest. Follow `shape_radius.node_rx` from route `spec_lock.md`; default is 6 px, dense labels can use 3 px.

## Version A Template Mapping

For the editable template version, prefer templates from `templates/technicalroute/templates/templates_index.json` whose `archetype` is `workflow` and whose `sub_variant_hint` matches this file.

Minimum mapping requirements:
- Every workflow stage maps to one visible template slot.
- A column or stage label is not split into independent overlapping text boxes.
- If the chosen template has fewer slots than the workflow needs, simplify the source-grounded content or select another template.
- Record `template_key`, `slot_map`, `color_var_map`, and any selected `gallery_refs` in route `spec_lock.md`.

## Version B AI Prompt Guidance

For the AI reference version, describe the same workflow content in `prompt_ai.md`:
- Name the reading order.
- List all stages and transition labels from `content.yaml`.
- Use Custom_gallery and `style_refs` as style or structure anchors only.
- Preserve source terminology verbatim through `glossary_preserve`.
- Explicitly forbid extra stages, fake datasets, fake metrics, fake citations, and copied reference-image text.

## Do Not

- Do not use a workflow diagram for a purely conceptual introduction page.
- Do not draw a result chart as the whole route diagram; result visuals should be small embedded signs inside the output stage.
- Do not make all stages the same size when the source clearly has a core method or core output.
- Do not add feedback loops unless the paper states an iterative process.
- Do not copy text, numbers, or institution names from Custom_gallery or literature reference images.

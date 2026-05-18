# TechnicalRoute Archetype Method
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 判定路线图为方法型时读取；它指导模型、算法、实验或分析方法路线的节点组织。

Use this archetype when the route diagram explains one model, algorithm, experimental protocol, mathematical method, or mechanism. The goal is to make the method understandable, not to summarize the whole paper.

## Selection Gate

Choose `archetype: method` when at least one condition is true:
- The source contains formulas, symbols, pseudocode, loss functions, or model equations.
- The diagram must explain a single method through ordered steps.
- The page needs to clarify inputs, internal mechanism, assumptions, symbols, and outputs.
- The main risk is that the audience may not understand how the method works.

Use another archetype when:
- The diagram explains the whole paper from data to result. Use `archetype-workflow.md`.
- The diagram explains motivation, conceptual relationships, or literature gaps. Use `archetype-thinking.md`.

## Sub-Variants

| sub_variant | Use when | Flow | Template hints |
|---|---|---|---|
| `core-steps` | One central idea plus 2-4 method steps | core idea to steps | `vertical_list`, `process_flow`, `module_composition` |
| `vertical-stack` | Four to eight ordered layers or algorithm steps | top to bottom | `layered_architecture`, `vertical_list`, `org_chart` |
| `formula-grid` | Two to six formulas need parallel explanation or comparison | grid reading | `method-formula-grid` |
| `mechanism-block` | The method is best shown as input to internal mechanism to output | left to center to right | `client_server_flow`, `module_composition`, `layered_architecture` |

Heuristic:
- Use `core-steps` when there is a short method claim plus a few interpretable steps.
- Use `vertical-stack` when the method is layered or has many ordered operations.
- Use `formula-grid` when formulas are the primary content.
- Use `mechanism-block` when the source emphasizes input, transformation, and output.

## Content Fields

Method diagrams may use generic `nodes`, `edges`, and `lanes`, plus these fields:

```yaml
archetype: method
sub_variant: core-steps | vertical-stack | formula-grid | mechanism-block
title: ""
subtitle: ""
core_idea:
  text: ""
  visual_hint: ""
steps:
  - id: S1
    label: ""
    formula_latex: ""
    formula_inline: ""
    interpretation: ""
    color_role: primary | secondary | accent
formulas:
  - id: F1
    label: ""
    formula_latex: ""
    note: ""
mechanism:
  inputs: []
  process: ""
  process_visual_hint: layered | tree | iterative_loop | black_box | neural_net | rule_engine
  outputs: []
symbols:
  - sym: ""
    desc: ""
assumptions:
  - label: ""
    note: ""
    icon_hint: balance | lock | filter | clock | boundary | sample
```

Formula strings must come from the source or from a faithful LaTeX transcription. If the formula will appear on a normal PPT slide outside Version B AI image generation, render it with `scripts/latex_formula_to_png.py` and insert the transparent PNG. For Version B route images, the AI prompt may ask for LaTeX-style formula rendering, but the formula text still comes from `content.yaml`.

## Visual Rules

- Formula boxes use white or very light gray backgrounds, never saturated fills.
- Method steps use thin borders, modest corners, and one top bar or badge at most.
- Assumption cards are optional and limited to three.
- Symbol legends should be one horizontal strip, not a separate large table.
- Use subtle connectors between steps. Do not use heavy workflow arrows unless the method itself is a pipeline.
- Use brick red only for a concise key warning, constraint, or central finding. Do not recolor all formulas red.
- Keep method labels short. Put explanations in `interpretation`, speaker notes, or captions rather than inside node titles.

## Version A Template Mapping

For editable template assembly:
- Select a method template with enough formula, step, or mechanism slots.
- Map each formula or step to one slot. A single formula cannot be split across multiple text boxes.
- If formulas are too long for a template slot, shorten the visible label and place the full formula on the slide as a separate rendered formula asset.
- Record all formula slot paths in `slot_map` so `assemble` can replace placeholders deterministically.

## Version B AI Prompt Guidance

For AI generation:
- Include the core idea, formula list, symbol list, and assumptions in the prompt.
- Tell the model to preserve formula strings and glossary terms verbatim.
- If Chinese label rendering is unreliable, request minimal labels and add editable SVG labels or formula PNG overlays on the PPT page.
- Use reference images only for layout rhythm, node shapes, connector style, and academic cleanliness.

## Do Not

- Do not invent formulas, symbols, model modules, or assumptions.
- Do not create five or more assumption cards.
- Do not place formula screenshots inside Version A when editable text or formula PNG assets are available.
- Do not use stock photos, gradient panels, large shadows, or decorative icons.
- Do not reuse method names, labels, or numeric examples from Custom_gallery reference images.

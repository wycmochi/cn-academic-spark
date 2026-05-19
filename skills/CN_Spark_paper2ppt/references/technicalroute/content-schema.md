# TechnicalRoute Content Schema
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 写 content.yaml 时读取；它定义技术路线图两种产物共用的结构化内容字段。

`content.yaml` is the single semantic source for both TechnicalRoute outputs:
- Version A editable template SVG, assembled through `image-templatedraw.md`.
- Version B AI reference PNG, generated through `image-aigenerate.md`.

The file must be grounded in the source paper, user material, extracted figures / tables / formulas, and confirmed `design_spec.md`. It must not contain invented nodes, claims, datasets, methods, metrics, or citations.

## Top-Level Required Fields

```yaml
project_name: ""
caller: cn-academic-spark-ppt-engine
language: zh_CN
diagram_type: research_route
archetype: workflow
sub_variant: horizontal-pipeline
title: ""
subtitle: ""
main_question: ""
main_claim: ""
scope_boundary: ""
canvas: "16:9"
density: balanced
source_basis:
  - section: ""
    figure: ""
    table: ""
    formula: ""
    note: ""
glossary_preserve:
  - ""
nodes: []
edges: []
lanes: []
citations: []
uncertainties: []
```

Allowed `diagram_type` values:
- `research_route`
- `method_framework`
- `thinking_map`
- `whole_paper_workflow`
- `concept_framework`

Allowed `archetype` values:
- `workflow`
- `method`
- `thinking`

Allowed `density` values:
- `airy`
- `balanced`
- `dense`

`sub_variant` must follow the selected archetype:
- thinking: `quad`, `cascade`, `twin`
- method: `core-steps`, `vertical-stack`, `formula-grid`, `mechanism-block`
- workflow: `horizontal-pipeline`, `twin-track`, `funnel`, `circular`

## Paper2ppt Integration Fields

Use these fields when the route is created for a specific slide slot:

```yaml
parent_project: ""
parent_module_number: ""
parent_module_title: ""
target_pages:
  version_a:
    title: ""
    svg_path: ""
    target_bbox: "x,y,w,h"
  version_b:
    title: ""
    svg_path: ""
    target_bbox: "x,y,w,h"
bottom_banner_text: ""
citation_footer: ""
```

Rules:
- `target_pages.version_a` and `target_pages.version_b` represent consecutive PPT pages.
- Do not use one page for both versions.
- Page titles follow the main SKILL title rule unless the page is a section divider or appendix.
- `citation_footer` is inherited from the parent academic deck when the diagram uses paper evidence or cited third-party concepts.

## Node Schema

```yaml
nodes:
  - id: n1
    label: ""
    role: input
    evidence_ref: ""
    detail: ""
    importance: normal
```

Allowed `role` values:
- `input`
- `problem`
- `hypothesis`
- `data`
- `method`
- `experiment`
- `model`
- `analysis`
- `validation`
- `result`
- `output`
- `limitation`
- `implication`

Rules:
- Every node label expresses one semantic unit.
- Every node must have a traceable `evidence_ref`.
- Keep labels short enough for route diagrams; put nuance in `detail`.
- Preserve English technical terms when translating them would reduce precision.
- Use `importance: high` only for the central claim, key method, key risk, or major output.

## Edge Schema

```yaml
edges:
  - from: n1
    to: n2
    relation: leads_to
    label: ""
    evidence_ref: ""
```

Allowed `relation` values:
- `leads_to`
- `feeds`
- `tests`
- `validates`
- `compares_with`
- `explains`
- `iterates`
- `constrains`
- `produces`

Rules:
- Edge direction must match the source logic.
- Do not add symmetric arrows unless feedback or iteration is explicit.
- Use edge labels only when they clarify a non-obvious relation.
- Do not use causal language unless the source supports causality.

## Lane Schema

```yaml
lanes:
  - id: lane_1
    label: ""
    node_ids: [n1, n2]
    role: data | method | result | theory | validation | timeline
```

Use lanes for data / method / output bands, time stages, theoretical levels, experiment / model / validation chains, or proposal phases. Do not use lanes as decoration.

## Archetype-Specific Extensions

### Thinking

```yaml
sections:
  - id: P1
    label: ""
    icon_hint: ""
    points: []
    table_2x2:
      - ["", ""]
      - ["", ""]
    contrast:
      old: []
      new: []
bottom_anchor:
  kind: question | claim | call_to_action
  text: ""
top_bridge:
  text: ""
```

### Method

```yaml
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

### Workflow

```yaml
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

## Length And Density Limits

| Field | Normal limit | Action when exceeded |
|---|---:|---|
| `title` | 30 Chinese characters or 12 English words | shorten and preserve meaning |
| `subtitle` | 60 Chinese characters or 24 English words | move details to notes |
| node / panel / step label | 12 Chinese characters or 6 English words | shorten label, keep detail elsewhere |
| one bullet | 25 Chinese characters or 12 English words | split or move to notes |
| `bottom_anchor.text` | 40 Chinese characters or 16 English words | shorten |
| `glossary_preserve` | 20 terms | keep the most critical terms |
| thinking `sections` | 2-6 | choose another sub-variant or merge |
| method `steps` | 1-8 | simplify or use a normal slide instead |
| workflow `columns` | 2-5 | merge adjacent phases |

## Source-Grounding Rules

- Every visible label in Version A and Version B must be traceable to `content.yaml`.
- Every `content.yaml` item must be traceable to source material, user confirmation, or `design_spec.md`.
- If a relation is inferred, planned, uncertain, or only proposed, record that in `uncertainties`.
- For review decks, distinguish literature synthesis from one-paper evidence.
- For proposal decks, distinguish planned work from completed work.

## Validation Checklist

Before generating either output:
- `diagram-contract.md` has been written.
- The chosen archetype reference has been read.
- `content.yaml` contains no gallery-derived text.
- `glossary_preserve` includes terms likely to be mistranslated or abbreviated.
- The content fits at least one editable template or the reason for gallery-only fallback AI generation is recorded.

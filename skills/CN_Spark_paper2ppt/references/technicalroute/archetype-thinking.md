# TechnicalRoute Archetype Thinking
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 判定路线图为思考脉络或概念框架时读取；它组织研究问题、概念、机制、证据和启示之间的关系。

Use this archetype when the diagram must explain the reasoning behind the study: motivation, research gap, conceptual framework, mechanism logic, theory to evidence, or review synthesis. It answers why the research matters and how key concepts relate.

## Selection Gate

Choose `archetype: thinking` when at least one condition is true:
- The source content is mainly background, problem origin, theory, research meaning, or conceptual relations.
- The relation among sections is parallel support, contrast, or conceptual progression.
- The page is a proposal background, literature review synthesis, introduction framework, or mechanism explanation without formulas.

Switch away from thinking when:
- There is a data to model to result chain. Use `archetype-workflow.md`.
- There is one algorithm, formula system, or experimental protocol. Use `archetype-method.md`.

## Sub-Variants

| sub_variant | Use when | Flow | Template hints |
|---|---|---|---|
| `quad` | Four relatively independent angles support one central issue | 2 by 2 parallel grid | `icon_grid`, `ansoff_matrix`, `bcg_matrix` |
| `cascade` | The argument is sequential, such as pain point to gap to contribution to implication | top to bottom or left to right | `pyramid_chart`, `vertical_list`, `process_flow` |
| `twin` | Two sides must be compared, such as existing studies vs this paper, current state vs target state, or two mechanisms | side by side with a bridge | `feature_matrix_table`, `venn_diagram` |

Heuristic:
- Use `quad` for four parallel panels.
- Use `cascade` for three to five ordered reasoning steps.
- Use `twin` for explicit comparison or overlap.

## Content Fields

Thinking diagrams may use generic `nodes`, `edges`, and `lanes`, plus:

```yaml
archetype: thinking
sub_variant: quad | cascade | twin
title: ""
subtitle: ""
sections:
  - id: P1
    label: ""
    icon_hint: ""
    points:
      - ""
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

Field meanings:
- `label` is the panel heading and must be used as written.
- `points` should contain short source-grounded statements, normally no more than four per section.
- `table_2x2` replaces `points` when the section itself is a matrix.
- `bottom_anchor` is optional. Draw it only when the source or contract provides a clear central question, claim, or action.
- `top_bridge` is mainly for `twin` diagrams and should summarize the comparison logic.

## Visual Rules

- `quad` panels are parallel. Do not draw heavy arrows between them.
- `cascade` panels are sequential. Use light arrows or chevrons to show progression.
- `twin` diagrams need visually balanced sides and a clear comparison bridge.
- Each panel may have one simple line icon. Do not use emoji or stock photos.
- Use modest rounded corners, thin borders, and enough inner padding.
- Keep bottom anchors concise and semantic. Do not use a banner just for decoration.
- Use the parent deck palette and route `spec_lock.md`; user-provided PPTX template colors override fallback palettes.

## Version A Template Mapping

For editable template assembly:
- Match `quad` to templates that naturally support four concept cards or a 2 by 2 matrix.
- Match `cascade` to hierarchy, pyramid, or vertical process templates.
- Match `twin` to comparison matrix, overlap, or two-column templates.
- Map each section to exactly one slot and keep each label in one editable text element.

## Version B AI Prompt Guidance

For AI generation:
- State whether the argument is parallel, sequential, or comparative.
- Include `sections`, `bottom_anchor`, and `top_bridge` as the content truth.
- Preserve glossary terms exactly.
- Ask for a restrained academic infographic, not a marketing illustration.
- Use Custom_gallery or literature references only for structure and style.

## Do Not

- Do not add data-processing stages to a conceptual thinking map.
- Do not add formulas unless the source explicitly uses them as conceptual anchors.
- Do not create a bottom banner when no anchor text exists.
- Do not make `quad` look causal through unnecessary arrows.
- Do not copy reference-image text, labels, author names, place names, or numbers.

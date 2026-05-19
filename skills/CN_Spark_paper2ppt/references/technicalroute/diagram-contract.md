# Diagram Contract
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 的 contract-first 阶段读取；它约束技术路线图的目标、边界、节点、连线和用户确认项。

Every TechnicalRoute diagram must start with a written contract before template selection, prompt construction, AI generation, or PPT insertion. The contract freezes the argument so the diagram remains an academic claim rather than decoration.

In the paper2ppt workflow, user confirmation is required only when a blocking ambiguity remains or when the user explicitly asked to approve diagrams before generation. Otherwise, write the contract, record conservative assumptions, and continue.

## Why The Contract Exists

Route diagrams commonly fail when:
- the model adds unsupported nodes;
- key stages are missing;
- the panel count is too high for the slide;
- colors carry no meaning;
- reference images leak unrelated text into the output;
- the generated diagram expresses a different claim than the paper.

The contract prevents these failures by fixing purpose, scope, content, references, and acceptance criteria before either Version A or Version B is produced.

## Required Contract Path

Write:

```text
<route_workdir>/contract.md
```

Then derive:

```text
<route_workdir>/content.yaml
<route_workdir>/spec_lock.md
<route_workdir>/prompt_ai.md
```

`content.yaml` must not contain a visible item that is absent from the contract. If a new item is needed, update the contract first.

## Contract Template

```markdown
# Diagram Contract - <route_job_id>

## 1. Core Claim
<One sentence with a strong verb. State what this diagram must defend.>

## 2. Diagram Identity
parent_project:
parent_module:
diagram_type:
archetype:
sub_variant:
audience:
purpose:
scope_boundary:

## 3. Archetype Rationale
reason:
alternative_rejected:

## 4. Panel / Stage Mapping
<For thinking: P1/P2/P3/P4 or cascade/twin sections.>
<For method: core idea, S1...Sn, formulas, assumptions, symbols.>
<For workflow: columns/tracks/inputs/core/stages/output and transition labels.>

## 5. Glossary Preserve
- <term that must appear verbatim>

## 6. Source Evidence
- <node or edge> -> <paper section / figure / table / formula / user note>

## 7. Forbidden Additions
- <dataset, method, variable, arrow type, citation, or claim that must not appear>

## 8. Visual Contract
canvas:
density:
palette_source: parent_deck | user_pptx_template | fallback_named_palette
color_roles:
  primary:
  secondary:
  accent:
  muted:
typography:
shape_radius:
emphasis_usage:

## 9. Reference Mode
mode: literature_only | gallery_only_fallback
expected_refs_count:
gallery_refs:
style_refs:
fallback_note:
source_gate: seed_sites_literature_first_then_custom_gallery_only

## 10. Dual Output Lock
version_a: editable template SVG through image-templatedraw.md
version_b: AI reference PNG through image-aigenerate.md
insertion: consecutive PPT pages

## 11. Reviewer Risk
Q1. What is the most likely challenge from the audience?
A1.
Q2. If panel count were halved, which part of the argument would fail?
A2.
Q3. Do any third-party methods, data, or concepts require citation footers?
A3.
Q4. Does color encode meaning, or is it decorative?
A4.

## 12. Acceptance Gate
- [ ] Every visible text item maps to Section 4.
- [ ] No node, number, author, citation, or dataset appears outside this contract.
- [ ] Every glossary term appears verbatim where required.
- [ ] Palette and typography follow Section 8.
- [ ] Reference images are used only for structure and style.
- [ ] Version A and Version B both exist and are inserted consecutively.
```

## Blocking Ambiguity Rules

Ask the user before continuing only when one of these is true:
- The main question cannot be determined from the source.
- The requested diagram type conflicts with the source.
- The source includes several possible routes and no dominant route is obvious.
- The diagram would require missing content, such as an unstated dataset or method.
- The user explicitly requested approval before route generation.

When ambiguity is non-blocking, choose the conservative interpretation and record it in `uncertainties` and `fallback_note`.

## Forbidden Additions

Record concrete forbidden additions, not generic warnings. Examples of useful forbidden items:
- datasets not used by the paper;
- methods not described by the paper;
- causal arrows not supported by evidence;
- decorative stages created only to fill space;
- institution, logo, author, or place names copied from references;
- numbers, citations, captions, or labels from Custom_gallery or literature images.

## Reference Integrity

Custom_gallery and seed-sites literature references are style and structure anchors only. They never become semantic sources. TechnicalRoute Version B must not use user-uploaded images, exported PPT screenshots, assembled SVGs, editable Version A pages, PPT/PPTX templates, or any file outside `style_refs/manifest.json` and `templates/technicalroute/Custom_gallery/gallery_index.json` as AI references. The contract must explicitly state that all node labels, formulas, dataset names, model names, place names, author names, and numeric values come from the uploaded source or confirmed user material.

## Dual Output Lock

Every accepted contract must require both outputs:
- Version A: editable template SVG using `image-templatedraw.md` and `generate_route_image.py assemble`.
- Version B: AI reference PNG using `image-aigenerate.md` and `generate_route_image.py run-ai-variant`.

Version B is not a fallback for Version A. Both are generated and inserted as two consecutive PPT pages so the user can later choose which route diagram style to keep.

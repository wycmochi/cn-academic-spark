# TechnicalRoute Design Spec Reference
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 写路线图局部 design_spec 时读取；它定义技术路线图页面的设计字段和继承关系。

This file defines the human-readable design narrative for one internal TechnicalRoute job. It is used only inside `CN_Spark_paper2ppt`; do not call an external technicalroute skill.

Route-level design specs must inherit the project palette, typography, citation/footer discipline, page size, and shape radius unless the user explicitly confirms otherwise.

## Required Reference Reads

Before writing a route-level design spec, read:
- `references/technicalroute/content-schema.md`
- `references/technicalroute/diagram-contract.md`
- `references/technicalroute/seed_sites.json`
- `references/technicalroute/seed_urls.md`
- `references/technicalroute/image-templatedraw.md`
- `references/technicalroute/image-aigenerate.md`
- `references/technicalroute/qa-checklist.md`

Read archetype details only as needed:
- `references/technicalroute/archetype-workflow.md`
- `references/technicalroute/archetype-method.md`
- `references/technicalroute/archetype-thinking.md`

## I. Route Job Information

| Item | Value |
|---|---|
| Route Job ID | `route_01` |
| Parent Project | `<project_name>` |
| Parent Module | Module number and module title |
| Page Pair | Template Version page + AI Reference Version page |
| Diagram Purpose | research route / method framework / thinking map / whole-paper workflow / concept framework |
| Source Scope | Which paper sections, figures, formulas, or tables support this route |
| Output Language | Chinese labels with preserved English technical terms when needed |

## II. Diagram Type And Archetype

Choose one `diagram_type`:
- `research_route`: research design from question to data, method, result, conclusion.
- `method_framework`: model, algorithm, architecture, or analytical framework.
- `thinking_map`: conceptual logic, literature synthesis, theoretical argument.
- `whole_paper_workflow`: full article pipeline from input to output.
- `concept_framework`: constructs, variables, mechanisms, and relations.

Choose one `archetype`:
- `workflow`: staged process, sequence, branch, feedback, input-output.
- `method`: architecture, layers, modules, data flow, model training / inference.
- `thinking`: conceptual categories, causal logic, evidence map, theoretical relation.

Record why the selected archetype fits the paper. If multiple archetypes fit, list the runner-up and why it was rejected.

## III. Content Contract

Summarize the content from `<route_workdir>/content.yaml`:

| Field | Requirement |
|---|---|
| `main_question` | One sentence, source-grounded |
| `inputs` | Data, samples, literature, variables, or materials |
| `steps` | Ordered stages or conceptual moves |
| `methods` | Models, experiments, algorithms, or analytical tools |
| `outputs` | Results, products, evaluation metrics, or conclusions |
| `edges` | Directional relations between nodes |
| `evidence_refs` | Source figure, table, section, formula, or page reference |
| `uncertainties` | Known limitations or assumptions |

Rules:
- Every node must trace back to the source or confirmed user instruction.
- Do not invent stages to make the diagram look balanced.
- Keep node labels short enough for PPT display.
- Use a separate annotation or caption for nuance; do not overload node text.

## IV. Reference Mode And Style Sources

Choose one reference mode from `seed_urls.md`. For online academic search, the concrete site list must come from `references/technicalroute/seed_sites.json` through `literature_search.py emit-plan`; do not write a separate site list here:
- `literature`: online academic / institutional visual references are available.
- `offline`: user uploaded at least three reference images; use `literature_search.py offline --hints <folder>`.
- `atlas_only`: no online references and no sufficient user images; use `templates/technicalroute/Custom_gallery/`.

Record:
- search topic and discipline
- selected seed sites from `seed_sites.json` or offline hint folder
- `style_profile.md` path
- 1-3 `gallery_refs` from `templates/technicalroute/Custom_gallery/`

Custom_gallery is a style and structure anchor for Version B AI generation and a structural hint for Version A. Do not invent gallery filenames. Do not copy gallery raster content directly into the editable SVG.

## V. Version A - Editable Template SVG

Read `references/technicalroute/image-templatedraw.md`.

Record:
- `template_index_read`: true / false
- candidate templates considered
- selected `template_key`
- selected SVG path
- structural match rationale
- node count / slot count fit
- `slot_map`
- `color_var_map`
- output path `route_template_svg_path`

Design constraints:
- All labels remain editable SVG text.
- One semantic label must remain one text element with `<tspan>` wrapping.
- Do not stack text fragments over one node.
- Use project `shape_radius.node_rx`, usually 6 px.
- Keep arrows and connectors editable.
- Avoid decorative complexity that makes PPT conversion unstable.

## VI. Version B - AI Reference Image

Read `references/technicalroute/image-aigenerate.md`.

Record:
- prompt file path
- source-grounded node list included in prompt
- selected style references from `style_profile.md` and `gallery_refs`
- aspect ratio
- output path `route_ai_image_path`

Prompt constraints:
- Include the paper topic, diagram purpose, node list, relation logic, visual style, deck palette, label language, and no-invention rule.
- Use Custom_gallery and literature/offline references as style anchors only.
- The AI image may be raster, but its labels must be legible at PPT size.
- It should differ meaningfully from Version A while conveying the same article logic.

## VII. Page Pair Embedding Plan

Both outputs go into the final PPT as two consecutive pages.

| Page | Title | Asset | Layout |
|---|---|---|---|
| Template Version | `<module_number> Research Route: Editable Template Version` | `route_template_svg_path` | Full-width editable SVG |
| AI Reference Version | `<module_number> Research Route: AI Reference Version` | `route_ai_image_path` | Full-width image with caption |

Rules:
- Keep both pages inside the same academic module.
- Mark both pages as `visual_requirement: technicalroute`.
- TechnicalRoute pages are exempt from the general "image or formula" requirement because they are route visual pages by definition.
- Preserve bottom banner and citation footer discipline from the parent deck.

## VIII. Palette, Typography, And Shape Use

Inherit:
- project `colors`
- project `typography`
- project `shape_radius`
- user PPTX template palette if active

Route-specific additions:
- Use `accent_critical` only for one critical conclusion, risk, or decision point.
- Keep connector strokes readable but not heavier than the template's authored visual language.
- Node labels should use the deck body font; section labels may use the title font.
- Formula fragments should be rendered as PNG if they are true formulas, not typed as approximate plain text.

## IX. QA Notes

Run `references/technicalroute/qa-checklist.md` after both outputs are generated.

Must pass:
- source-grounded content
- correct route archetype
- no invented file references
- no external technicalroute skill calls
- Version A is editable SVG
- Version B is generated / raster reference image
- both pages are consecutive in the deck
- text is legible
- no text stacking or overflow
- all paths exist


## Version B slide embedding rule

The `route_ai_image_path` file is only an intermediate artifact. Normal execution must call `generate_route_image.py run-ai-variant --refs-plan <route_workdir>/style_refs/route_ai_refs.json --out-svg <project_path>/svg_output/<NN>_route_ai.svg` so the generated PNG is embedded into the Version B PPT page in the same step. `create-ai-slide` is manual recovery only. The generated SVG must contain `<image id="technicalroute-ai-reference-image" href="data:image/png;base64,...">`. Do not leave a path-only image href in the Version B slide.

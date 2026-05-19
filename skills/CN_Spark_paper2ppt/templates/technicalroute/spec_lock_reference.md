# TechnicalRoute Spec Lock Reference
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 写路线图局部 spec_lock 时读取；它提供机器可读的模板、槽位、颜色和输出路径锁定格式。

This is the machine-readable lock skeleton for one internal TechnicalRoute job. It controls both Version A editable template SVG and Version B AI reference image.

Important parser rule: `scripts/technicalroute/generate_route_image.py assemble` reads only Markdown `## section` headers and `- key: value` rows. In the generated route `spec_lock.md`, do not put machine-readable rows inside fenced YAML blocks.

## route_job

- id: route_01
- parent_project: <project_name>
- parent_module_number: 3
- parent_module_title: Research Route
- page_template_version: P08
- page_ai_reference_version: P09
- external_skill_call_allowed: false

## diagram

- diagram_type: research_route
- archetype: workflow
- sub_variant: horizontal-pipeline
- purpose: Explain the paper research route from question to evidence.
- output_language: zh_CN
- preserve_english_terms: true

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

## paths

- route_workdir: technicalroute/route_01
- contract_path: technicalroute/route_01/contract.md
- content_path: technicalroute/route_01/content.yaml
- design_spec_path: technicalroute/route_01/design_spec.md
- spec_lock_path: technicalroute/route_01/spec_lock.md
- style_profile_path: technicalroute/route_01/style_refs/style_profile.md
- prompt_ai_path: technicalroute/route_01/prompt_ai.md
- route_template_svg_path: technicalroute/route_01/output/route_template_01.svg
- route_ai_image_path: technicalroute/route_01/output/route_ai_01.png
- route_template_slide_svg_path: svg_output/08_route_template.svg
- route_ai_slide_svg_path: svg_output/09_route_ai.svg
- audit_report_path: technicalroute/route_01/audit_report.md

## references

- content_schema: references/technicalroute/content-schema.md
- diagram_contract: references/technicalroute/diagram-contract.md
- archetype_reference: references/technicalroute/archetype-workflow.md
- color_typography: references/technicalroute/color-typography.md
- shape_recipes: references/technicalroute/shape-recipes.md
- seed_sites: references/technicalroute/seed_sites.json
- seed_urls: references/technicalroute/seed_urls.md
- template_draw_prompt: references/technicalroute/image-templatedraw.md
- ai_generate_prompt: references/technicalroute/image-aigenerate.md
- qa_checklist: references/technicalroute/qa-checklist.md

## reference_mode

- mode: literature_only | gallery_only_fallback
- online_search_plan: technicalroute/route_01/style_refs/search_plan.md
- seed_sites_path: references/technicalroute/seed_sites.json
- gallery_index_path: templates/technicalroute/Custom_gallery/gallery_index.json
- selected_seed_site_1: <optional site name from seed_sites.json>
- gallery_ref_1: templates/technicalroute/Custom_gallery/<discipline>/<file>
- gallery_ref_2: <optional>
- style_refs_manifest: technicalroute/route_01/style_refs/manifest.json
- fallback_note: <why gallery_only_fallback was chosen; include completed search proof and nearest-intent gallery reason>

Allowed route-level `mode` values:
- `literature_only`: seed-sites academic / institutional raster references were used.
- `gallery_only_fallback`: Custom_gallery raster anchors were used only after the completed seed-sites search produced zero usable literature refs.

When calling `generate_route_image.py prompt`, use `--reference-mode literature_only` or `--reference-mode gallery_only_fallback`. User-uploaded references, PPT/PPTX pages, SVG templates, exported slides, and editable Version A pages must not be recorded as Version B AI references.

## source_choice

- template_key: pipeline_with_stages
- template_svg_path: templates/technicalroute/templates/pipeline_with_stages.svg
- template_reason: matches the source-grounded workflow stage count and left-to-right logic
- candidate_1: pipeline_with_stages
- candidate_1_reason: strongest structural fit
- rejected_1: cycle_diagram
- rejected_1_reason: source does not describe iteration

`source_choice.template_key` is the primary key consumed by `assemble`. Legacy `## template_version` with `- template_key: ...` is still accepted by the script for compatibility, but new route locks should use `source_choice`.

## content_contract

- main_question: <main question>
- main_claim: <one-sentence claim>
- node_count: 0
- edge_count: 0
- lane_count: 0
- no_invention: true
- source_grounding_required: true

Every node and edge must be traceable to `content.yaml` and `contract.md`.

## slot_map

- title: content.yaml.title
- subtitle: content.yaml.subtitle
- columns[0].label: content.yaml.columns[0].label
- columns[1].label: content.yaml.columns[1].label
- columns[2].label: content.yaml.columns[2].label
- nodes[0].label: content.yaml.nodes[0].label

Rules:
- The left side is the template placeholder name without braces.
- The right side is a dotted `content.yaml` path.
- One slot maps to one semantic item.
- One semantic label should not be split into multiple text boxes.
- If a node must wrap, use one text element with multiple `<tspan>` lines.
- If node count exceeds available slots, select another template or revise `content.yaml`.

## color_var_map

- --route-bg: colors.bg
- --route-surface: colors.surface
- --route-primary: colors.primary
- --route-secondary: colors.secondary
- --route-accent: colors.accent
- --route-critical: colors.accent_critical
- --route-text: colors.text
- --route-border: colors.border

The script accepts raw CSS variable names such as `--route-primary` and compatibility keys such as `var(--route-primary)`.

## colors

- bg: #FFFFFF
- surface: #F6F8FB
- primary: #1F3864
- secondary: #4472C4
- accent: #2F75B5
- accent_critical: #A23B2A
- text: #1F1F1F
- text_secondary: #595959
- border: #D9E2F3
- source: inherited_from_project_or_user_template

If the parent project uses a user PPTX template palette, these variables must resolve through that palette first.

## typography

- title_family: Microsoft YaHei, PingFang SC, Arial, sans-serif
- body_family: Microsoft YaHei, PingFang SC, Arial, sans-serif
- latin_family: Times New Roman, serif
- annotation_family: Microsoft YaHei, PingFang SC, Arial, sans-serif
- node_label: 16
- lane_label: 18
- annotation: 12

Use the parent deck font stacks unless route-local design explicitly overrides them.

## shape_radius

- node_rx: 6
- dense_node_rx: 3
- group_rx: 6
- lane_rx: 4
- image_rx: 4

This controls route diagram corner roundness. Keep values modest for academic PPT.

## glossary_preserve

- term_1: <verbatim source term>
- term_2: <verbatim source term>

Each term must remain unchanged in prompts and visible labels.

## forbidden

- no_external_skill: Do not call an external technicalroute skill.
- no_gallery_text: Do not copy text, numbers, formulas, dataset names, model names, author names, citations, or place names from Custom_gallery or style references.
- no_invention: Do not add unsupported datasets, methods, variables, or causal claims.
- no_stacked_text_fragments: Do not split one semantic phrase into overlapping text boxes.

## ai_reference_version

- enabled: true
- prompt_path: technicalroute/route_01/prompt_ai.md
- backend: openai
- model: gpt-image-2
- aspect_ratio: 16:9
- image_size: 2K
- output_filename: route_ai_01
- output_path: technicalroute/route_01/output/route_ai_01.png
- style_source_1: technicalroute/route_01/style_refs/style_profile.md
- refs_plan: technicalroute/route_01/style_refs/route_ai_refs.json
- gallery_ref_1: <optional>
- no_invention: true
- refs_required_when_declared: true
- allow_no_ref_fallback: false

Version B must be generated from article content plus one mutually exclusive reference class recorded in `style_refs/route_ai_refs.json`: `literature_only` manifest raster route figures listed in `style_refs/manifest.json` after collection from a `seed_sites.json`-driven search plan, or `gallery_only_fallback` discipline-matched Custom_gallery raster anchors only when the manifest has zero usable refs. It must not mix the two classes and must not be a screenshot of Version A. `run-ai-variant` must pass `--refs-plan <route_workdir>/style_refs/route_ai_refs.json` and write `<project_path>/svg_output/_direct_image_slides.json` with `--direct-slide-manifest <project_path>/svg_output/_direct_image_slides.json --after-svg-stem <NN>_route_template`; the PPTX exporter then inserts the generated PNG as a direct picture slide without an SVG wrapper.

## embedding

- consecutive_pages_required: true
- template_version_title: 3 Research Route: Editable Template Version
- ai_reference_version_title: 3 Research Route: AI Reference Version
- template_version_visual_requirement: technicalroute
- ai_reference_version_visual_requirement: technicalroute
- template_slide_svg_path: svg_output/08_route_template.svg
- ai_direct_slide_manifest: svg_output/_direct_image_slides.json
- ai_slide_must_be_direct_pptx_picture: true
- citation_footer: <inherited>
- bottom_banner_text: <inherited>

## qa

- run_checklist: references/technicalroute/qa-checklist.md
- require_editable_template_svg: true
- require_ai_png: true
- require_source_grounding: true
- require_existing_paths: true
- forbid_external_technicalroute_skill: true
- forbid_stacked_text_fragments: true
- max_label_lines: 3

## commands

- contract: python3 scripts/technicalroute/generate_route_image.py contract --out <route_workdir>/contract.md --project <project_name> --archetype <thinking|method|workflow>
- assemble: python3 scripts/technicalroute/generate_route_image.py assemble --spec-lock <route_workdir>/spec_lock.md --content <route_workdir>/content.yaml --out <route_workdir>/output/route_template_01.svg
- prompt: python3 scripts/technicalroute/generate_route_image.py prompt --archetype <archetype> --content <route_workdir>/content.yaml --style <route_workdir>/style_refs/style_profile.md --reference-mode <literature_only|gallery_only_fallback> --out <route_workdir>/prompt_ai.md
- prepare_ai_refs: python3 scripts/technicalroute/literature_search.py prepare-ai-refs --topic "<paper title / keywords>" --discipline <discipline> --archetype <thinking|method|workflow> --out <route_workdir>/style_refs
- run_ai_variant: python3 scripts/technicalroute/generate_route_image.py run-ai-variant --prompt <route_workdir>/prompt_ai.md --backend openai --model gpt-image-2 --aspect_ratio 16:9 --image_size 4K --filename route_ai_01 --out <route_workdir>/output --refs-plan <route_workdir>/style_refs/route_ai_refs.json --direct-slide-manifest <project_path>/svg_output/_direct_image_slides.json --after-svg-stem 08_route_template
- audit: python3 scripts/technicalroute/generate_route_image.py audit --image <route_workdir>/output/route_ai_01.png --content <route_workdir>/content.yaml --contract <route_workdir>/contract.md --out <route_workdir>/audit_report.md

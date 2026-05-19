---
name: cn-academic-spark-ppt-engine
description: >
  Convert a complete academic source package, such as a paper, report, proposal,
  review outline, PDF, Word document, Markdown file, or pasted text, into a
  Chinese academic .pptx deck. Use this skill for thesis defense, group meeting,
  journal club, course report, proposal defense, and literature review slides.
  The pipeline is Source to Outline to Design Spec to SVG to DrawingML PPTX,
  with editable vector output, GB/T 7714 citation footers, speaker notes, bottom
  banners, academic route selection, and an internal TechnicalRoute module for
  research-route / framework diagrams. Do not call an external technicalroute
  skill; this skill contains the full route-diagram pipeline.
---

# CN Academic Spark PPT Engine
document explanation(It doesn't affect the process, it only helps with understanding）：本文件是 skill 主入口；当用户提供学术材料并要求生成中文学术 PPT 时触发；它串联 source 解析、模板选择、学术大纲、图片获取、内置 TechnicalRoute、SVG 生成、质检和 PPTX 导出。

## Core Contract

Output a real editable `.pptx`, not a Markdown outline and not flattened slide screenshots. Generate editable SVG pages first, then convert them to native DrawingML using `scripts/svg_to_pptx.py`.

Hard requirements:
- Run steps serially. Each step's output is the next step's input.
- Stop at blocking checkpoints when user confirmation is required.
- Re-read project `spec_lock.md` before generating every SVG page.
- The main agent writes the final SVG pages sequentially. Do not delegate bulk SVG generation to subagents.
- Use mixed-font `<tspan>` segmentation for Chinese / Latin / numeric SVG text. See `references/academic/citation-style.md`.
- Keep `design_spec.md` and `spec_lock.md` keys in English. Field values may be Chinese.
- Do not load or call any external `technicalroute` skill. Use the internal `scripts/technicalroute/`, `references/technicalroute/`, and `templates/technicalroute/` folders only.
- Cover slides are metadata-only: show the material title/topic, report type, presenter/defense candidate, advisor, institution, date, and paper/source/DOI when applicable. Do not place source figures, formulas, route diagrams, result charts, method summaries, or research-content teasers on the cover.

## Main Scripts

| Script | Purpose |
|---|---|
| `scripts/source_to_md/pdf_to_md.py` | Convert PDF to Markdown and extract academic figures. |
| `scripts/source_to_md/doc_to_md.py` | Convert DOCX / EPUB / HTML to Markdown. |
| `scripts/source_to_md/excel_to_md.py` | Convert spreadsheets to Markdown tables. |
| `scripts/source_to_md/ppt_to_md.py` | Convert PPTX to Markdown. |
| `scripts/source_to_md/web_to_md.py` | Convert web pages to Markdown. |
| `scripts/project_manager.py` | Initialize, validate, and import project assets. |
| `scripts/template_import/cli.py` | Convert user PPTX templates into manifest / SVG references for template registration. |
| `scripts/template_import/layout_guard.py` | Audit user PPTX template slots, protected regions, page-number slots, unused placeholders, and overlap risks. |
| `scripts/analyze_images.py` | Analyze source figures and recommend captions / placement. |
| `scripts/image_gen.py` | Generate AI images when required by the asset plan. |
| `scripts/latex_formula_to_png.py` | Render extracted LaTeX formulas to transparent PNG assets for PPT insertion. |
| `scripts/technicalroute/generate_route_image.py` | Internal route-diagram commands: `contract`, `prompt`, `assemble`, `run-ai-variant`, `embed`, `audit`. |
| `scripts/technicalroute/literature_search.py` | Build literature / offline / atlas style references for route diagrams. |
| `scripts/svg_quality_checker.py` | Validate SVG compatibility. |
| `scripts/total_md_split.py` | Split speaker notes by slide. |
| `scripts/notes_to_docx.py` | Export speaker notes as a standalone DOCX, one section per slide. |
| `scripts/finalize_svg.py` | Remove unused template placeholders, embed icons, align / embed images, flatten text, and normalize SVG. |
| `scripts/svg_to_pptx.py` | Convert SVG pages to editable DrawingML PPTX. |
| `scripts/pptx_openability_check.py` | Validate exported PPTX package relationships, notes master parts, content types, and current-user read/open permission. |
| `scripts/skill_integrity_check.py` | Developer maintenance audit for route/workflow/index/formula/TechnicalRoute/PPTX export integrity. |
| `scripts/update_spec.py` | Propagate theme color and typography changes. |

## Template Indexes

Always inspect `templates/resource_index.json` first, then the resource-specific index before choosing assets:
- `templates/resource_index.json`: compact map of resource indexes, selection stages, and downstream consumers.
- `templates/layouts/layouts_index.json`: deck layout templates.
- `templates/charts/charts_index.json`: reusable chart and framework SVGs.
- `templates/formula/formula_templates_index.json`: formula explanation block templates; use for one PNG containing formula title, formula, and variable interpretation.
- `templates/technicalroute/templates/templates_index.json`: editable TechnicalRoute SVG skeletons.
- `templates/technicalroute/Custom_gallery/`: style anchors for AI-generated route diagrams.
- `templates/icons/`: icon libraries.

Academic defaults: `academic_defense` for defense / group meeting / journal club, `medical_university` for medicine and life science, and `government_blue` for proposal defense.

## References To Load On Demand

Academic references:
- `references/academic/paper-type-guidance.md`: classify paper type, choose narrative, and write numbered slide titles.
- `references/academic/route-academic-paper.md`: Route A, single academic paper.
- `references/academic/route-course-report.md`: Route B, course report or case / policy report.
- `references/academic/route-proposal.md`: Route C, proposal / research plan.
- `references/academic/route-literature-review.md`: Route D, literature review.
- `references/academic/citation-style.md`: GB/T 7714 citation footer and mixed-font SVG rules.
- `references/academic/speaker-notes.md`: spoken notes rules.
- `references/academic/layout-library.md`: academic `content_type` layout mapping.
- `references/academic/formula-rendering.md`: mandatory formula extraction, LaTeX rendering, PNG embedding, and formula QA.
- `references/academic/executor-academic.md`: academic executor additions; read in Step 6 with `references/executor-base.md`.

TechnicalRoute references:
- `references/technicalroute/content-schema.md`
- `references/technicalroute/diagram-contract.md`
- `references/technicalroute/archetype-thinking.md`
- `references/technicalroute/archetype-method.md`
- `references/technicalroute/archetype-workflow.md`
- `references/technicalroute/color-typography.md`
- `references/technicalroute/shape-recipes.md`
- `references/technicalroute/seed_sites.json`
- `references/technicalroute/seed_urls.md`
- `references/technicalroute/image-templatedraw.md`
- `references/technicalroute/image-aigenerate.md`
- `references/technicalroute/handling-no-references.md`
- `references/technicalroute/qa-checklist.md`

## Conditional Workflows

Load these only when the trigger matches:

| Workflow | Trigger |
|---|---|
| `conditional-workflows/create-template.md` | User uploads or defines a reusable PPT / SVG / screenshot template for `templates/layouts`. |
| `conditional-workflows/topic-research.md` | User provides only a topic or broad requirement with no citeable source material. |
| `conditional-workflows/resume-execute.md` | User resumes an existing project folder in a fresh session. |
| `conditional-workflows/verify-charts.md` | SVG pages contain calculator-supported data charts before final export. |
| `conditional-workflows/visual-edit.md` | User wants localized visual changes to generated slides. |
| `conditional-workflows/customize-animations.md` | User asks for object-level animation, reveal order, timing, or transition changes. |
| `conditional-workflows/generate-audio.md` | User asks for narration audio, recorded PPTX, or video-ready voice-over export. |
## Workflow

### Step 1 - Parse Source Material

Gate: the user has provided a PDF, DOCX, EPUB, URL, Markdown file, pasted text, or existing notes. If the user only provides a topic and no source material, run `conditional-workflows/topic-research.md` first with citeable academic or authoritative sources, then return here.

Commands:
| Input | Command |
|---|---|
| PDF | `python3 scripts/source_to_md/pdf_to_md.py <file>` |
| DOCX / Word | `python3 scripts/source_to_md/doc_to_md.py <file>` |
| Excel | `python3 scripts/source_to_md/excel_to_md.py <file>` |
| Web page / journal abstract | `python3 scripts/source_to_md/web_to_md.py <URL>` |
| Markdown | Read directly. |

Academic PDF figure extraction defaults to rendered clipping, because embedded-only extraction can lose vector layers, arrows, axes, and captions. Use `--image-extract embed` only when legacy behavior is required, or `--images none` when figures are not needed.

### Step 2 - Initialize Project

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source_files...> --move
```

Checkpoint: `projects/<name>/` exists with `sources/`, `templates/`, `images/`, `svg_output/`, and `notes/`.

### Step 3 - Select Template

Read `templates/layouts/layouts_index.json`. Do not default to free design unless the user explicitly asks for it or every candidate scores below threshold.

Score candidates by scenario match, style / audience match, palette fit, and school / institution identity. Write the Top 3 candidates into `design_spec.md` section I with original `summary`, matched keywords, rationale, and copy command. Ask the user to choose candidate 1 / 2 / 3 or free design at Step 4.2.

After template choice, copy the template SVGs, `design_spec.md`, and images into the project. Read the copied template `design_spec.md` and merge its Color, Typography, and Page Roster into project `design_spec.md` and `spec_lock.md`.

If the selected template came from a user-provided PPTX, its detected aesthetics and parameters have the highest priority: master/layout placeholder geometry, title position, title box size, font family, font size, bold settings, colors, logo position, footer rhythm, page-number position, and page density. Use the template in master-placeholder fill mode: replace placeholder prompt text inside the corresponding master/layout/slide-local slots and inherit that slot's geometry and text style. Add source figures, formula PNGs, charts, and route images into the matching picture/content placeholders. Do not overlay new text on top of template prompt text. Do not create extra free-floating shapes, text boxes, or image frames when a suitable template slot exists. If a slot is unusable, choose another imported layout; only fall back to the built-in template library after recording the fallback in `spec_lock.md`. Treat school name, college name, logos, page numbers, footer marks, and authored master graphics as protected regions. Run overlap/placeholder cleanup before export and block export if any prompt such as `Click to edit...`, `单击此处...`, or `演讲者/课程名称` remains visible.

Before generating pages from a user-provided PPTX template, read `manifest.json` / `templateBinding` and copy the manifest-derived `editableContentRegion` into `design_spec.md` and `spec_lock.md`. Center body content inside `editableContentRegion.primary`, keep titles inside the imported title slot / `titleRegion`, and keep citations, footer marks, and page numbers inside the imported footer slots. If the editable region is missing, zero-sized, or overlaps logo / school-name / footer protected regions, run `scripts/template_import/layout_guard.py` and block SVG generation until the template contract is fixed. A user-template deck is invalid if any slide has more than one visible page number.

Template import or creation uses `conditional-workflows/create-template.md`.

### Step 4 - Strategist Stage

Read:
```text
references/strategist.md
references/academic/executor-academic.md
```

Classify the deck route first and read only the matching route reference:
| Input type | Route | Reference |
|---|---|---|
| Single academic journal / conference paper | Route A | `references/academic/route-academic-paper.md` |
| Course report, policy report, or case analysis | Route B | `references/academic/route-course-report.md` |
| Proposal, research plan, or opening defense | Route C | `references/academic/route-proposal.md` |
| Literature review / review / journal club synthesis | Route D | `references/academic/route-literature-review.md` |

After Route A / B / C / D is selected, read:

```text
references/academic/paper-type-guidance.md
```

Use it to classify the paper type, choose the narrative framework, and then organize modules and slide titles. This reference is the local copy of the Paper-Type Guidance logic; do not read external skill paths during execution. Body slide titles must use:

```text
<module_number> <module_title>: <slide_subtitle_or_evidence_conclusion>
```

Examples: `4 Model Results: Variable Importance Ranking`; `4 Model Results: Network ALE Structure Analysis`. Cover, agenda, section divider, acknowledgements, and reference pages may omit this format.

Blocking confirmation: ask once for canvas, template choice, page count, audience, style goal, palette, icon style, typography, and image policy.

### Step 5 - Image Acquisition

Gate: `design_spec.md` contains any `Acquire Via: ai` or `Acquire Via: web`, or source figures / complex tables are available. Read as needed:
```text
references/image-base.md
references/image-generator.md
references/image-searcher.md
references/image-layout-spec.md
```

Academic image priorities:
- Reuse source figures, experimental results, methodological diagrams, and complex table screenshots when available.
- Run `scripts/analyze_images.py` to create captions and placement recommendations.
- Label embedded source figures with citation markers.
- For self-drawn research route, framework, thinking map, or full-paper workflow diagrams, switch to Step 5.5.

High-priority visual coverage rule: except TechnicalRoute pages, summary pages, and planning / implication pages, every slide must contain at least one meaningful image, source figure, complex table screenshot, chart, or mathematical formula.

Formula rule: when the source contains equations, read `references/academic/formula-rendering.md`. Analyze the user text, extract main academic steps, keep the important formulas under those steps whenever possible, transcribe each formula as LaTeX, write the formula title and variable meanings, render the title + complete formula + interpretation as one PNG with `scripts/latex_formula_to_png.py --block-json`, and insert that PNG via `<image data-formula-png="true" data-formula-block-png="true">`. This is mandatory for both user-provided PPTX templates and built-in template-library decks. Do not render formulas or their interpretation as separate SVG text boxes. Put at most five formula blocks on one slide and separate adjacent formula blocks with gray 1.5pt dashed lines. Use low-resolution formula screenshots only when LaTeX transcription fails and the limitation is recorded.

### Step 5.5 - Internal TechnicalRoute Dual Output

Gate: any resource or page requires `technical_route`, `research_framework`, `thinking_map`, `whole_paper_workflow`, `concept_framework`, or `embed_technicalroute: true`. A page roster item, slide title, notes line, or final QA item named `Technical Route`, `Research Workflow`, `Workflow`, `Pipeline`, `技术路线`, `技术路线页`, `全文方法链条`, or equivalent Chinese wording counts as this gate; a locally hand-drawn workflow page is not a substitute for the required A/B TechnicalRoute output. `svg_quality_checker.py` blocks export when such a route/workflow declaration exists without consecutive Version A/B TechnicalRoute pages.

For every required route diagram, generate two consecutive PPT pages:
| Version | Method | Output field | PPT insertion |
|---|---|---|---|
| A editable template version | Select the best SVG skeleton from `templates/technicalroute/templates/templates_index.json` and inject `content.yaml` via `assemble`. | `route_template_svg_path` | One standalone page titled `<module_number> Research Route: Editable Template Version`. |
| B AI reference version | Generate a high-resolution PNG from article content plus the `prepare-ai-refs` plan: academic-search raster refs first, `Custom_gallery` raster fallback only after the seed-site search completed, produced zero usable academic raster refs, and fallback was explicitly allowed. | `route_ai_image_path` | The next consecutive page is a direct full-slide picture page, with no global layout/title/footer/caption wrapper. |

Execution order:
1. Read `references/technicalroute/diagram-contract.md`, then create `<route_workdir>/contract.md` with `generate_route_image.py contract`. Ask the user only for blocking ambiguity or explicit pre-approval requests; otherwise record conservative assumptions and continue.
2. Classify `archetype` and `sub_variant`, then read exactly one matching archetype file: `archetype-thinking.md`, `archetype-method.md`, or `archetype-workflow.md`.
3. Read `references/technicalroute/content-schema.md` and write `<route_workdir>/content.yaml` from the source and confirmed spec only. No Custom_gallery or literature-reference text may enter `content.yaml`.
4. Read `references/technicalroute/color-typography.md` and `references/technicalroute/shape-recipes.md`; write route `spec_lock.md` with inherited deck colors, user PPTX template palette priority, shape radius, `template_key`, `slot_map`, `color_var_map`, `gallery_refs`, and forbidden additions.
5. Read `references/technicalroute/seed_urls.md` for the branch rules, and treat `references/technicalroute/seed_sites.json` as the only source of online academic-search sites. First run `literature_search.py emit-plan --topic <paper title/keywords> --archetype <thinking|method|workflow> --out <route_workdir>/style_refs`, execute the generated `search_plan.json` with academic search over `seed_sites.json`, inspect similar papers for mechanism diagrams / model-principle diagrams / technical-route or workflow figures, download accepted raster figures, and record them with `literature_search.py record`. Then run `literature_search.py prepare-ai-refs --topic <paper title/keywords> --discipline <discipline> --archetype <thinking|method|workflow> --out <route_workdir>/style_refs`. If usable literature refs exist, `refs` must contain only those manifest-listed raster figures. Only after the seed-site search completed and produced zero usable raster refs may `prepare-ai-refs --allow-gallery-fallback-after-search --search-completed` select discipline-matched raster anchors from `templates/technicalroute/Custom_gallery/gallery_index.json`; alternatively write `style_refs/search_completed.json` with `{"completed": true}` before running fallback. The refs list must never mix literature and gallery sources. Do not hard-code sites or use SVG/PPTX/editable route pages as AI references.
6. Inspect `templates/technicalroute/Custom_gallery/` and record 0-3 suitable `gallery_refs`; do not invent files and do not copy reference text.
7. Read `references/technicalroute/image-templatedraw.md`; select a template from `templates/technicalroute/templates/templates_index.json`, complete the slot map, and generate Version A with `generate_route_image.py assemble`.
8. Read `references/technicalroute/image-aigenerate.md`; build `prompt_ai.md` from the article outline / `content.yaml`, then generate Version B with `generate_route_image.py run-ai-variant --refs-plan <route_workdir>/style_refs/route_ai_refs.json`. Let `run-ai-variant` write `<project_path>/svg_output/_direct_image_slides.json` automatically, or pass `--direct-slide-manifest <project_path>/svg_output/_direct_image_slides.json --after-svg-stem <NN>_route_template`, so the generated PNG is inserted by the PPTX exporter as a direct picture slide without any SVG wrapper. `--refs-plan` is the single allowed reference bridge: it must be either `literature_only` with seed-site manifest raster refs, or `gallery_only_fallback` with Custom_gallery raster anchors only when the seed-site search completed, produced no usable refs, and both `gallery_fallback_after_search` and `seed_search_completed` are true. Mixing the two classes, manual `--refs`, SVG, PPTX, and screenshots of Version A are forbidden. Version B is prompt/reference independent from Version A; never feed `route_template_svg_path`, `pipeline_with_stages.svg`, assembled SVGs, PPT exports, or screenshots into the AI image call.
   Backend/model selection follows `.env.example`: set `IMAGE_BACKEND` plus provider-specific keys/model variables in the process environment or `.env`; do not pass `--backend` / `--model` unless the user explicitly needs a temporary override. Keep `--aspect_ratio 16:9 --image_size 4K`; the script then normalizes the PNG to at least 330ppi full-slide target pixels before PPT insertion.
9. Verify `route_ai_image_path` exists and `<project_path>/svg_output/_direct_image_slides.json` contains a `technicalroute_ai` entry whose `image_path` points to that PNG and whose `after_svg_stem` points to the Version A route template slide. `create-ai-slide --out-svg` remains only a legacy manual recovery path. Normal execution must not wrap Version B in SVG; `scripts/svg_to_pptx.py` reads `_direct_image_slides.json` and inserts the PNG as the next PPTX picture slide directly. Run `references/technicalroute/qa-checklist.md` before export.

TechnicalRoute output record:
```yaml
contract_path: <route_workdir>/contract.md
content_yaml_path: <route_workdir>/content.yaml
route_spec_lock_path: <route_workdir>/spec_lock.md
route_template_svg_path: <route_workdir>/output/route_template_<id>.svg
route_ai_image_path: <route_workdir>/output/route_ai_<id>.png
audit_report_path: <route_workdir>/audit_report.md
route_template_slide_svg_path: <project_path>/svg_output/<NN>_route_template.svg
route_ai_direct_slide_manifest: <project_path>/svg_output/_direct_image_slides.json
reference_mode: literature | offline_user_uploads | atlas_only
gallery_refs: []
style_refs_manifest: <route_workdir>/style_refs/manifest.json
```

Academic integrity lock: Custom_gallery, literature references, and offline user reference images are only style / structure anchors. All visible labels, formulas, data names, method names, place names, author names, citations, and numeric values must come from the uploaded paper, user material, or confirmed `design_spec.md`.

### Step 6 - Generate SVG Pages And Notes

Read:
```text
references/executor-base.md
references/academic/executor-academic.md
references/academic/formula-rendering.md
references/shared-standards.md
```

Use `executor-general.md` only for general non-academic mechanics not covered by academic references. Do not use consultant-specific executor flows.

For each page, re-read `spec_lock.md`, use the selected template, fill the selected layout slots, include `bottom_banner_text` and `citation_footer` when required, place generated page numbers according to `spec_lock.md` page-number source, apply the visual coverage rule, remove unused placeholder prompts, check forbidden overlaps, and write spoken notes to `notes/total.md` following `references/academic/speaker-notes.md`.

User PPTX template execution is slot replacement, not overlay drawing. For every title, subtitle, body, picture, formula, route image, and page number, use the imported slot box, inherited font size/color/bold setting, and protected-region map whenever available. Delete or replace unused prompt text and unused picture/body placeholders before finalization. A generated page is invalid if title text overlaps school identity, if one semantic phrase is split into stacked text boxes, or if unused template prompts remain visible.

Formula execution is blocking here: before writing any page that explains a displayed formula, create the formula block JSON under `notes/`, run `scripts/latex_formula_to_png.py --block-json`, verify the PNG exists under `images/formulas/`, and insert the formula template shell with `<image data-formula-png="true" data-formula-block-png="true">`. Do not write the formula role, equation, `式中`, or variable explanations as separate final SVG text boxes.

Keep summary and closing separate: create one standalone summary/conclusion page, and create a separate final thank-you / Q&A page. Never combine `总结` / `Summary` with `谢谢大家` / `Thank you` on one slide.

For every template source, formula execution must insert the rendered PNG into the user-template picture/content slot or built-in content region as `<image data-formula-png="true" data-formula-block-png="true" href="images/formulas/formula_block_*.png">` or an embedded PNG data URI. Formula PNG boxes, text boxes, and separator lines must not overlap or stack.

Formula block rendering rule: the formula title, `definition_label`, and variable explanation text use the same font size and are not bold unless a selected template explicitly defines a different non-bold size. Do not make formula titles larger or heavier than the explanation text.

Template-first style rule: citation arrows, numbered markers, callouts, connector strokes, dashes, shadows, and badge styles must inherit from the selected user PPTX template or built-in template library first. Copy the template marker shape, stroke width, color, dash pattern, number-badge fill, and label typography instead of inventing generic arrows or numeric circles.

### Step 7 - Validate, Finalize, Export

```bash
python3 scripts/svg_quality_checker.py <project_path>/svg_output
python3 scripts/total_md_split.py <project_path>
python3 scripts/notes_to_docx.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_quality_checker.py <project_path>/svg_final
python3 scripts/svg_to_pptx.py <project_path> --only native -s output -t none
python3 scripts/pptx_openability_check.py <exported_pptx> --fix-permissions
```

Keep the default `finalize_svg.py` steps enabled for user PPTX template decks; `cleanup-placeholders` is the export-time fallback that removes unused PowerPoint prompt text and untouched placeholder guide boxes. The second `svg_quality_checker.py` pass on `svg_final/` is mandatory because it catches template prompt residue after cleanup, missing TechnicalRoute Version B pages, non-embedded AI route images, formula text-box fallbacks, and combined summary/thank-you slides.

Native DrawingML export must read `svg_output/`, not `svg_final/`. `svg_final/` is only for the explicit diagnostic SVG-reference fallback because post-processing may convert rounded rectangles and simple lines into SVG paths, which become many `<a:custGeom>` objects and can cause PowerPoint repair / missing-content failures. `svg_output` pages must not be authored as full-slide `<image id="slide-raster-image">` bitmaps; that produces non-editable PPT slides and is a hard quality failure. TechnicalRoute Version B is the only full-slide bitmap exception, but it must be inserted through `_direct_image_slides.json` as a direct PPTX picture slide, not authored as a normal SVG page. The PNG must be image-only, full-canvas, and >=330ppi target resolution. Keep slide transitions disabled by default with `-t none`; add transitions only when the user explicitly asks for them.

Speaker notes are exported as a standalone DOCX. Do not embed notes into the PPTX because notes-heavy packages can trigger PowerPoint repair prompts and COM/RPC open failures. The PPTX exporter strips notesSlide / notesMaster package parts even if a legacy flag is passed.

The PPTX openability check is mandatory before handing the file to the user. It must pass zip readability, internal relationship targets, notes slide -> notes master packaging, `[Content_Types].xml` notes overrides, `presentation.xml` notes master linkage, current-user file read/open permission, custom-geometry budget, and slide-transition budget. If it reports a broken package, excess `<a:custGeom>`, transition risk, or access-denied risk, fix the SVG-to-DrawingML export path and rerun export; do not bypass the converter by generating a different standard PowerPoint package.

If a user says the generated PPTX cannot open, asks to repair a PPTX, or reports content missing after opening, stop normal generation and run a recovery cycle:
1. Inspect the failed PPTX with `scripts/pptx_openability_check.py <failed.pptx> --fix-permissions`.
2. Record the likely cause: missing rel target / notes master, ACL/read permission, native export from `svg_final`, excessive `<a:custGeom>`, slide transitions, bad media relationship, or invalid content type.
3. Regenerate a new timestamped copy from the same project using `scripts/svg_to_pptx.py <project_path> --only native -s output -t none`.
4. Re-run `pptx_openability_check.py` and only return the regenerated copy if the check passes.
5. Never solve this by switching to python-pptx or another direct PPT generator that bypasses the SVG -> DrawingML converter.

If charts are used, run `conditional-workflows/verify-charts.md` before final export.

Final checklist: numbered module titles, semantically coherent cover title grouping, visual coverage on non-exempt slides, proportional/equal-frame paper figures, consistent citations, consecutive TechnicalRoute A/B pages with Version B inserted through `_direct_image_slides.json`, formula blocks rendered as PNG, no unused user-template placeholders, separate summary and thank-you pages, spoken notes, and editable PPTX output.

Write `<project_path>/ppt_outline_cn.md` as the only final QA summary after export. It must report page count, notes coverage, image / formula object count, TechnicalRoute page locations and editability, citation handling, known limitations, and a per-page checklist. Do not create a second outline or duplicate QA report under another filename.

Maintenance audit: after changing skill code, workflows, template indexes, or export logic, run `python3 scripts/skill_integrity_check.py`. This is a developer check, not a mandatory per-user generation step.

Readable body font rule: except citation/reference footers and page numbers, final PPT text must be at least 12px. Export must be blocked when `svg_quality_checker.py` reports any error; do not bypass the gate with a custom PPTX writer. Body slides (not cover, divider, ending, or reference pages) should be dense by default and fill the selected editable content region with source-grounded text, charts, formulas, tables, or route content.

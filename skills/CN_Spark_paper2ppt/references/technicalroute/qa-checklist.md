# TechnicalRoute QA Checklist
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 生成两种研究路线图后读取；它检查内容真实性、可读性、双页插入和 PPT 转换兼容性。

Run this checklist for both Version A editable template SVG and Version B AI reference PNG before inserting the pages into the final deck.

## Machine Checks

Run audit for the AI PNG:

```bash
python3 scripts/technicalroute/generate_route_image.py audit --image <route_workdir>/output/route_ai_<id>.png --content <route_workdir>/content.yaml --contract <route_workdir>/contract.md --out <route_workdir>/audit_report.md
```

For Version A, also run the normal SVG quality checker after insertion:

```bash
python3 scripts/svg_quality_checker.py <project_path>/svg_output
```

Machine or semi-machine checks:
- Canvas ratio matches the target slide or declared route bbox.
- PNG width is sufficient for PPT insertion, preferably at least 1600 px.
- Output file is not suspiciously tiny or blank.
- OCR or visual inspection finds no watermark, URL, stock-service logo, or social handle.
- No emoji or decorative stock-photo elements appear.
- Version A SVG contains editable text, not a full-slide raster image.
- Version A SVG does not use `<foreignObject>` for critical text.

## Content QA

- Title matches the route scope and the parent slide module.
- Every visible node, panel, formula, stage, and edge appears in `content.yaml`.
- Every `content.yaml` item traces to source material, user confirmation, or `design_spec.md`.
- No invented dataset, method, variable, metric, causal claim, citation, author name, or place name appears.
- Source uncertainty remains visible when the route describes planned or inferred work.
- Review diagrams synthesize literature structure rather than pretending a single paper proves all claims.
- Proposal diagrams distinguish planned work from completed work.
- Any third-party method, dataset, or concept that is semantically used by the slide has a GB/T 7714 citation footer or reference entry.

## Visual QA

- Labels are legible at PPT size.
- Node count is normally 5-12 unless the source requires another range.
- A node label does not exceed three wrapped lines unless the template explicitly supports it.
- One semantic phrase is not split into multiple stacked text boxes.
- Text boxes do not overlap each other, connectors, badges, or icons.
- Connectors are readable and do not cross labels unnecessarily.
- The diagram is not overcrowded.
- Color follows the parent deck strategy and user PPTX template palette priority.
- Accent and brick red are used sparingly and semantically.
- Shape radius follows route `spec_lock.md`, normally `rx=6` or smaller for dense labels.
- Chinese / Latin / numeric mixed text follows the deck mixed-font rule in Version A.

## Version A Editable Template QA

- `route_template_svg_path` exists.
- `template_key` exists in `templates/technicalroute/templates/templates_index.json`.
- `slot_map` covers every required placeholder in the template.
- `color_var_map` resolves template variables to real HEX colors.
- All text remains editable SVG text with `<text>` and `<tspan>`.
- No whole-diagram rasterization.
- No phrase is broken into unnatural separate text objects.
- The page can be converted to DrawingML without losing the route structure.

## Version B AI Reference QA

- `route_ai_image_path` exists.
- The generation command normally omits `--backend` and `--model` so `scripts/image_gen.py` selects the agent/model from the process environment or `.env.example` provider variables. Only pass `--backend` / `--model` for an explicit temporary override documented in the route workdir.
- The generation command uses `--refs-plan <route_workdir>/style_refs/route_ai_refs.json`.
- `route_ai_refs.json` is either `literature_only` with only manifest-listed raster files from `style_refs/manifest.json`, or `gallery_only_fallback` with only discipline `Custom_gallery` raster anchors after the seed-site search was executed and found zero usable literature refs. It must not mix the two.
- Academic-search references in `style_refs/manifest.json` were collected from a search plan generated from `references/technicalroute/seed_sites.json`; the search targeted similar-paper mechanism diagrams, model-principle diagrams, technical-route figures, and workflow figures. No separate hard-coded research website list appears in `prompt_ai.md`, route `spec_lock.md`, or project QA notes.
- `prompt_ai.md` uses article content plus exactly one visual reference class: seed-sites research-search manifest refs, or Custom_gallery fallback refs after a completed zero-result search. It does not use Version A SVG, assembled SVG, chart SVG, template SVG, exported slide images, PPT/PPTX pages, or user-uploaded references as an AI image reference.
- The image differs meaningfully from Version A in style or composition while preserving the same logic.
- No reference-image text, number, caption, author, citation, institution, or place name leaks into the output.
- If AI labels are unreliable, add editable SVG labels, callouts, or captions on top of the PPT page.
- If the AI output cannot be made reliable after retry policy, keep Version A and report the limitation.

## Reference Integrity QA

Compare Version B with selected `gallery_refs` and `style_refs`:
- Similar layout rhythm is acceptable.
- Similar exact text is not acceptable.
- Similar numbers, paper titles, author names, or dataset names are not acceptable.
- A copied visual structure is acceptable only when it has been abstracted into the selected template or recipe and the content is fully replaced.

## Embedding QA

- Version A and Version B are inserted into consecutive PPT pages.
- Page titles are different and include the version meaning.
- Both pages inherit parent footer, page number, bottom banner rules, and citation policy.
- Both output paths are recorded in project assets or route `spec_lock.md`.
- `_direct_image_slides.json` contains a `technicalroute_ai` entry whose `image_path` points to the Version B PNG; SVG wrappers for Version B are blocked by default and must not be used in production execution.
- `svg_to_pptx.py` reads `_direct_image_slides.json` and inserts the Version B PNG directly into the PPTX as a picture slide.
- Final deck checklist marks both pages as TechnicalRoute pages.
- Non-TechnicalRoute visual coverage rules do not mistakenly require extra images on these route pages.

## Retry Policy For Version B

Retry at most three times:
1. Add a targeted refine instruction and stronger negative constraints.
2. Change backend if available while keeping the same content.
3. Stop, keep Version A, and record the limitation in `ppt_outline_cn.md`.

Do not continue regenerating indefinitely. The editable template version is the reliable baseline.

## Blocking Export Gate

Run the deck-level quality gate after Version A/B insertion:

```bash
python3 scripts/svg_quality_checker.py <project_path>/svg_output
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_quality_checker.py <project_path>/svg_final
```

The gate must fail if any of the following is true:
- a Version A editable TechnicalRoute page exists without a consecutive Version B AI reference page;
- `_direct_image_slides.json` is missing, lacks a `technicalroute_ai` entry, or points to a missing/low-resolution PNG;
- the AI image href is not `data:image/png;base64,...`, has invalid base64, or does not decode to PNG bytes;
- `run-ai-variant` failed, was skipped, silently dropped usable `style_refs`, or used `Custom_gallery` before the seed-site literature search was completed.

Do not export PPTX until the AI reference image is generated, inserted, finalized, and verified.

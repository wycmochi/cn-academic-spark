# TechnicalRoute Seed URLs And Reference Priority
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 选择参考图路径时读取；它把 seed-sites 在线学术检索和 Custom_gallery 最近意图降级路径接入主流程。

Use this file before building `style_refs` for Version B AI reference generation. The goal is to collect or assess visual style anchors, not to collect semantic content. The paper, user material, and `content.yaml` remain the only content sources.

`scripts/technicalroute/literature_search.py` reads `references/technicalroute/seed_sites.json` for the concrete academic-search site configuration. This Markdown file explains how the agent should choose the branch and prioritize reference classes; it must not become a second hard-coded site list.

## Reference Priority

Use this order:
1. Academic-website and relevant-literature raster references from the `seed_sites.json` search plan: DOI-linked journal or publisher pages, official lab / university / project pages, paper supplementary material, reputable academic sources, open course materials, documentation pages, and institutional repositories, only when they provide flowchart / framework / workflow / route-diagram / explanatory-legend style references.
2. Custom_gallery nearest-intent raster anchors selected through `templates/technicalroute/Custom_gallery/gallery_index.json`, only after the seed-sites search has completed and produced zero usable academic raster references.

Do not invent URLs. Do not claim that search succeeded when it did not. Do not treat Version A SVGs, assembled SVG templates, result charts, histograms, ROC curves, maps, heatmaps, or raw tables as AI image references. Uploaded paper content and outline are semantic sources through `content.yaml`, not image-reference sources for Version B.

## Site Configuration Source

The concrete search URLs, priorities, login flags, minimum reference count, and image-filter hints live only in `references/technicalroute/seed_sites.json`. When the user or maintainer changes that JSON, the search behavior follows the JSON without editing this Markdown file. Agents must not paste a separate website list into `prompt_ai.md`, `spec_lock.md`, `ppt_outline_cn.md`, or any generated project notes.

Valid Version B style references are local raster files downloaded from the search plan emitted by `literature_search.py emit-plan`, then recorded with `literature_search.py record` into `<route_workdir>/style_refs/manifest.json`. Custom_gallery is a fallback only when this manifest has zero usable raster references and the completed seed-site search is explicitly proven with `--search-completed` or `style_refs/search_completed.json`.

## Branch Selection

### Online Branch

Use when search or browser tools are available and the topic benefits from discipline-specific visual conventions.

```bash
python3 scripts/technicalroute/literature_search.py emit-plan --topic "<topic>" --archetype <thinking|method|workflow> --max 8 --out <route_workdir>/style_refs/
```

Then use available search tools to inspect the generated search plan. Record useful references:

```bash
python3 scripts/technicalroute/literature_search.py record --out <route_workdir>/style_refs/ --doi "<doi>" --title "<title>" --journal "<journal>" --year "<year>" --authors "<authors>" --source-url "<url>" --image-url "<figure_url>" --downloaded "<local_file>" --caption-hint "<why it fits>" --score <score>
```

Assess the collected references:

```bash
python3 scripts/technicalroute/literature_search.py assess --out <route_workdir>/style_refs/
```

If accepted raster references exist, continue to `generate_route_image.py prompt --reference-mode literature_only` and then `prepare-ai-refs` normally. If the completed search produced zero usable figures, run `prepare-ai-refs --allow-gallery-fallback-after-search --search-completed` so `route_ai_refs.json` records `gallery_only_fallback`, `gallery_fallback_after_search: true`, and `seed_search_completed: true`. If no exact Custom_gallery entry matches the paper's discipline/archetype/sub-variant, the fallback still must stay inside Custom_gallery and use the highest-scoring nearest-intent raster recorded with `selection_policy: nearest_intent_within_custom_gallery_only`.

### Offline / User-Reference Branch Is Forbidden For Version B

Do not use user-uploaded reference images, exported PPT screenshots, previous demo images, or local SVG/PPT-derived rasters as Version B AI references. The Version B reference bridge has exactly two allowed source classes: seed-site academic-search raster figures first, and Custom_gallery raster fallback after a completed zero-result search. User-provided images may inform the editable deck style elsewhere, but they must not enter `route_ai_refs.json` and must not be passed to `run-ai-variant`.

### Gallery-Only Fallback Branch

Use when the seed-sites search has completed and no usable academic raster references are available.

```bash
python3 scripts/technicalroute/literature_search.py assess --out <route_workdir>/style_refs/
python3 scripts/technicalroute/literature_search.py prepare-ai-refs --topic "<paper title / keywords>" --discipline <discipline> --archetype <thinking|method|workflow> --out <route_workdir>/style_refs --allow-gallery-fallback-after-search --search-completed
python3 scripts/technicalroute/generate_route_image.py prompt --archetype <thinking|method|workflow> --content <route_workdir>/content.yaml --style <route_workdir>/style_refs/style_profile.md --reference-mode gallery_only_fallback --out <route_workdir>/prompt_ai.md
```

Gallery-only fallback means:
- use only raster anchors selected from `templates/technicalroute/Custom_gallery/gallery_index.json` as fallback style guidance after a completed zero-result seed-site search; when there is no exact match, choose the nearest-intent gallery raster by score; do not use template SVGs, PPTX editable pages, PPT exports, user images, or Version A screenshots as AI references;
- do not claim external literature reference support;
- keep article-derived `content.yaml` as the only semantic source.

## Image Filtering Heuristics

Keep references that match these signals:
- title, caption, or surrounding text includes route, framework, pipeline, workflow, research design, method framework, or similar terms;
- aspect ratio is suitable for slide composition, normally 1.2 to 3.0;
- image width is at least 800 px when possible;
- the figure shows nodes, stages, panels, arrows, lanes, or conceptual grouping;
- it matches the selected archetype and sub-variant.

Reject or down-rank:
- result charts that do not show process or framework structure;
- heatmaps, boxplots, ROC curves, loss curves, regression plots, or scatter plots when they are only empirical results;
- screenshots with dense unreadable text;
- watermarked, promotional, or non-academic graphics;
- images whose visual grammar conflicts with the deck style.

## Style Profile Requirements

`style_profile.md` or the assessed reference summary should capture:
- discipline or domain;
- selected archetype and likely sub-variant;
- node shape style;
- connector style;
- density level;
- color saturation level and accent placement;
- typography hints;
- features to avoid.

## Academic Integrity Rules

- References are style and structure anchors only.
- SVG files are never passed as Version B AI image references.
- Do not copy text, numbers, formulas, dataset names, model names, author names, captions, citations, or place names from references.
- Keep DOI, title, author, and source metadata in `style_refs/manifest.json` for traceability.
- The final route diagram normally does not cite style references, because it does not use their content. If the user requests an acknowledgement, list them in the deck's source-note or reference appendix.

## Workflow Placement

This file is Step 5.5 item 3 in the main workflow:
1. Write `contract.md`.
2. Write `content.yaml`.
3. Choose reference mode using this file.
4. Inspect `Custom_gallery/gallery_index.json` only if `prepare-ai-refs` enters `gallery_only_fallback`; Version B must never inspect the editable Version A template or PPT output as a reference source.
5. Generate Version A using `image-templatedraw.md`.
6. Generate Version B using `image-aigenerate.md`.
7. Audit and insert both pages.

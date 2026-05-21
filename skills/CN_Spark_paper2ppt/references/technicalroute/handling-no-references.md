# Handling No References
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 找不到足够外部参考图时读取；它规定如何从 seed-sites 文献检索降级到 Custom_gallery 最近意图参考图，并保证仍能生成双产物。

If the seed-sites literature search does not provide usable raster anchors, continue the pipeline by using only the nearest-intent raster anchors from `templates/technicalroute/Custom_gallery/gallery_index.json`. The absence of literature references affects Version B style confidence; it does not remove the requirement to create both Version A and Version B unless the user explicitly cancels one output.

## Trigger Conditions

Use this file when any condition is true:
- `literature_search.py assess --out <style_refs>` recommends gallery fallback after a completed seed-sites search.
- `style_refs/manifest.json` is missing or has too few usable references.
- Search tools are unavailable or return no usable raster mechanism/model/technical-route/workflow figures.
- The available references are result charts rather than route or framework diagrams.
- The exact Custom_gallery discipline / archetype / sub-variant is missing and the nearest-intent gallery raster must be selected.
- The user requests no external reference use for copyright, privacy, or style reasons; in that case Version B may use only Custom_gallery, never user-uploaded or PPT-derived references.

## Fallback Order

1. Seed-site literature raster figures recorded in `style_refs/manifest.json` when they are route, framework, method, or workflow diagrams.
2. Closest Custom_gallery raster anchors selected through `templates/technicalroute/Custom_gallery/gallery_index.json` only after the seed-site literature search has been executed and no usable mechanism/model/technical-route raster refs exist.
3. Hard failure if neither source class has a usable raster reference; do not invent neutral styles or use user-uploaded/editor screenshots as AI references.

At every level, semantic content still comes only from `content.yaml`.

## Fallback A - User References Are Not Allowed For Version B

Do not run `literature_search.py offline` for TechnicalRoute Version B. User-uploaded images, exported slides, screenshots, SVG/PPT/PPTX template pages, and editable route pages are not valid AI references for Version B, even when they look relevant.

Then continue:
- Version A: choose and assemble the editable template using `image-templatedraw.md`.
- Version B: use only `literature_only` refs from seed-sites search, or `gallery_only_fallback` refs from Custom_gallery after the completed zero-result search is recorded.
- Version B still adds one extra direct PPT picture page outside the user's requested page count; do not delete or merge a regular editable slide to make room for it.

## Fallback B - Atlas-Only From Internal Assets

Use only after the seed-sites academic search has completed and produced zero usable raster references.

Actions:
- Inspect `templates/technicalroute/Custom_gallery/gallery_index.json` and select discipline-matched raster files; if no exact match exists, select the highest-scoring nearest-intent raster recorded by `prepare-ai-refs`; do not invent file paths.
- Do not use `templates/technicalroute/templates/*.svg`, a PPTX editable route page, or a screenshot of Version A as an AI reference.
- Record `reference_mode: gallery_only_fallback` and `fallback_note` in route `spec_lock.md`.
- Generate Version A normally through `assemble`.
- Generate Version B with the refs-plan bridge:

```bash
python3 scripts/technicalroute/literature_search.py prepare-ai-refs --topic "<paper title / keywords>" --discipline <discipline> --archetype <thinking|method|workflow> --out <route_workdir>/style_refs --allow-gallery-fallback-after-search --search-completed
python3 scripts/technicalroute/generate_route_image.py prompt --archetype <thinking|method|workflow> --content <route_workdir>/content.yaml --style <route_workdir>/style_refs/style_profile.md --reference-mode gallery_only_fallback --out <route_workdir>/prompt_ai.md
python3 scripts/technicalroute/generate_route_image.py run-ai-variant --prompt <route_workdir>/prompt_ai.md --aspect_ratio 16:9 --filename route_ai_<id> --out <route_workdir>/output --refs-plan <route_workdir>/style_refs/route_ai_refs.json --direct-slide-manifest <project_path>/svg_output/_direct_image_slides.json --after-svg-stem <NN>_route_template
```

The prompt must include a gallery-only fallback clause: no usable literature raster references are available after the completed seed-sites search, so the model must use only the declared structure, the selected Custom_gallery raster anchors, deck color roles, and article-derived content.

The fallback does not change the page-count contract: `_direct_image_slides.json` must still mark the Version B page with `page_count_policy: extra_reference_page_not_counted`, `counts_against_user_page_count: false`, and `page_count_delta: 1`.

## Fallback C - AI Output Remains Unusable

If Version B fails after reasonable retries:
- Keep Version A as the reliable editable deliverable.
- Package `prompt_ai.md`, `content.yaml`, `contract.md`, selected template key, and any reference manifest in the route workdir.
- Insert a clearly labeled placeholder or a low-label AI draft only if the user accepts it.
- Record the limitation in the final `ppt_outline_cn.md` QA report.

Retry policy:
- First failure: refine the prompt with the failed checklist item and stronger negative constraints.
- Second failure: change image backend if available.
- Third failure: stop regenerating and report the limitation.

## Contract Update

When falling back, update `contract.md` Section 9:

```yaml
mode: gallery_only_fallback
expected_refs_count: "<number of selected Custom_gallery raster anchors>"
fallback_note: "<reason the completed seed-sites search produced no usable literature raster refs; include nearest-intent gallery selection reason>"
```

Ask for user confirmation only if the user expected literature-based visual references or the fallback changes the intended meaning. Otherwise continue with the recorded fallback.

## Relationship To Version A

Reference scarcity does not block Version A. Template assembly depends on:
- a valid `content.yaml`;
- a selected `template_key`;
- a complete `slot_map`;
- resolved project colors.

If no template fits, do not silently replace Version A with Version B. Instead choose the closest editable template, simplify content, or report the missing template fit.

## Do Not

- Do not fabricate a search result, DOI, style reference, or downloaded file.
- Do not copy text from Custom_gallery to compensate for missing source content.
- Do not stop the whole PPT generation only because online references failed.
- Do not present gallery-only fallback output as literature-guided output.

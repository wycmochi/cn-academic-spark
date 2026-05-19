# Handling No References
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 找不到足够外部参考图时读取；它规定如何降级到用户图、论文图或 Custom_gallery atlas-only，保证仍能生成双产物。

If literature search, user references, or Custom_gallery do not provide enough anchors, continue the pipeline instead of stopping. The absence of references affects Version B style confidence; it does not remove the requirement to create both Version A and Version B unless the user explicitly cancels one output.

## Trigger Conditions

Use this file when any condition is true:
- `literature_search.py assess --out <style_refs>` recommends `atlas_only`.
- `style_refs/manifest.json` is missing or has too few usable references.
- Search tools are unavailable and the user did not upload enough reference images.
- The available references are result charts rather than route or framework diagrams.
- The selected Custom_gallery discipline folder is empty or lacks a useful manifest.
- The user requests no external reference use for copyright, privacy, or style reasons.

## Fallback Order

1. Seed-site literature raster figures recorded in `style_refs/manifest.json` when they are route, framework, method, or workflow diagrams.
2. Closest Custom_gallery raster anchors selected through `templates/technicalroute/Custom_gallery/gallery_index.json` only after the seed-site literature search has been executed and no usable mechanism/model/technical-route raster refs exist.
3. Hard failure if neither source class has a usable raster reference; do not invent neutral styles or use user-uploaded/editor screenshots as AI references.

At every level, semantic content still comes only from `content.yaml`.

## Fallback A - User Provides At Least Three Images

Run:

```bash
python3 scripts/technicalroute/literature_search.py offline --hints <user_uploaded_dir> --out <route_workdir>/style_refs/ --topic "<topic>" --archetype <thinking|method|workflow>
python3 scripts/technicalroute/literature_search.py assess --out <route_workdir>/style_refs/
```

Then continue:
- Version A: choose and assemble the editable template using `image-templatedraw.md`.
- Version B: use the offline `style_refs` as references. Call `generate_route_image.py prompt` with `--reference-mode literature` because the prompt command currently supports only `literature` and `atlas_only`.

## Fallback B - Atlas-Only From Internal Assets

Use when online and user references are unavailable or weak.

Actions:
- Inspect `templates/technicalroute/Custom_gallery/gallery_index.json` and select discipline-matched raster files; do not invent file paths.
- Do not use `templates/technicalroute/templates/*.svg`, a PPTX editable route page, or a screenshot of Version A as an AI reference.
- Record `reference_mode: gallery_only_fallback` and `fallback_note` in route `spec_lock.md`.
- Generate Version A normally through `assemble`.
- Generate Version B with the refs-plan bridge:

```bash
python3 scripts/technicalroute/literature_search.py prepare-ai-refs --topic "<paper title / keywords>" --discipline <discipline> --archetype <thinking|method|workflow> --out <route_workdir>/style_refs --allow-gallery-fallback-after-search
python3 scripts/technicalroute/generate_route_image.py prompt --archetype <thinking|method|workflow> --content <route_workdir>/content.yaml --style <route_workdir>/style_refs/style_profile.md --reference-mode atlas_only --out <route_workdir>/prompt_ai.md
python3 scripts/technicalroute/generate_route_image.py run-ai-variant --prompt <route_workdir>/prompt_ai.md --aspect_ratio 16:9 --filename route_ai_<id> --out <route_workdir>/output --refs-plan <route_workdir>/style_refs/route_ai_refs.json --direct-slide-manifest <project_path>/svg_output/_direct_image_slides.json --after-svg-stem <NN>_route_template
```

The prompt must include an atlas-only clause: no literature references are available, so the model must use only the declared structure, shape recipes, deck color roles, and article-derived content.

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
mode: atlas_only
expected_refs_count: 0
fallback_note: "<reason search or references were unavailable>"
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
- Do not present atlas-only output as literature-guided output.

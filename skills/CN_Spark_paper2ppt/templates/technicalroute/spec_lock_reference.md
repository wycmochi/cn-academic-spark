# `{project_name}` · Execution Lock (single-figure)

> **⚠️ Skeleton for the main agent — do NOT copy this file verbatim into a project.** When producing `<project_path>/spec_lock.md`, emit ONLY `##` sections with filled-in `-` data lines. Strip all `>` blockquotes (those are author-time guidance, not runtime data). Every output line must be parseable data.
>
> **Position in the pipeline (TR engine):** This is the **machine-readable** counterpart of `design_spec.md`. The renderer (`generate_route_image.py prompt|run`) and the template-assembler MUST `read_file` this before producing the SVG / PNG. Values not listed here MUST NOT appear in the output. For the human-readable rationale (why we chose this template / palette / panel plan), read `design_spec.md`.
>
> **Conflict rule**: on divergence with `design_spec.md`, **`spec_lock.md` wins** (it is what the renderer actually consumes).

---

## canvas
- viewBox: 0 0 1280 720
- format: ppt169
- aspect_ratio: 16:9
- margin_top: 60
- margin_bottom: 80
- margin_left: 60
- margin_right: 60

> Mirror `design_spec.md §II`. Common alternatives: `0 0 1024 768` (PPT 4:3), `0 0 1242 1660` (Xiaohongshu), `0 0 1080 1920` (Story). Mismatching this with `design_spec.md` triggers the conflict rule (this file wins, but emit a warning).

---

## archetype
- archetype: thinking
- sub_variant: quad
- argument_flow: left_to_right
- panel_count: 4

> Copied verbatim from `contract.md §2` via `design_spec.md §III`. Renderer uses `archetype` to pick the right prompt skeleton from `references/image-prompt-templates.md`.

---

## colors
- bg: #FFFFFF
- primary: #1F3864
- accent: #C00000
- muted: #B0B0B0
- border: #DDDDDD
- text_body: #222222
- text_caption: #666666

> Fill only the colors actually used. Delete unused rows rather than leave as `#......`. Accent area must stay ≤ 5% of the canvas — enforced in `qa-checklist.md`.

---

## typography
- title_family: "Microsoft YaHei", "Source Han Sans SC", sans-serif
- title_latin_family: "Times New Roman", serif
- body_family: "Microsoft YaHei", "Source Han Sans SC", sans-serif
- body_latin_family: "Inter", "Arial", sans-serif
- formula_family: "STIX Two Math", "Cambria Math", "Times New Roman", serif
- title_size: 28
- panel_label_size: 20
- body_size: 14
- formula_size: 18
- caption_size: 12

> Mixed-script discipline (hard rule): CJK and Latin runs MUST use separate `<tspan font-family>` segments. Renderer never mixes Microsoft YaHei into Latin runs or Times New Roman into CJK runs.

---

## source_choice
- template_key: pipeline_with_stages
- template_path: assets/templates/pipeline_with_stages.svg
- gallery_refs:
  - assets/Custom_gallery/transportation/全文思路.png
  - assets/Custom_gallery/transportation/技术路线-模型数据.png
- fallback_backend: gemini
- fallback_atlas_only: false

> One of `template_key` / `gallery_refs` / `fallback_backend` must be set for the renderer to know how to produce the figure.
>
> - `template_key` set → editable-SVG assembly path. Renderer reads the SVG, performs slot substitution per `slot_map` below, writes both `.svg` and a rasterised `.png`.
> - `template_key: none` → AI generation path. Renderer uses `fallback_backend` + the prompt synthesized from `prompt.md`. `gallery_refs` (if any) are passed as `--reference` images.
> - `fallback_atlas_only: true` → renderer adds the `[ATLAS-ONLY MODE]` clause to the prompt and skips the literature `style_refs/*.png` (only the abstract atlas SVGs feed in).

---

## slot_map
- P0.title: content.yaml.title
- P1.label: content.yaml.panels[0].label
- P1.points[0]: content.yaml.panels[0].points[0]
- P1.points[1]: content.yaml.panels[0].points[1]
- P2.label: content.yaml.panels[1].label
- P2.formula: content.yaml.panels[1].formula_latex
- P3.label: content.yaml.panels[2].label
- P4.label: content.yaml.panels[3].label
- caption: content.yaml.caption

> One row per `{{<path>}}` placeholder that appears in the chosen template SVG. Right-hand side is the dotted path inside `content.yaml`. **Every placeholder in the template must have a row here**; unmapped placeholders are a `FAIL` in the audit. **Every row's value must come from `content.yaml` only** — never hardcode display strings here.
>
> When `template_key: none`, omit this section entirely (AI generation has no slots).

---

## color_var_map
- "var(--primary)": colors.primary
- "var(--accent)": colors.accent
- "var(--muted)": colors.muted
- "var(--surface)": colors.bg
- "var(--border)": colors.border

> One row per CSS variable used in the template SVG. The renderer literally string-replaces the CSS-var token with the HEX from §colors. Templates MUST use these var() tokens, not raw HEX, so they can re-skin per project. Templates without any var() are accepted but warned against in `qa-checklist.md`.

---

## glossary_preserve
- 站点客流可恢复性
- 双链路恢复曲线
- 接驳可达性指数
- TSI

> Copy verbatim from `contract.md §4`. These strings will appear in the SVG / image with **zero modification** — no translation, no abbreviation, no case folding. The renderer fails the audit if any of these strings is mutated.

---

## emphasis_panel
- panel_id: P3
- reason: contract.md §3 P3 carries the "what we learnt" punchline

> Optional. Set ONLY when the figure has a single panel that should carry the `accent` color (≤ 5% area). All other panels use `primary` / `muted`. Omit if the figure has no emphasis.

---

## output
- svg_path: projects/{project_name}/output/route_{archetype}_{timestamp}.svg
- png_path: projects/{project_name}/output/route_{archetype}_{timestamp}.png
- png_size: 2K
- aspect_ratio: 16:9
- prompt_log_path: projects/{project_name}/output/route_{archetype}_{timestamp}_prompt.txt
- audit_path: projects/{project_name}/audit_report.md

> When `template_key: none`, `svg_path` may be omitted (AI generation produces PNG only). Otherwise both `svg_path` and `png_path` are required.

---

## forbidden
- emojis anywhere (including `glossary_preserve` strings — strip emojis from source before listing)
- watermarks, URLs, social-media logos in the rendered output
- raw HEX in templates (must go through `color_var_map`)
- mixing CJK and Latin under one `<tspan>` font-family
- using `glossary_preserve` strings as ENGLISH abbreviations or translated forms anywhere in the figure
- 3D / drop shadows / saturated gradients / freestyle curved arrows (except `workflow.circular`)
- node text / data values / place names / author names copied from any `gallery_refs` image

> The last bullet is the **academic-integrity guardrail**. Gallery images are style anchors only; their content (numbers, place names, model names) must never appear in the produced figure unless it independently appears in `content.yaml` (which itself derives strictly from the user's material).

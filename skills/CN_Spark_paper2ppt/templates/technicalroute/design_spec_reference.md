# `{project_name}` · Design Spec (single-figure)

> **Skeleton for the main agent. Do NOT copy this file verbatim into a project**——only emit `##` sections with filled-in `-` data lines. Strip all `>` blockquotes (those are author-time guidance, not runtime data).
>
> **Position in the pipeline (TR engine, contract-first):**
>
> `contract.md` (argumentation) → `content.yaml` (typed content) → **`design_spec.md` (this file: visual rationale, human-readable)** → `spec_lock.md` (machine-readable execution lock) → `prompt.md` → `image_gen.py` / template-assembly → `audit_report.md`
>
> design_spec narrates **why** we chose this canvas / archetype / template / palette. spec_lock fixes the **what** the renderer must use. Both must stay in sync; on divergence, **`spec_lock.md` wins** (it is what gets read by the renderer).

## I. Project Information

| Item | Value |
|---|---|
| **Project Name** | {project_name} |
| **Created Date** | {date_str} |
| **Caller** | `standalone` / `cn-academic-spark-ppt-engine` |
| **Target Output** | PNG only / Editable SVG + PNG / Embedded into PPT slide |
| **Contract ref** | `contract.md` (§1 core claim, §2 archetype, §6 reference mode) |

---

## II. Canvas Specification

| Property | Value |
|---|---|
| **Canvas Format** | `ppt169` (1280 × 720) — default for standalone academic figures and for PPT-embed |
| **viewBox** | `0 0 1280 720` |
| **Aspect Ratio** | 16:9 |
| **Margins** | left/right 60–80 px, top 60 px, bottom 80 px (reserve for caption / source line) |
| **Caption Position** | below-figure (use the bottom 60 px) / inside-figure (top-bar) / none |

> Alternative canvases — `1024 × 768` (4:3 deck embed), `1242 × 1660` (Xiaohongshu vertical), `1080 × 1080` (square poster). If using a non-`ppt169` canvas, mirror the change in `spec_lock.md §canvas`.

---

## III. Archetype × Sub-variant (carried from `contract.md §2`)

| Item | Value |
|---|---|
| **Archetype** | `thinking` / `method` / `workflow` |
| **Sub-variant** | one of `quad` / `cascade` / `twin` / `core-steps` / `vertical-stack` / `formula-grid` / `mechanism-block` / `horizontal-pipeline` / `twin-track` / `funnel` / `circular` |
| **Argument Flow** | left→right / top→bottom / center→outward / circular CW / two-track converging |
| **Panel Count** | the exact number from `content.yaml` (do NOT over-fill empty panels) |

> The archetype + sub-variant pair must already be locked in `contract.md §2` before this file is written. If you find the contract's choice doesn't match the actual content shape, **stop and revise the contract** — do not silently override here.

---

## IV. Reference Chain — Gallery first, Template second, AI third

> **Reading order (always)**: `Custom_gallery/<discipline>/` 取结构/风格 anchor → `templates/templates_index.json` 找能装下 gallery 那种结构的可编辑模板 → 找不到合适模板就 AI 生 PNG。
>
> Gallery 不是"模板找不到才看"的兜底，**它是工作流的起点**——它告诉我们"这种论文里行业里同主题的图大概长什么样、有几格、什么流向、用什么色调"。模板与 AI 都按这个 anchor 去定。

### IV.1 Gallery Anchor (always; first read)

Read [`assets/Custom_gallery/<discipline>/trans-manifest.json`](Custom_gallery/) — when present — and pick 1–3 anchor images whose `agentKeywords` overlap with our `content.yaml.themes` or `contract.md §1` core claim.

| Item | Value |
|---|---|
| **Discipline folder** | `<discipline>` (e.g. `transportation`, `biology`) — matched to the paper's field |
| **Anchor images** | 1–3 filenames from that folder (e.g. `algorithm-workflow.jpg`, `全文思路.png`) |
| **Why each one** | quote the `plotSummary` (gallery manifest) that says when to pick this anchor |
| **Visual signal extracted** | one line per anchor: panel count, flow direction (横向/纵向/环形/双轨), color discipline, density |
| **What we copy** | **structure** (panel count / flow direction / proportion) + **color discipline**. Nothing else. |
| **What we DO NOT copy** | node text, data values, place names, author names, model names, dataset names, formulas — even when the gallery image's content fits our topic, those strings must come from `content.yaml` (i.e. user's own paper). |

> **Academic-integrity guardrail (HARD)**: Gallery images are style anchors. If a gallery image's caption / labels contain a phrase that also fits our paper, source that phrase from the user's own material — never from the gallery — and list it in `contract.md §4 glossary_preserve` so renderer + audit both lock onto the user-source version.
>
> When the discipline folder has no `trans-manifest.json` yet (e.g. 13 of the 14 stub folders pre-Phase-2 finish), fall through to IV.3 directly — do NOT make up a gallery anchor.

### IV.2 Template Assembly (editable SVG — the preferred output)

With the gallery anchor's structure in mind, read [`assets/templates/templates_index.json`](templates/templates_index.json) and pick the highest-scoring template under the chosen archetype **whose `sub_variant_hint` matches the gallery anchor's structure**.

| Item | Value |
|---|---|
| **Selected Template** | `<template_key>` (e.g. `pipeline_with_stages`) — must exist in `templates_index.json.templates` |
| **Why this one** | quote the entry's `summary` "Pick for …" clause that matches our content shape + the gallery anchor's structure |
| **Why not the runners-up** | name 1–2 close-but-rejected templates with the `Skip if …` clause that ruled them out |
| **Slot Substitution Plan** | list each `{{path}}` placeholder in the template SVG and where its value comes from in `content.yaml` |

If **no template scores ≥ 2** under the chosen archetype, or **no template's `sub_variant_hint` matches the gallery anchor's structure** → set `Selected Template: none` and fall through to IV.3.

### IV.3 AI PNG Fallback (last resort — raster only when SVG assembly is not possible)

Used **only** when IV.2 returned `Selected Template: none`. The gallery anchor from IV.1 is still passed as `--reference` to the image backend.

| Item | Value |
|---|---|
| **Backend** | `gemini` (nano banana pro, default) / `qwen` (image2, Qwen Image 2.0) / `openai-image` / `volcengine-seedream` |
| **Why PNG instead of SVG** | one line: "no template under archetype `<X>` matches sub_variant `<Y>` and gallery structure `<Z>`" — must be specific |
| **References passed** | the gallery anchor filenames from IV.1 (these go in as `--reference`); + any literature `style_refs/*.png` from Step 3 |
| **Atlas-only mode** | yes / no — see `references/handling-no-references.md` |
| **Failure plan** | retry once without `--reference` → switch backend (gemini → qwen) → emit half-product per `handling-no-references.md` ladder C |

> **任务 8 的明确兜底**：如果按 `templates_index.json` 找不到合适的模板来装配可编辑技术路线图，**直接走 IV.3 出 PNG**——不要硬塞一个不匹配的模板（会出难看的图），也不要拒绝交付。nano banana pro / image2 任选其一，把 gallery anchor 当视觉参考喂进去即可。

---

## V. Color Scheme

> Strategist: when the caller is `cn-academic-spark-ppt-engine`, copy the deck-level palette from the PPT engine's `design_spec.md §III` (the figure must not diverge from the deck). Standalone TR projects pick from `references/color-typography.md` named palettes.

| Role | HEX | Notes |
|---|---|---|
| **Background** | `#FFFFFF` (default) or `#FAFAFA` | Pure white preferred for academic figures |
| **Primary** | `#......` | Main lines / boxes / titles — uses ≤ 60% of ink |
| **Accent** | `#......` | The ONE emphasis color — uses ≤ 5% of ink. Reserved for `<emphasis>` panel only. |
| **Muted** | `#......` | Secondary boxes / annotations |
| **Border / Divider** | `#......` | Panel borders, axis lines |
| **Body text** | `#222222` | Default body text |
| **Caption** | `#666666` | Source line, "Figure N: …" |

> **Hard rules** (inherited from `references/color-typography.md`):
> - At most 1 primary + 1 accent + 1 muted + 1 border + 2 text colors. No rainbow palettes.
> - Accent color area ≤ 5% of canvas.
> - Saturated red is reserved for genuine "warning / negative" semantic; never decorative.

---

## VI. Typography

| Role | Stack | Size (px) | Notes |
|---|---|---|---|
| **Title** | `"Microsoft YaHei", sans-serif` (CJK) / `"Times New Roman", serif` (Latin) | 28–32 | Mixed-language titles MUST split into `<tspan>` segments — never one font for both. |
| **Panel label** | same as title | 18–22 | One-line label per panel. |
| **Body** | `"Microsoft YaHei", sans-serif` (CJK) / `"Inter", "Arial", sans-serif` (Latin) | 14–16 | Body points / annotations. |
| **Formula** | `"STIX Two Math", "Cambria Math", "Times New Roman", serif` | 16–20 | Required for any `method-formula-grid` cell. |
| **Caption** | same as body | 12 | Bottom caption / source line. |

> Same mixed-CJK-Latin discipline as the PPT engine: middle-school students don't get a free pass to render Latin characters with `Microsoft YaHei`. Use `<tspan font-family="...">` to switch fonts inline.

---

## VII. Panel-by-Panel Visual Plan

> One row per panel from `content.yaml`. Strategist writes one line per panel describing the visual treatment — Executor uses this as the bridge between yaml data and SVG output.

| Panel ID | Source (`content.yaml` path) | Shape Recipe | Color Role | Notes |
|---|---|---|---|---|
| `P1` | `panels[0]` | `R1` panel box + `R2` step badge | primary border, muted fill | Carries the lead-in claim |
| `P2` | `panels[1]` | `R3` formula box | muted fill | Equation 1 |
| `P3` | `panels[2]` | `R4` arrow strip | accent | Single arrow between P2 and P4 — emphasis |
| `…` | `…` | `…` | `…` | `…` |

> `Shape Recipe` refers to `references/shape-recipes.md` R1–R10. Reuse rather than invent.

---

## VIII. Reference & Citation Plan

> When this figure ends up embedded in a PPT slide, the PPT engine writes a GB/T 7714 footer on that slide. The TR engine still records the source authority for traceability.

| Item | Value |
|---|---|
| **Style ref source** | `style_refs/manifest.json` (Step 3 output) — the 5+ literature figures we matched in style |
| **Content ref source** | the user's own paper / draft — `content.yaml.themes`, `contract.md §3 panels` derived solely from here |
| **Glossary preserved** | `contract.md §4 glossary_preserve` — these strings appear in SVG VERBATIM, no translation / no abbreviation |
| **Caption format** | "Figure N · `<contract.md §1 core claim short form>`" + " 来源: 作者绘制 " (always; never claim a figure from the reference set) |

---

## IX. Output Plan

| File | Path | Format | Notes |
|---|---|---|---|
| **Editable figure** | `projects/<name>/output/route_<archetype>_<ts>.svg` | SVG | Emitted only when IV.1 picked a template; this is the primary deliverable. |
| **Raster figure** | `projects/<name>/output/route_<archetype>_<ts>.png` | PNG, 2K, 16:9 | Emitted always. Either rasterised from the SVG (`finalize_svg`) or directly from `image_gen.py`. |
| **Prompt log** | `projects/<name>/output/route_<archetype>_<ts>_prompt.txt` | plain text | Frozen prompt for reproducibility. |
| **Audit report** | `projects/<name>/audit_report.md` | Markdown | Step 8 hard + soft + reviewer-risk checks. |

---

## X. Checkpoint (must hold before writing `spec_lock.md`)

- [ ] `contract.md` §1–§8 all filled and user-confirmed.
- [ ] `content.yaml` validates clean (`scripts/content_schema.py validate`).
- [ ] §III archetype × sub-variant matches `contract.md §2` verbatim.
- [ ] §IV.1 picked ≥ 1 gallery anchor (or explicitly noted the discipline folder is empty / no manifest).
- [ ] §IV.2 either picked a template (key exists in `templates_index.json`) AND its `sub_variant_hint` matches the gallery anchor's structure, OR explicitly fell through to IV.3 with a one-line "why PNG instead of SVG".
- [ ] When falling through to IV.3, the gallery anchor from IV.1 IS passed as `--reference` (not silently dropped).
- [ ] §V palette either inherited from caller deck or chosen from named palette in `references/color-typography.md` (no ad-hoc HEX).
- [ ] §VII panel plan covers every `content.yaml.panels[*]` (no orphan panels, no fabricated panels).
- [ ] §VIII glossary lines are byte-identical to `contract.md §4`.

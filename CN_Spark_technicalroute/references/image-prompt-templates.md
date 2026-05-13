# Image Prompt Templates · 通用 prompt 骨架（placeholder-driven）

> 每个 archetype × sub_variant 都有一份**英文骨架 prompt**（描述结构与风格，喂给图像模型）+ **中文 CONTENT 注入区**（描述实际节点文字，逐字保留）。骨架不写入任何学科 / 主题 / 案例，所有具体内容由 `content.yaml` 注入。

## 拼装函数（被 `generate_route_image.py prompt` 调用）

```python
def build_prompt(archetype, sub_variant, content, contract, color_scheme, reference_mode):
    return "\n\n".join([
        COMMON_PREAMBLE,
        f"[ARCHETYPE]\n{archetype} / {sub_variant}",
        "[STRUCTURE]\n" + render_skeleton(archetype, sub_variant, content),
        "[SHAPE RECIPES]\n" + render_recipes(archetype, sub_variant),
        "[COLOR DISCIPLINE]\n" + render_palette(color_scheme),
        "[TYPOGRAPHY]\n" + render_typography(content.get("typography", "cn_yahei_en_times")),
        "[CHINESE CONTENT — render exactly as written, no translation]\n" + render_cn_content(content),
        "[GLOSSARY — preserve verbatim]\n" + render_glossary(content.get("glossary_preserve", [])),
        atlas_only_clause(reference_mode),
        "[NEGATIVE]\n" + NEGATIVE,
    ])
```

---

## COMMON_PREAMBLE（每个 archetype 都注入）

```
A high-resolution academic infographic in the visual language of contemporary scholarly
research-framework / technical-route figures. Flat 2D vector style. Pure white background.

No 3D, no isometric, no drop shadows, no glow effects, no gradients, no emoji, no stock
photo people, no watermarks, no URLs, no social media logos, no rainbow palette.

Typography: Chinese characters render in a clean sans-serif consistent with the
[TYPOGRAPHY] block; Latin characters and numbers render in the serif specified there.
All text must be sharp, legible, free of artifacts and untruncated.

Color discipline: obey the [COLOR DISCIPLINE] block strictly. Use AT MOST four hues:
primary / secondary / accent / muted. Avoid saturated reds except for the position
explicitly designated in [STRUCTURE]. Accent area must be ≤ 5% of canvas.

Line discipline: arrows are straight or right-angled (elbow), never curved freestyle
unless the archetype is `workflow circular`. Borders are thin (1–2px). Panel corners
are 8–16px rounded.

Composition discipline: there must be a clear reading order. Every visible text element
must correspond to a node listed in [CHINESE CONTENT] below. Do NOT invent nodes,
captions, authors, citations, or numbers that are not listed.
```

---

## Archetype = thinking

### sub_variant `quad`

```
Render a 2×2 panel grid filling ~85% of canvas height, plus an optional bottom anchor
banner spanning full width.

Each of the four panels is a R1 panel with: radius=12, border=thin, fill=surface,
badge=R2 number_circle (1 / 2 / 3 / 4) at top_left, padding=normal.

Inside each panel, top-row: badge + label + leading icon hinted by content.icon_hint.
Body of the panel renders bullets (or a 2×2 mini-grid if content provides table_2x2).

NO arrows between panels — they are concurrent supports of the same claim.

If [STRUCTURE.bottom_anchor] is non-empty, render a R4 banner at the bottom with
position=bottom, height=56px (proportional), fill_role from accent or primary as
indicated, with a leading icon (target / lightbulb / question depending on
bottom_anchor.kind), and the verbatim text from [CHINESE CONTENT.bottom_anchor].
```

### sub_variant `cascade`

```
Render N=3–5 panels stacked vertically, each spanning ~80% of canvas width and centered.

Each panel is R1 with radius=12, border=thin, badge=R2 step_pill at top_left
("01" / "02" / "03" …).

Between consecutive panels, render a R3 arrow: kind=straight, weight=thin, head=chevron,
pointing downward, no label. Vertical gap between panels: ~24px (proportional).

If [STRUCTURE.bottom_anchor] is non-empty, render a R4 banner below the last panel.
```

### sub_variant `twin`

```
Render TWO large columns side by side, each ~46% canvas width with ~6% gap.
Each column has a top R2 tag_pill with its label.

If [STRUCTURE.top_bridge] is non-empty, render a thin R4 banner at top (height=40px,
fill_role=primary) spanning both columns with verbatim text.

Inside each column, render bullets / contrast lists as flat unboxed lines (icon + text).
The left column uses primary tint; the right column uses secondary tint.

If [STRUCTURE.bottom_anchor] is non-empty, render a R4 banner at bottom (fill_role
=accent if kind=question, otherwise primary) spanning both columns.

NO arrows between the two columns — the comparison is read in parallel.
```

---

## Archetype = method

### sub_variant `core-steps`

```
Render ONE "core idea" R1 card on the left (~28% width) with a R2 corner_icon
(lightbulb on a tinted circle) and the verbatim core_idea.text inside.

Then render N=2–4 Step cards filling the remaining ~70% width horizontally with
~3% gaps between them.

Each Step card is R1 with radius=16, border=thin. At the top of each step card,
render a R2 top_color_bar in the color matching step.color_role (primary or
secondary cycled). White text inside the bar: "Step N <step.label>".

The center of each step card is a R5 formula_box: bg=#F5F8FB, padding=28px, font_style
=LaTeX serif, math italics for variables, roman for indices, with the verbatim
formula_latex.

Below the formula_box: 14px muted grey caption beginning with "含义：" or "Meaning:"
(language matches the user input) followed by verbatim interpretation.

R3 thin straight arrows (head=open) between consecutive step cards.

If [STRUCTURE.symbols] non-empty, render a R9 symbol_legend_strip below the step row.

If [STRUCTURE.assumptions] non-empty, render up to 3 R10 assumption_cards in a single
horizontal row at the bottom of the canvas.
```

### sub_variant `vertical-stack`

```
Render N=4–8 step rows stacked vertically. Each row is a full-width R1 panel split
horizontally into: left 30% (R2 step_pill with label) + middle 35% (R5 formula_box)
+ right 35% (interpretation text in 14px muted).

Color cycling on the step pills: primary / secondary alternating, no rainbow.

No arrows between rows — vertical stacking implies ordered execution.

Bottom row: R9 symbol_legend_strip if symbols non-empty.
```

### sub_variant `formula-grid`

```
Render a 1×N or 2×2 grid of R5 formula_boxes. Each box has the verbatim formula_latex
plus a R2 tag_pill in the top-left containing the label ("(1)" / "(a)" / etc.).

Below each box: a 14px muted note line with verbatim note text.

No arrows. No banner. Just the grid.
```

### sub_variant `mechanism-block`

```
Render three large R1 cards horizontally: Input (left, ~25%) → Mechanism (middle,
~45%) → Output (right, ~25%).

Input card: verbatim list of input items, each with a small leading icon.

Mechanism card: an internal diagram in the style hinted by process_visual_hint
(layered / tree / iterative_loop / black_box / neural_net). The mechanism is a
schematic abstraction, NOT a literal mathematical diagram. Use R7 tree/network
recipe if applicable.

Output card: verbatim list of output items.

R3 thick straight arrows (weight=heavy, head=triangle) between Input → Mechanism
→ Output, with optional italic muted labels if specified.
```

---

## Archetype = workflow

### sub_variant `horizontal-pipeline`

```
Render N=3–5 column groups across the canvas left-to-right. Column headers are thin
bold sans-serif labels (NOT boxed) above each column.

Column rendering by kind:
- If column has `items` (data sources): render each as a small badge: small
  brand-like logo placeholder + name + source line in italic muted. Vertical stack.
- If column has `blocks` (processes / algorithms): render each as a R1 small card
  with optional R8 mini chart based on visual_hint (scatter_map / cylinder_stack /
  tree / shap_bars / heatmap / network / scatter_with_fit_line).
- Special case visual_hint=cylinder_stack: render a R6 cylinder stack with 3–5
  layers, tilted ≤ 5°.
- Special case visual_hint=tree or shap_bars: use R7 tree/network recipe.

Between consecutive columns: R3 heavy straight arrow (weight=heavy, head=triangle)
with italic muted grey LABEL from column.arrow_label.

Information density: dense — fill the canvas without overlaps. White background. No
panel-number badges (this is workflow, not thinking).
```

### sub_variant `twin-track`

```
Render TWO parallel horizontal tracks stacked vertically. Each track has its own
header label on the far-left.

For each track, render its blocks left-to-right with thin straight arrows between
them.

At the rightmost position of both tracks, the two tracks merge into a single R1
"confluence" node (shape per confluence.visual_hint: diamond / circle / merge_box),
then a single R3 heavy arrow leads to the right-most "output" R1 card.

Track 1 uses primary tints; Track 2 uses secondary tints.
```

### sub_variant `funnel`

```
Render multiple input badges fanned out on the left (vertical stack with slight
horizontal stagger so they look like a funnel), each a R1 small card.

All inputs converge via thin R3 arrows into a central R1 "core" card (visual_hint:
black_box / neural_net / decision_tree, using R7 tree/network recipe).

Single R3 heavy arrow from core to the right-most "output" card.
```

### sub_variant `circular`

```
Render N=4–6 stage R1 cards arranged on a circle around the canvas center. Each
stage card has a R2 badge with the stage number.

Between consecutive stages: R3 arrows with kind=curved-mild (gentle arcs, NOT
freestyle wiggles), weight=medium, head=triangle, following clockwise direction.

The center of the circle may have a small label or remain empty.
```

---

## CHINESE CONTENT block (auto-rendered from content.yaml)

The function `render_cn_content` walks `content.yaml` and produces a literal text block
listing every Chinese / English string that must appear in the figure verbatim. This is
the figure's **content ground truth** — the image model treats it like subtitles.

Structure (illustrative):

```
[CHINESE CONTENT — render exactly as written, no translation]

标题：<title>
副标题：<subtitle>

(per archetype, list every label / point / bullet / formula / note / symbol /
 assumption / column-arrow-label / etc. line by line)
```

Order matches the figure reading order.

---

## GLOSSARY block

```
[GLOSSARY — preserve verbatim, do not translate or paraphrase]
- <术语 1>
- <term 2>
- ...
```

Image model must render each glossary term **byte-identical** to its listing — no
spacing changes, no font-style swaps, no abbreviation, no transliteration.

---

## atlas_only clause（reference_mode == "atlas_only" 时插入）

```
[ATLAS-ONLY MODE]
No literature reference images are provided. Render using ONLY the [STRUCTURE]
block, [SHAPE RECIPES], and [COLOR DISCIPLINE] above as the source of layout
truth. Default to a clean, restrained, academic-poster look with generous white
space, thin strokes, flat fills, and no decorative flourishes.
```

---

## NEGATIVE block

```
no 3D, no isometric, no drop shadows, no glow effects, no gradients,
no emoji, no stock photo of people, no watermarks, no URLs, no social media logos,
no rainbow palette, no oversaturated red except in the explicitly designated banner
position,
no curved freestyle arrows (except for archetype=workflow sub_variant=circular),
no decorative flourishes,
no nodes / captions / authors / citations / numbers not listed in [CHINESE CONTENT]
or [GLOSSARY],
no Chinese typos, no character cutoffs, no garbled CJK,
no translation, paraphrase, abbreviation, or transliteration of any [GLOSSARY] term,
no English-only output if Chinese content is provided,
no extra panels, columns, steps, or stages beyond what [STRUCTURE] specifies
```

---

## 使用 reference images（literature 模式）

literature 模式下传入的参考图作为视觉风格 anchor。Prompt 头部追加：

```
[REFERENCE IMAGE USAGE]
The provided reference images are STYLE ANCHORS ONLY. Use them to guide:
  - panel rhythm and spacing
  - color saturation level
  - icon density and weight
  - line stroke weight
  - typography weight

DO NOT copy any text, node labels, formula, author name, citation, or specific
content from the references. Replace 100% of the content with [CHINESE CONTENT].
The references' Chinese / English / numeric content is irrelevant to this figure.
```

这条 clause 是 image2-to-image 接口下的**关键稳定性条款**——没有它模型会偷懒抄参考图文本。

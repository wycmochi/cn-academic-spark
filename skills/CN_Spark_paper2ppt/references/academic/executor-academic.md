# Executor Academic
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 6 被执行器读取；它补充中文学术 PPT 的引文页脚、底部横幅、公式页、研究框架页、颜色策略和自检规则。

General execution rules are in `../executor-base.md`; SVG and PPT compatibility constraints are in `../shared-standards.md`. This file only defines academic additions. In academic mode, use this file as the style executor and do not load non-academic consultant executor flows.

## 1. Role

You are the SVG executor for Chinese academic presentations: argument pages, evidence pages, result pages, formula pages, research framework pages, TechnicalRoute embed pages, literature review matrices, and reference pages.

Style target: restrained, rigorous, information-dense, readable aloud, and free of decorative clutter. Every content page must communicate one clear academic claim.

## 2. Whole-Deck Color Strategy

Color serves information, not decoration. Apply the strategy across the entire deck, except citation footers, which remain muted gray and must not be made visually dominant.

| Purpose | Academic rule |
|---|---|
| Focus | Highlight the target variable, key model, or main finding in the theme color; keep context, baselines, and secondary series gray. |
| Reduce cognitive load | For one data family, use the same hue with opacity or lightness variations instead of unrelated colors. |
| Semantics | Green means improvement / positive direction; red means risk, contradiction, negative direction, or statistically important warning; gray means baseline / reference / uncertainty. |
| Branding | Use the institution or template primary color for title accents, bottom banners, route nodes, and small structural lines. Do not add decorative gradients unless the selected template already requires them. |

Commandments:
- Use no more than three primary colors in the deck, plus neutral grays.
- Use the accent color sparingly: at most 2-3 emphasis points per slide, and consistently across the deck.
- Data series should use same-hue depth variations, not rainbow palettes.
- Background should be white or very light gray unless the selected template explicitly defines otherwise.
- Key text must be bold and brick red: use `font-weight="700"` and `fill="#A23B2A"`. Apply this to major takeaways, high-priority warnings, or important evidence phrases only. Do not apply it to citation footer text.

Default palette when `spec_lock.md` does not override it:

| Token | Color | Use |
|---|---|---|
| `primary` | `#1F3864` | Titles, bottom banner, primary nodes. |
| `secondary` | `#4472C4` | Secondary nodes, links, supporting emphasis. |
| `surface` | `#F0F4FA` | Cards, table zebra rows, light panels. |
| `accent_critical` | `#A23B2A` | Brick-red bold key text, risks, contradictions, high-priority findings. |
| `positive` | `#2E7D32` | Positive or improved results only. |
| `muted` | `#888888` | Citations, footnotes, auxiliary labels. |
| `text_main` | `#222222` | Main text. |

## 3. Academic Page Elements

Every evidence or argument page must check these elements. Cover, agenda, section divider, acknowledgement, and pure reference pages may be exceptions.

### 3.1 `citation_footer`

Every page that uses cited claims or source figures must include a citation footer.

```svg
<g id="citation_footer">
  <text x="60" y="650" font-size="11" fill="#888888">
    <tspan font-family="Microsoft YaHei,Source Han Sans SC,sans-serif">[1] Author. Chinese or translated title</tspan><tspan font-family="Times New Roman,serif">[J]. Journal, 2025, 80(3): 512-528.</tspan>
  </text>
</g>
```

Rules:
- Font size 8-11 px; fill `#888888`.
- Place directly above `bottom_banner`, with 1.0-1.2 line spacing. Keep it anchored to the lower footer zone; it should visually sit near the bottom edge, never float in the middle of the slide.
- At most three entries per slide. If more are needed, show the first three plus a pointer to the reference page.
- Split Chinese, Latin text, numbers, and symbols into separate `<tspan>` runs with proper fonts.
- Italicize English journal names when appropriate; do not italicize Chinese journal names.
- Do not add boxes, colored backgrounds, shadows, or brick-red emphasis to citation entries.

### 3.2 Mixed CJK / Latin `<tspan>` Segmentation

Any title, body text, table cell, or citation containing Chinese plus numbers, Latin words, or symbols must be segmented into font-specific `<tspan>` runs.

### 3.3 Page Number, Logo, Bottom Banner

- Page number: in user PPTX template mode, follow the slide/layout/master page-number placeholder recorded in `spec_lock.md`; otherwise use the academic default bottom-right position, between citation footer and bottom banner, 9 px gray.
- If the user PPTX template defines a page-number slot, do not move the generated page number to another location.
- Exactly one visible page number is allowed per slide. A duplicated number such as two `06` labels is a blocking error.
- Logo: use the template-provided logo / protected region when available; otherwise use top right around 40 x 40 px with `<image href="logos/school_logo.png">`.
- Bottom banner: use the page's `bottom_banner_text`; keep it short and claim-like. Treat the banner, citation footer, and page number as a single protected bottom region that body content may not enter.
- None of these may overlap each other.

### 3.4 Cover Metadata Only

The cover is an identity page, not a content page. It may contain the paper/opening topic title, report type, presenter/defense candidate, advisor, institution, date, author list, journal/source, and DOI. It must not contain source figures, formulas, methodology diagrams, route diagrams, result charts, conclusion cards, or teaser summaries; those begin on body slides.

## 4. Academic Layout Skeletons

Use `design_spec.md` section IX `content_type` to choose the skeleton.

| `content_type` | Execution rule |
|---|---|
| `text_flow` | Argument flow page: title, concise body, supporting visual. |
| `bullet_analysis` | Four to six analytical bullets, or 2-3 grouped evidence blocks when the source material is richer. |
| `pipeline` | Use Step 5.5 for complex research routes; hand-draw only simple 3-5 step flows. |
| `matrix_framework` | Three columns: dimensions, modules, outputs. |
| `results_chart` | Left chart / right insights; verify chart data before export. |
| `formula_step` | Stacked derivation panels with rendered formulas. |
| `formula_paragraph` | Formula list plus explanatory prose for four or more formulas. |
| `gantt` | Proposal timeline using `templates/charts/gantt_chart.svg`. |
| `conceptual_framework` | Matrix, thinking map, or timeline for review synthesis. |
| `evidence_matrix` | Native SVG literature comparison table. |
| `references_page` | Numbered reference list; required for Route C and D. |

Use smaller rounded corners by default: `rx="6"` for 1280 x 720 academic slides. For dense tables or tiny tags, use `rx="3"` or no rounding. If a selected template defines a different radius in `spec_lock.md`, follow the template. If a user PPTX template is selected, fill the template's existing placeholders and do not add extra shape frames or text boxes unless the page explicitly falls back to the built-in template library.

Formula rendering is image-based and mandatory for complete formula explanations in both user-PPTX-template mode and built-in-template mode. Read `formula-rendering.md` before any `formula_step` or `formula_paragraph` page. Transcribe all important formulas used by the paper's main academic steps as LaTeX, write each formula role and variable definitions into a formula block JSON, render the role + formula + interpretation with `scripts/latex_formula_to_png.py --block-json`, and embed each result with `<image data-formula-png="true" data-formula-block-png="true">`. Do not rebuild the formula, role label, `式中`, or variable explanations as stacked SVG text boxes. Put at most five formula block PNGs on one slide, use gray 1.5pt dashed separators between adjacent formula blocks, and ensure formula PNGs, explanatory text, and separators never overlap. If a complete displayed equation appears as SVG text, the page is invalid even when the visual layout looks acceptable.

### 4.1 User PPTX Template Slot-Fill Mode

When `spec_lock.md` marks `template.source: user_pptx` or `user_pptx_template: true`, the imported template is authoritative.

Rules:
- Replace text inside the existing title, subtitle, body, footer, and page-number slots; do not place new text boxes over those slots.
- Before drawing each page, read the imported manifest's `editableContentRegion`. Use its `primary` rectangle or one of its `availableRegions` as the true writable area. Do not treat the full 1280 x 720 canvas as writable when the template reserves logo, school name, or footer space.
- Inherit each filled slot's x/y/width/height, font family, font size, weight, color, alignment, and line spacing unless the user explicitly asks to change it.
- Use imported picture/content placeholders for source figures, formula PNGs, charts, and TechnicalRoute images. Do not add extra picture frames when a suitable placeholder exists.
- Delete unused prompt text and unused picture/body placeholders before final export. Visible prompts such as `Click to edit...`, `单击此处...`, or `演讲者/课程名称` are blocking errors.
- Protect school name, college name, logo, page number, footer marks, and authored master graphics. Title, subtitle, images, formulas, and route diagrams may not overlap these protected regions.
- Do not split one semantic phrase into multiple stacked text boxes. Use one bounded text element with `<tspan>` line breaks.
- Body text boxes must never overlap, and the gap between any two body text-box boundaries must be at least 3 pt. If the gap would be smaller, merge adjacent text into one box, enlarge the containing shape, or compress sibling spacing before export.
- Keep slide content vertically centered inside the actual writable region, not near the top of the page. Use the content region's midpoint as the visual center and reserve the footer region for citation, bottom banner, and page number.
- Body slides, except cover and ending/Q&A, should fill the writable region rather than leaving one small text island. Target at least 80% width and 75% height usage with source-grounded editable text, tables, charts, formula PNGs, route images, or grouped evidence blocks. If a single column leaves blank space, switch to two or three columns before shrinking text.
- On the first and final slides, use one dominant visual layer. Do not stack a paper figure over a cover/thanks image, and do not place an empty white shape over a large image unless it is a deliberate text overlay marked as `overlay` or `scrim`.
- If no imported layout can hold the content, record `layout_source: fallback_template_library` and then use a built-in template page. Do not silently mix free-floating generated objects into a user-PPTX page.

## 5. Strategist Handoff Fields

In `design_spec.md` section IX, every page brief should include academic fields:

```yaml
P05:
  page_rhythm: dense
  content_type: matrix_framework
  page_layouts: 03_content
  page_charts: comparison_table
  bottom_banner_text: "The second dimension explains why dynamic exposure differs from static exposure assessment."
  citations: ["[1]", "[3]"]
  framework_variant: null
```

If `bottom_banner_text` or `citations` are missing, infer them from the page prose and source material, then mark them as auto-filled in the output notes.

## 6. Forbidden In Academic Decks

- Flattening complex route diagrams into unreadable screenshots when editable SVG is available.
- Rasterizing a whole slide into a single `<image id="slide-raster-image">`; all normal slides must remain editable PPT objects after native export.
- Citing a claim without a footer marker or reference-page entry.
- Mixing Chinese and Latin text under one font family.
- Using Times New Roman for Chinese journal names.
- Putting more than six ungrouped bullets on a normal content slide; if content is richer, group it into columns, cards, a table, or a second slide.
- Using decorative shadows, 3D effects, emoji, or ornamental gradients.
- Leaving speaker notes blank.
- Putting source figures, formulas, route diagrams, result visuals, or concrete research-content summaries on the cover slide.
- Using vague section-label titles such as "Methods" for body pages. Use claim-based titles.

## 7. Per-Page Checklist

Summary and thank-you / Q&A must be separate slides. Do not combine conclusion bullets with 谢谢大家 or Thank you on the same page.


- [ ] Title is claim-based and follows the numbered module title rule when applicable.
- [ ] `bottom_banner` exists on evidence / argument pages and does not collide with citations.
- [ ] Every citation marker resolves to `citation_footer` or the reference page.
- [ ] Mixed CJK / Latin / numeric text is segmented by `<tspan>`.
- [ ] Color follows the whole-deck strategy; key text is bold brick red only where justified.
- [ ] Complex TechnicalRoute / Research Workflow / 技术路线 pages come from Step 5.5 rather than local hand drawing, with consecutive editable Version A and AI Version B slides.
- [ ] Non-exempt slides include a meaningful image, chart, formula, or complex table screenshot.
- [ ] Formula pages embed formula title, equation, and variable explanations as one PNG with `data-formula-block-png="true"`; no duplicate SVG text boxes reconstruct the same content; at most five formula blocks per slide; adjacent formula blocks use gray 1.5pt dashed separators; formula/text/separator boxes do not overlap.
- [ ] User-template pages use `editableContentRegion`; all body tables/cards/images/text boxes stay inside the writable region and do not overlap logo, school name, citation/footer, bottom banner, or page-number protected regions.
- [ ] Body text boxes have no overlap and keep at least 3 pt spacing from every neighboring text box.
- [ ] Each slide has exactly one page number, citation/footer text is anchored at the bottom, and first/final pages have no unintended large image/shape stack.
- [ ] `scripts/svg_quality_checker.py` passes before PPTX export, with no full-slide raster image SVG pages. TechnicalRoute Version B appears as a direct PPTX picture slide via `svg_output/_direct_image_slides.json`.

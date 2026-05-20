# Academic Formula Rendering
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在学术 PPT 需要展示或解释公式时读取；上游来自论文/文本解析、`design_spec.md`、`spec_lock.md` 和公式模板索引，下游连接 `scripts/latex_formula_to_png.py`、`images/formulas/`、SVG 公式页插图、质量检查和最终 PPTX 导出。它的作用是强制把公式标题、完整公式和中文变量解释合成为一个透明 PNG，避免公式页被拆成多个重叠文本框。

This is the mandatory flow for formula pages in academic PPT decks. Its purpose is to render "formula title + complete formula + variable explanation" as one transparent PNG, then insert that PNG into the PPT as a single image object, preventing formulas and explanations from being split into multiple overlapping text boxes.

## Trigger Conditions

Use this flow whenever any of the following conditions is true:
- The paper contains key formulas for methods, indicators, models, loss functions, estimation strategies, or explanatory variables.
- `design_spec.md` declares `visual_requirement: formula_png` or `formula_block_png`.
- The page content type is `formula_step` or `formula_paragraph`.
- The slide needs to explain formula variables.

## Formula Selection Rules

First analyze the user-provided paper or text, then extract formulas under the main method, main model, or core metric. Prioritize formulas that:
1. Define a method, model, objective function, estimator, evaluation metric, or inference rule.
2. Are repeatedly referenced by later results or interpretations.
3. Introduce high-frequency variables.
4. Are necessary for understanding the research logic in an oral presentation.

Do not show only one formula while omitting other key formulas from the same main step. Place at most five formula blocks on one page; split to additional pages when there are more.

## Required JSON

For each important formula, write a formula block JSON first, then render the PNG. All explanatory text must be in Chinese; `formula_role` must be a Chinese formula title, and `definition_label` is fixed as `式中：`.

```json
{
  "formula_id": "formula_01",
  "source_location": "第3节 / 式(1) / 第5页",
  "formula_role": "客流恢复力指标",
  "latex": "<忠实转写的 LaTeX>",
  "definition_label": "式中：",
  "variables": [
    {"symbol": "C_{r,i}", "meaning": "站点 i 的客流恢复力，数值越大表示累计损失越小"},
    {"symbol": "P_i(o)", "meaning": "站点 i 在正常状态下第 o 天的客流量"}
  ],
  "png_path": "images/formulas/formula_block_01.png",
  "status": "rendered"
}
```

The placeholder reference is `templates/formula/formula_block_schema.json`. Replace every `{{...}}` before rendering, and do not write `Variables`, `Where`, or `???` into the final JSON.

## Rendering Commands

Preferred command:

```bash
python3 scripts/latex_formula_to_png.py --block-json <project_path>/notes/formula_01.json --out <project_path>/images/formulas/formula_block_01.png --font-size 30 --dpi 260 --color "#111111"
```

This command must create two files together:
- `images/formulas/formula_block_01.png`
- `images/formulas/formula_block_01.meta.json`

The sidecar metadata records the source LaTeX, normalized mathtext LaTeX, renderer name, output size, DPI, and `mathtext_validated: true`. A formula PNG without this metadata is treated as untrusted and must not enter the PPTX export.

Single-formula rendering is for diagnostics only. In the final PPT, explanatory formulas must use formula block PNGs:

```bash
python3 scripts/latex_formula_to_png.py --latex "<latex>" --out <project_path>/images/formulas/formula_01.png --font-size 30 --dpi 260 --color "#111111"
```

## Insertion Method

First read `templates/formula/formula_templates_index.json` and choose `formula_explanation_block`. The SVG template is only an image shell; the formula content must be inserted as one PNG:

```svg
<g id="formula_block_01" data-content-type="formula_block" data-formula-id="formula_01">
  <image id="formula_block_01_png" data-formula-png="true" data-formula-block-png="true" href="images/formulas/formula_block_01.png" x="32" y="130" width="1216" height="120" preserveAspectRatio="xMidYMid meet"/>
</g>
```

Rules:
- One explained formula corresponds to one formula block PNG.
- The PNG itself contains the Chinese formula title, the formula, `式中：`, and Chinese variable explanations.
- The formula title and variable explanations inside the formula block PNG must not be smaller than 18 pt. If they do not fit, enlarge the PNG/SVG insertion region or split to two pages; do not shrink them to 8-12 pt.
- Keep `data-formula-png="true"` and `data-formula-block-png="true"` when inserting into SVG.
- Use gray 1.5 pt dashed separators between multiple formula blocks.
- Formula PNGs, text boxes, and separators must not overlap.
- Place formula block PNGs under `<project_path>/images/formulas/`.
- Keep the paired `.meta.json` beside every formula block PNG; do not move or rename only the PNG.
- Record `usage: formula_block_png` in the `design_spec.md` Image Resource List and in `spec_lock.md images`.

## QA

Check before export:
- Every formula page has at least one `<image ... data-formula-block-png="true">` or `images/formulas/formula_block_*.png`.
- Every formula block PNG has a sibling `.meta.json` with `schema: cn_spark_formula_png_meta_v1`, `renderer: matplotlib.mathtext`, and `mathtext_validated: true`.
- `normalized_latex` in the metadata must be wrapped in `$...$` and must not contain unsupported raw environments such as `\begin{cases}` or `\end{cases}`.
- A single formula page has no more than five formula blocks.
- Formula roles, variable explanations, and `式中：` are not split into SVG text boxes.
- Any equation-like SVG text on a formula page is a blocking error, even if another formula image exists on the same slide.
- Formula block PNG files already exist before `finalize_svg.py`.
- Formula explanation text is in Chinese.
- Adjacent formula blocks and separators do not overlap.

If mathtext cannot parse a LaTeX command, do not export raw LaTeX as visible text. Re-read the source paper, rewrite the formula into supported LaTeX, rerender the PNG, and rerun the quality gate.

---
description: Verify chart coordinates, scale, labels, source binding, and PPTX-safe geometry before final export.
---

# Verify Charts Workflow
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在生成 SVG 后、最终导出 PPTX 前读取；它从 design_spec.md 枚举图表页，使用 svg_position_calculator.py 校验坐标、比例、标签和数据来源，防止图表进入 PPTX 后出现比例错误或坐标漂移。

Standalone post-generation workflow. Run after SVG pages are generated and before final export when the deck contains calculator-supported data charts.

## When To Run

Run when all are true:

- `<project_path>/svg_output/` exists;
- `design_spec.md` declares visualization pages, normally section VII plus section IX page outline;
- at least one declared chart is supported by `scripts/svg_position_calculator.py`;
- final post-processing and PPTX export have not yet run, or a chart was edited after export and must be re-exported.

Do not run for pure conceptual diagrams, TechnicalRoute pages, mind maps, screenshots of paper figures, decorative infographics, or tables without plotted numeric geometry.

## Step 1 - Build The Page List From `design_spec.md`

Read `<project_path>/design_spec.md` section VII as the authoritative visualization plan and cross-check section IX. Do not guess chart pages from SVG content alone.

| Calculator command | Chart keys | Notes |
|---|---|---|
| `calc bar` | `bar_chart`, `horizontal_bar_chart` | Use `--horizontal` for horizontal bars. Single-series direct check. |
| `calc line` | `line_chart`, `area_chart`, `scatter_chart` | Area chart uses line output as top boundary. |
| `calc pie` | `pie_chart`, `donut_chart` | Donut requires `--inner-radius`. |
| `calc radar` | `radar_chart` | Separate command family. |

Repeat-call / manual recipe: `stacked_bar_chart`, `stacked_area_chart`.

Out of scope: grouped, paired, signed-delta, waterfall, bullet, dumbbell, pareto, dual-axis charts; treemap, gauge, funnel, heatmap, matrix, bubble, box plot, KPI cards; process, strategy, architecture, framework, TechnicalRoute, and table diagrams.

If section VII is absent, report `verify-charts skipped: design_spec.md has no authoritative visualization list`. Do not infer silently.

## Step 2 - Per-Page Verification

For each in-scope chart page:

1. Read `<project_path>/svg_output/<page>.svg`.
2. Locate `<!-- chart-plot-area: ... -->` if present.
3. If missing, derive the plot area from axes or radial geometry, then add the marker back after verification.
4. Extract data labels and numeric values from SVG labels or the source chart plan.
5. Extract axis ticks when present.
6. Run the matching calculator.
7. Confirm calculator scale matches the drawn axis before applying any coordinate changes.
8. Update SVG coordinates only when plot area and scale are confirmed.

Example commands:

```bash
python3 scripts/svg_position_calculator.py calc bar --data "A:10,B:20" --area "120,150,1120,560" --bar-width 80 --value-range "0,100"
python3 scripts/svg_position_calculator.py calc bar --horizontal --data "A:10,B:20" --area "120,150,1120,560" --bar-width 42 --value-range "0,100"
python3 scripts/svg_position_calculator.py calc line --data "2020:10,2021:18" --area "120,150,1120,560" --y-range "0,30"
python3 scripts/svg_position_calculator.py calc pie --data "A:40,B:60" --center "640,360" --radius 180
python3 scripts/svg_position_calculator.py calc pie --data "A:40,B:60" --center "640,360" --radius 180 --inner-radius 110
python3 scripts/svg_position_calculator.py calc radar --data "Dim1:80,Dim2:60,Dim3:70" --center "640,360" --radius 180
```

Scale rule: if the SVG has explicit axis ticks, pass the tick-derived range. Do not update coordinates with auto-normalized calculator output when the chart axis is explicit.

## Step 3 - Academic Chart QA

For every verified chart, check:

- plotted values match the source material;
- units are visible and not misleading;
- scale does not exaggerate findings;
- legend labels match plotted series;
- colors follow `spec_lock.md` and the selected template;
- important emphasis uses bold brick red only when justified;
- source note or citation marker exists;
- chart does not collide with title, footer, bottom banner, logo, or page number;
- chart remains editable SVG unless it is an accepted source-paper screenshot.

For paper figures or complex table screenshots, do not use the calculator. Verify resolution, crop, caption, and citation instead.

## Step 4 - Stacked Chart Recipe

For `stacked_bar_chart`, verify each segment with repeated `calc bar` calls using segment values and cumulative offsets.

For `stacked_area_chart`, verify cumulative top boundaries with repeated `calc line` calls.

If negative segments, percent stacks, or nonstandard baselines make the recipe unreliable, mark the page `manual-verify` and inspect by hand. Do not silently pass.

## Step 5 - Receipt

Output one line per in-scope page. Receipt count must equal the Step 1 page count.

```text
verify-charts: 07_model_results.svg | type=bar | scale=0-100 from ticks | calc=ran | svg=updated
verify-charts: 10_ablation.svg | type=line | scale=0-1 | calc=ran | svg=unchanged
verify-charts: 12_resource_mix.svg | type=donut | scale=N/A | calc=ran | marker=added
verify-charts: 15_stacked_area.svg | type=stacked-area | manual-verify | reason=percent stack with nonstandard baseline
```

## Step 6 - Continue Export

After updates, run the current main export chain:

```bash
python3 scripts/svg_quality_checker.py <project_path>/svg_output
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

If the quality checker fails after chart updates, repair the SVG before export. Keep `finalize_svg.py` default steps enabled so image embedding, icon expansion, rounded-rect handling, and placeholder cleanup run consistently.

## Connection To Main Pipeline

This workflow is called from SKILL.md Step 7. It also depends on `references/executor-base.md` requiring chart plot-area markers during SVG generation.

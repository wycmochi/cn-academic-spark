---
description: Launch or replace a visual edit loop for generated SVG slides, then validate and re-export the PPTX.
---

# Visual Edit Workflow
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在用户要求修改已生成页面的视觉效果时读取；它指导基于现有 SVG、spec_lock.md 和用户标注进行局部修改，并重新执行校验、后处理与 PPTX 导出。

Standalone post-export workflow. Use when the user wants to change generated slide visuals and the change is easier to specify by clicking on the slide, or when the user gives vague feedback such as `change this part`, `the text overflows`, `this figure is wrong`, or `make this page cleaner`.

If the user gives a precise edit, apply it directly to the SVG instead of launching the visual editor.

## When To Run

Run when:

- the deck has reached SVG generation or final export;
- `<project_path>/svg_output/` exists;
- the user wants localized visual edits;
- a browser is reachable, or a port can be forwarded.

Do not run when:

- the user requests full regeneration;
- the requested edit is precise enough to apply directly;
- project SVGs are missing.

## Step 1 - Start The Editor

```bash
python3 scripts/svg_editor/server.py <project_path> --no-browser
```

The default server listens on `127.0.0.1:5050` and edits `<project_path>/svg_output/` in place. If the port is busy, pass `--port <other_port>`.

Tell the user:

- the local URL;
- to click the element to change;
- to write a short instruction;
- to submit annotations;
- to return to the conversation when done.

Do not wait for extra confirmation before launching if the user already asked for visual editing.

## Step 2 - Apply Annotations

When the user says annotations were submitted:

```bash
python3 scripts/check_annotations.py <project_path>
```

If no annotations exist, report that and stop.

For each annotated SVG:

1. Read the SVG.
2. Locate elements with `data-edit-target="true"`.
3. Read `data-edit-annotation`.
4. Apply the requested edit while preserving academic constraints.
5. Remove `data-edit-target` and `data-edit-annotation`.
6. Keep paths, ids, and group structure stable unless the edit requires a structural change.

## Step 3 - Academic Edit Constraints

Always preserve:

- `spec_lock.md` colors and typography unless the user explicitly asks to change them;
- user PPTX template palette and geometry priority;
- citation footer readability;
- bottom banner position;
- page number and logo position;
- source figure citation markers;
- TechnicalRoute A/B page pairing;
- non-exempt visual coverage rule;
- text box stability contract.

Text edits:

- prevent overflow;
- do not split one phrase into stacked text boxes;
- keep one semantic phrase in one `<text>` element with `<tspan>` wrapping;
- use explicit `data-box-*` bounds when text is inside or aligned to a visible shape;
- avoid title overlap with school name, logo, footer, or page number;
- re-run quality checks after changes.

Figure edits:

- source figures and table screenshots must preserve aspect ratio unless the user explicitly approves cropping;
- formulas should remain rendered PNGs if they came from LaTeX;
- charts should remain editable SVG when possible;
- user PPTX template placeholders should be filled, not duplicated with new free-floating boxes.

## Step 4 - Re-Run Post-Processing

After edits:

```bash
python3 scripts/svg_quality_checker.py <project_path>/svg_output
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

If the user wants another review loop, restart the editor and keep the same process.

## Step 5 - Direct Edit Fallback

If the editor cannot run:

- ask the user to describe the slide number and change;
- inspect the corresponding SVG manually;
- apply the smallest necessary edit;
- validate and re-export.

## Completion Report

Report:

- annotated pages edited;
- key changes applied;
- validation status;
- updated PPTX path;
- any unresolved annotations or edits that require content judgment.

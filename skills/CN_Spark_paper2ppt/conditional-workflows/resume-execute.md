---
description: Resume SVG generation, validation, and PPTX export from an existing project folder in a fresh session.
---

# Resume Execution Workflow
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在中断后继续已有项目时读取；它通过磁盘上的 design_spec.md、spec_lock.md、sources、images、templates 和 technicalroute 输出判断恢复点，并继续执行 SKILL.md Step 6 与 Step 7。

Standalone continuation workflow. Run when Phase A planning already produced a project folder and the user wants to continue SVG generation, validation, and PPTX export in a fresh session.

This workflow does not recreate the plan. It resumes from disk state and follows SKILL.md Step 6 and Step 7.

## When To Run

Recognize requests such as:

- `continue generating <project_path>`;
- `resume execution for <project_path>`;
- `finish this project`;
- `continue from the existing project folder`;
- a project path plus continuation wording.

Prerequisite: Phase A must already be present in the named project. Do not silently restart Phase A when required state is missing.

## Step 1 - Sanity Check Project State

Verify these before generating any SVG:

| Artifact | Required when | Purpose |
|---|---|---|
| `<project_path>/design_spec.md` | Always | Page outline, academic route, content plan. |
| `<project_path>/spec_lock.md` | Always | Machine-readable execution contract. |
| `<project_path>/sources/` | Always when source files were imported | Concrete facts and evidence. |
| `<project_path>/images/` | `spec_lock.md` references images, formulas, figures, or table screenshots | Asset embedding. |
| `<project_path>/templates/` | `page_layouts` or selected template exists | Template inheritance. |
| `<project_path>/technicalroute/` | TechnicalRoute pages were planned | Route content, route locks, outputs. |
| `<project_path>/notes/` | Existing notes should be preserved | Avoid overwriting user-edited speaker notes. |

If `design_spec.md` or `spec_lock.md` is missing, stop and report the missing file. Do not infer the plan from memory.

## Step 2 - Determine The First Incomplete Step

Use disk evidence:

| State | Resume point |
|---|---|
| TechnicalRoute planned but route output missing | SKILL.md Step 5.5, then Step 6. |
| `svg_output/` missing or incomplete | SKILL.md Step 6. |
| `svg_output/` exists but quality check failed | Repair Step 6 output, then Step 7. |
| `notes/total.md` missing | Step 6 notes generation. |
| Calculator-supported chart pages exist and chart verification missing | `verify-charts.md`, then Step 7. |
| Final PPTX missing | Step 7 export. |
| Final PPTX exists and user asks for tweaks | `visual-edit.md` or direct SVG edit. |

Do not overwrite user-edited SVG, notes, or spec files without confirmation. If files are inconsistent, report the inconsistency and choose the least destructive continuation path.

## Step 3 - Reload Required References

Read:

```text
SKILL.md
references/executor-base.md
references/academic/executor-academic.md
references/shared-standards.md
references/academic/citation-style.md
references/academic/layout-library.md
references/academic/speaker-notes.md
```

Read TechnicalRoute references only if planned pages require them:

```text
references/technicalroute/content-schema.md
references/technicalroute/diagram-contract.md
references/technicalroute/image-templatedraw.md
references/technicalroute/image-aigenerate.md
references/technicalroute/qa-checklist.md
```

## Step 4 - Source Material Rule

A fresh session has no reliable source details in context. Read relevant files under `<project_path>/sources/` while writing each page. `design_spec.md` gives page intent; sources provide concrete claims, figure names, formulas, citations, data values, and terminology.

Never fill evidence pages from outline memory alone.

## Step 5 - Resume TechnicalRoute Safely

If `design_spec.md` or `spec_lock.md` declares TechnicalRoute pages:

- verify each route job has `content.yaml`;
- verify route `spec_lock.md`;
- verify Version A editable SVG output;
- verify Version B AI image output;
- verify the two planned PPT pages are consecutive;
- rerun route audit if any output is missing.

Do not call an external technicalroute skill. Use internal `scripts/technicalroute/` only.

## Step 6 - Continue Step 6 And Step 7

Generate pages sequentially. Before each SVG page:

- re-read project `spec_lock.md`;
- confirm `page_rhythm`;
- confirm `page_layouts` / `page_charts`;
- enforce academic title rules;
- enforce visual coverage rule;
- preserve citation footer, bottom banner, page number, and protected template regions;
- in user PPTX template mode, fill existing slots and avoid extra free-floating shapes/text boxes.

Post-processing and export:

```bash
python3 scripts/svg_quality_checker.py <project_path>/svg_output
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

If the local script signatures differ, follow SKILL.md Step 7 and `scripts/docs/`.

## Step 7 - Chart Verification

If `design_spec.md` section VII declares calculator-supported charts, run `verify-charts.md` before final export. Do not guess chart pages from SVG alone when the design spec has no visualization section.

## Completion Report

Report:

- resume point used;
- repaired or generated files;
- skipped steps and why;
- final PPTX path;
- any remaining risks, such as missing source figures, unresolved citations, or accepted template guard warnings.

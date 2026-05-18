---
description: Gather citeable academic source materials when the user supplies only a topic or broad requirements without source files.
---

# Topic Research Workflow
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在用户只有主题但没有论文、报告、URL 或其他材料时读取；它指导检索权威可引用资料、保存研究文档和候选图片，并把产物交给 SKILL.md Step 1/2。

Standalone pre-processing workflow. Run before SKILL.md Step 1 when the user asks for an academic PPT but provides only a topic, requirement, or broad direction without source files.

Output is a citeable research Markdown document plus an image / figure folder that can be imported as source material.

## When To Run

| User input | Action |
|---|---|
| Topic only | Run this workflow. |
| Requirement description without substantive facts | Run this workflow. |
| One or more academic source files attached | Skip; go to SKILL.md Step 1. |
| At least one page of substantive pasted content | Skip; treat chat content as source material. |
| User explicitly asks for a literature-backed deck but no source package exists | Run this workflow. |

## Step 1 - Confirm Scope Once

Ask one bundled clarification only when the initial request is under-specified:

- topic;
- academic field;
- intended route if obvious: paper explanation, course report, proposal, or literature review;
- depth;
- time span;
- output language;
- target audience;
- expected source type;
- file slug.

Do not ask row by row. If the user already specified enough, proceed.

## Step 2 - Source Priority

Use citeable sources. For academic decks, prioritize:

| Tier | Source type |
|---|---|
| 1 | User-provided papers, PDFs, datasets, reports. |
| 2 | DOI landing pages, journal pages, conference proceedings, official preprint pages. |
| 3 | University, laboratory, government, standards body, institutional pages. |
| 4 | Reputable academic databases, textbooks, official project docs. |
| 5 | Reputable news or policy sources only for Route B context. |
| Avoid | Unsourced blogs, reposts, watermarked stock images, social posts without primary source. |

For Route C and Route D, gather enough references to support a reference page. For Route D, prefer a small representative paper set over shallow coverage of many unrelated sources.

## Step 3 - Search Strategy

Use available web search tools if the environment supports them. If web tools are unavailable, ask the user for 2-4 authoritative URLs and convert them with:

```bash
python3 scripts/source_to_md/web_to_md.py <URL>
```

Search in phases:

1. Broad landscape search to identify field vocabulary and authoritative sources.
2. Targeted search for high-value papers, reports, datasets, standards, or official pages.
3. Figure / table search from original source pages only.
4. Citation metadata cleanup.

Stop when the material covers background, core concepts, representative evidence, current gap or controversy, source list, and candidate figures or tables.

## Step 4 - Save Research Artifacts

Save under `projects/`, not the repository root:

| Artifact | Path |
|---|---|
| Research document | `projects/<topic_slug>.md` |
| Image / figure folder | `projects/<topic_slug>/` |

Filename and folder name must match.

Research document structure:

```markdown
# <Topic>

## Scope
## Key Questions
## Background
## Core Concepts
## Evidence And Findings
## Candidate Figures And Tables
## Open Questions
## Suggested PPT Route
## Sources
```

Every factual claim that is likely to enter the PPT must be backed by a listed source.

## Step 5 - Figure And Image Rules

Prefer figures from papers, official charts, government statistics, dataset diagrams, institution-provided images, and complex tables that can be screenshotted with citation.

Avoid decorative stock images, unsourced internet diagrams, low-resolution reposted figures, watermarked images, and images whose license or origin is unclear.

Use descriptive English snake_case filenames such as `study_flow_diagram.png`, `policy_timeline_2024.png`, or `dataset_sample_distribution.png`.

## Step 6 - Route Handoff

Recommend a route:

- Route A: one specific paper dominates.
- Route B: course report, policy report, case analysis, or thematic report.
- Route C: proposal or research plan.
- Route D: literature review or multi-paper synthesis.

The output Markdown should contain enough structure for SKILL.md Step 1 and Step 4 to classify paper type and build the deck.

## Hand-Off

After saving artifacts, continue with the main pipeline:

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> projects/<topic_slug>.md projects/<topic_slug>/*.* --move
```

Report:

- research document path;
- number of sources;
- number of images / figures;
- recommended route;
- any gaps or sources requiring user confirmation.

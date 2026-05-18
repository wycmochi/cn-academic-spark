# Route D Literature Review
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 4 判断为文献综述或 review 汇报时读取；它组织检索范围、证据地图、主题聚类、概念框架和研究展望。

Use this route for review articles, perspective papers, journal-club synthesis across multiple papers, literature review reports, and pre-proposal research landscape decks.

## Selection Signals

Choose Route D when:
- the input is a review / perspective paper;
- the input contains five or more related papers;
- the user provides a literature review outline, reading notes, or bibliography;
- the goal is to clarify a field's research landscape rather than present one hypothesis.

Evaluation criteria:
- reasonable classification;
- coverage;
- clear lineage;
- accurate citations;
- meaningful gaps and future directions.

## Narrative Skeleton

Use an evidence-map axis:

```text
why the topic matters now -> review scope -> evidence map -> conceptual framework -> theme details -> relations and controversies -> research gaps -> synthesis and future directions
```

A review deck should answer:
- What does the field look like?
- Which themes or methods structure the literature?
- Where do studies agree or disagree?
- What gaps remain?
- What should be done next?

## Default Page Structure

```text
P01 Cover: title, time span, author, institution, date
P02 Agenda
P03 Review Background And Significance
P04 Review Scope: what is included, excluded, and time span
P05 Search And Screening Method: databases, keywords, inclusion / exclusion, final corpus
P06 Conceptual Framework Visualization: required core page
P07 Theme 1: method lineage
P08 Theme 1: representative evidence
P09 Theme 2: method lineage
P10 Theme 2: representative evidence
P11 Theme 3: optional, depending on topic count
P12 Cross-Theme Relations / Evolution / Controversy
P13 Research Gaps And Open Questions
P14 Author Synthesis And Future Directions
P15 Review Limitations
P16 Full References: may span multiple pages
P17 Acknowledgement / Q&A
```

Typical length: 13-18 slides. Dense reviews may need multiple reference pages.

## Required Artifacts

Route D must include:
- review scope;
- evidence map or search / inclusion summary when available;
- conceptual framework page;
- theme detail pages;
- controversy / relation page;
- research gap page;
- complete reference page.
- standalone summary page and separate final thank-you / Q&A page.

Use Step 5.5 for complex thinking maps, conceptual frameworks, or whole-field workflows.

## Core Page: Conceptual Framework

The conceptual framework page is the signature Route D page. It should use one of three forms.

### Form 1: Theme Matrix

Default recommendation. Best for dense academic synthesis.

Rows are themes. Columns may include:
- core methods;
- main findings;
- representative papers;
- limitations;
- relevance to this review.

Reference cells should contain markers only, such as `[1][3]`. Full entries go to the reference page.

Use when:
- theme count is 4-6;
- each theme has multiple papers;
- print readability matters.

### Form 2: Thinking Map

Use when themes form a clear hierarchy.

Structure:
- center node: review topic;
- first-level branches: 3-5 themes;
- second-level branches: submethods or subtopics;
- leaf labels: representative paper markers.

Constraints:
- normally no more than 15 nodes;
- labels should be short;
- no arrows unless direction is meaningful;
- cite paper markers near leaf nodes.

Use Step 5.5 if the map is complex.

### Form 3: Evolution Timeline

Use when methods, theories, or tools evolve over time.

Structure:
- horizontal time axis from early to recent;
- year or period ticks;
- 1-3 representative nodes per period;
- arrows showing replacement, derivation, challenge, or complementarity.

Use restrained color progression from early neutral to recent emphasis. Do not make the timeline decorative only.

### Selection Rule

| Review pattern | Recommended form |
|---|---|
| Few themes, many papers per theme | Theme matrix |
| 3-6 themes with clear hierarchy | Thinking map |
| Strong chronological method evolution | Evolution timeline |
| Method, task, and dataset dimensions all matter | Theme matrix plus smaller framework pages |

When uncertain, use the theme matrix.

## Theme Detail Pages

Each theme usually gets 1-2 pages:

Method lineage page:
- `content_type: matrix_framework`;
- left column: method class;
- middle column: representative models / algorithms;
- right column: assumptions, strengths, weaknesses.

Representative evidence page:
- `content_type: results_chart` or `table_compare`;
- one source figure plus interpretation rail, or an editable table comparing 3-5 papers;
- cite all representative papers.

## Controversy Page

This page is often the highest-value review slide.

Acceptable forms:
- two-column comparison of mainstream view versus alternative explanation;
- relation graph where nodes are themes and edges are dependency, contradiction, or complementarity;
- timeline showing how a debate changed.

State the controversy directly. Avoid vague phrases such as "there are different opinions" without explaining what differs.

## Research Gap Page

List 3-5 gaps. Each gap should include:
- one sentence naming the gap;
- current limitation;
- why it matters;
- possible direction.

Avoid generic statements such as "more research is needed." Make gaps specific to method, data, scenario, theory, evaluation, or transferability.

## Formula Page Rules

Use formula pages only when formulas are part of the research lineage:
- objective functions differ across methods;
- evaluation metrics evolve across papers;
- definitions or estimators are the review object.

Use `formula_step` for common pipelines:
- problem definition;
- general objective;
- common solution;
- output metric.

Use `formula_paragraph` when comparing branches, time periods, or theme clusters.

Do not copy formulas from every paper. Abstract shared structure and explain key differences.

## Citation Strategy

Route D has the highest citation density.

High-density pages:
- concept matrix cells use markers only;
- footer may only say that full entries are on the reference page;
- full list appears in `references_page`.

Medium-density pages:
- body markers plus footer entries for up to three or four sources;
- if more are needed, show representative entries and point to the reference page.

Low-density pages:
- one or two markers with full footer entries.

The reference page is required:
- list entries in citation-number order;
- keep numbering consistent across pages;
- allow multiple pages;
- omit bottom banner if it crowds the list.

## Speaker Notes Focus

- Background: explain why the review is timely.
- Search method: mention databases, keywords, and selected count when available.
- Conceptual framework: spend extra time on this page; explain whole map, then themes, then relations.
- Theme detail: locate each theme in the framework before evidence.
- Controversy: name competing views clearly.
- Gaps: explain why each gap deserves future work.
- Limitations: discuss review limitations such as language, time window, and database coverage.

## Page Brief Fields

Every Route D page should include:

```yaml
content_type: conceptual_framework
page_rhythm: dense
visual_requirement: chart
citations: ["[1]", "[3]", "[5]"]
reference_density: high
bottom_banner_text: "One synthesis claim."
```

For high-density reference pages, set:

```yaml
reference_strategy: full_list_on_reference_page
footer_behavior: marker_only
```

## Closing Page Rule

The summary / conclusion page and the final thank-you / Q&A page must be separate slides. Do not combine 总结, Summary, or conclusion bullets with 谢谢大家, Thank you, acknowledgements, or Q&A prompts on one slide.

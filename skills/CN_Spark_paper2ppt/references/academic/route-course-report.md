# Route B Course Report
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 4 判断为课程报告、政策报告或案例分析时读取；它组织背景、问题、分析、建议和课堂汇报型结论。

Use this route for undergraduate or graduate course presentations, policy analysis, case analysis, issue briefings, and thematic academic reports not centered on one specific paper.

## Selection Signals

Choose Route B when:
- the input is a course assignment, research report, policy review, case analysis, or thematic material;
- the user wants academic rigor plus policy, news, case, or statistical visuals;
- grading likely emphasizes logic, coverage, source quality, and visualization clarity rather than one empirical hypothesis.

If one paper dominates the content, use Route A. If the goal is multi-paper synthesis, use Route D.

## Narrative Skeleton

Default axis:

```text
background -> problem -> analysis framework -> evidence / data -> case or comparison -> synthesis -> recommendation / reflection
```

Variants:
- Policy interpretation: policy background, policy content, affected stakeholders, evidence, evaluation, suggestions.
- Case analysis: industry or event background, case choice, phenomenon and data, cross-case comparison, implications.
- Thematic issue report: origin of the issue, current status, view comparison, evidence and data, position.

## Default Page Structure

```text
P01 Cover: title, course, class, student, instructor, date
P02 Agenda
P03 Topic Background: current event, policy context, or issue origin
P04 Why The Issue Matters: data cards or concise evidence
P05 Core Question And Scope
P06 Key Concepts / Policy Text / Analytical Dimensions
P07 Current Status / Statistics: policy_stat_cards or chart
P08 Analysis Perspective 1
P09 Analysis Perspective 2
P10 Analysis Perspective 3
P11 Case / Event / Example
P12 Cross-Perspective Comparison
P13 Position / Recommendation / Reflection
P14 Limitations And Extension
P15 References
```

Typical length: 12-18 slides. Shorter class talks may merge perspectives; longer policy reports may add data and case pages.

## Required Pages

- Topic scope page.
- Core question page.
- Source / evidence base page.
- Framework or concept page.
- At least two analysis pages.
- Synthesis or recommendation page.
- References page when many source types are used.
- Separate final thank-you / Q&A page.

## Image And Policy Visual Handling

If the user provides images:
- use them as source assets;
- add a caption and source marker;
- preserve aspect ratio;
- do not crop away key context.

If the user only provides keywords:
- prefer official or citeable images;
- otherwise use a placeholder plan and tell the user what image should be added;
- avoid unauthorized random web images.

For statistics:
- use charts or `policy_stat_cards`;
- every number needs a source;
- explain what the number means, not only what it is.

For policy text:
- place excerpt in a light panel with an accent bar;
- keep excerpt short;
- cite the policy document.

## Layout Specialization

| Page type | Layout |
|---|---|
| Background | Image or event context plus short text |
| Statistics | 2-4 data cards or one chart |
| Policy text | Light quotation panel with source marker |
| Comparison | Native SVG table |
| Case | Image / timeline first, analysis second |
| Recommendation | 3-4 claim cards or open conclusion layout |

## Formula Page Rules

Route B is usually not formula-heavy. Use formula pages only when the report includes:
- evaluation metrics;
- index construction;
- scoring model;
- policy effect measurement;
- statistical test;
- simple economic or public-policy model.

Default `formula_step`:
- metric definition;
- calculation;
- interpretation;
- how it answers the report question.

Use `formula_paragraph` when formulas need institutional context, variable definitions, or policy-specific assumptions.

## Citation Rules

Route B often mixes source types:
- academic papers;
- policy documents;
- news reports;
- government statistics;
- websites;
- image sources.

Use GB/T 7714 entries with correct type markers such as `[J]`, `[Z]`, `[N]`, `[R]`, `[EB/OL]`, and `[DS/OL]`. Every policy quote, statistic, and news image must be traceable.

## Speaker Notes Focus

- Background: orient the audience with a concrete event or scenario.
- Data cards: explain what each number implies.
- Case pages: tell the timeline or story first, then analyze.
- Position pages: state the view clearly when the assignment allows it.
- Recommendations: connect each suggestion to evidence.

## Page Brief Fields

Every Route B page should include:

```yaml
content_type: policy_stat_cards
page_rhythm: dense
visual_requirement: chart
citations: ["[2]", "[4]"]
bottom_banner_text: "One evidence-based claim."
source_type: policy_report
```

Mark summary / implication pages as exempt only when they genuinely synthesize prior evidence.

## Closing Page Rule

The summary / conclusion page and the final thank-you / Q&A page must be separate slides. Do not combine 总结, Summary, or conclusion bullets with 谢谢大家, Thank you, acknowledgements, or Q&A prompts on one slide.

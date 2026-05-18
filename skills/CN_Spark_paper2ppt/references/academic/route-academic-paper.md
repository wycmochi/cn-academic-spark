# Route A Academic Paper
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 4 判断为单篇学术论文讲解时读取；它提供 question-to-evidence 的页面结构和学术论文汇报重点。

Use this route for one journal or conference paper. The deck explains the research question, importance, methods, evidence, interpretation, contribution, and limits of one paper.

## Selection Signals

Choose Route A when:
- the input is one paper with abstract, introduction, methods, results, and discussion;
- the user asks to present the paper in a group meeting, journal club, defense, seminar, or class;
- the target talk is usually 15-25 minutes;
- the expected deck size is usually 10-16 slides.

If the user provides several papers and wants synthesis, use Route D. If the material is a proposal, use Route C.

## Narrative Skeleton

First classify paper type using `paper-type-guidance.md`, then choose the route skeleton.

| Paper type | Narrative axis | Key order |
|---|---|---|
| Discovery / mechanism | question-to-evidence | phenomenon, unknown mechanism, hypothesis, design, evidence chain, model, limitations |
| Methods / AI / tool / algorithm | problem-to-solution | bottleneck, proposed method, architecture, evaluation, baseline comparison, ablation / robustness, boundary |
| Resource / dataset / atlas | workflow-to-validation | motivation, resource design, production workflow, QC, landscape, validation, reuse |
| Clinical / population / intervention | design-to-inference | problem, study design, cohort / endpoint, primary result, subgroup / sensitivity, bias / implication |
| Materials / chemistry / engineering | design-to-performance | target property, design principle, fabrication, characterization, performance, mechanism, stability / boundary |

Do not simply translate source section headings. Convert them into claim-based slide titles.

## Default Page Structure

For a 15-22 minute presentation, 12-14 slides is often enough. Exceed 16 slides only when the paper is complex.

```text
P01 Cover: title, authors, affiliation, journal / year, DOI
P02 Agenda: 4-6 module anchors
P03 Research Background: why the problem matters
P04 Current Gap: bottleneck, controversy, or unresolved mechanism
P05 Research Question: one central question or hypothesis
P06 Research Design / Technical Route: Step 5.5 if complex
P07 Method Framework / Model Architecture: matrix or architecture page
P08 Key Evidence 1: source figure plus interpretation rail
P09 Key Evidence 2: source figure, chart, table, or formula
P10 Key Evidence 3: validation, control, ablation, or sensitivity
P11 Mechanism / Integrated Interpretation
P12 Contribution And Reuse Value
P13 Limitations And Open Questions
P14 Summary And Outlook
P15 References: optional but recommended
P16 Thank You / Q&A
```

Adjust page count by paper type:
- method papers need more method / evaluation / ablation pages;
- mechanism papers need more evidence-chain pages;
- clinical papers need design, endpoints, primary result, subgroup, and bias pages;
- resource papers need QC, landscape, validation, and reuse pages.

## Required Page Types

Minimum Route A deck:
- source overview;
- background gap;
- central question or hypothesis;
- method / workflow / research design;
- at least two result evidence pages;
- interpretation / discussion;
- contribution and limitations;
- summary;
- references when footer capacity is insufficient.
- separate final thank-you / Q&A page.

Complex method routes, full-paper workflows, and framework diagrams should use SKILL.md Step 5.5:
- Version A: editable template SVG route page;
- Version B: AI reference route image page;
- two pages inserted consecutively.

## Evidence Page Layout

Every key evidence page should use this hierarchy:
1. Hero source figure / chart / formula / complex table screenshot.
2. Narrow interpretation rail with one conclusion and 2-3 notes.
3. Citation marker near the evidence object.
4. `citation_footer` above the bottom banner.
5. Bottom banner restating the page claim.

Do not place a dense source figure in a 1:1 split where labels become unreadable. Crop the relevant subpanel when necessary, but preserve axes, scale bars, labels, and captions needed for interpretation.

## Figure Selection

Select figures for argument value, not completeness.

Priority:
1. research design or workflow;
2. main result or mechanism figure;
3. validation / control / ablation;
4. model architecture or mechanism diagram;
5. application or implication visual.

A 12-14 slide paper deck usually needs 4-8 strong visuals. More figures often make every figure too small.

## Formula Page Rules

Only expand formulas when they are necessary:
- without the formula, the audience cannot follow the method;
- the formula carries the paper's methodological contribution;
- later result pages refer back to an objective function, update rule, metric, or decision criterion.

Use `references/academic/formula-rendering.md` and `scripts/latex_formula_to_png.py --block-json` for complex formulas. The formula role, complete equation, and variable definitions must be rendered together as one PNG image.

Default `formula_step` order:
1. variable definition;
2. core computation;
3. objective / constraint;
4. inference output.

Use `formula_paragraph` only when formulas belong to separate sections, such as encoding, alignment, decoding, training, and inference.

Do not copy every notation from the paper. Move supplementary derivations to backup pages or omit them.

## Citation Rules

- The paper's DOI, venue, and year should appear on the cover.
- Pages using the paper's own figures or data cite the paper.
- Works cited inside the paper are included only when the PPT repeats those external claims.
- A full reference page is optional but recommended for defense or formal seminar settings.

Use `citation-style.md` for GB/T 7714 formatting and mixed-font SVG segmentation.

## Speaker Notes Focus

- Cover: introduce the paper and state its biggest novelty in one sentence.
- Background: explain why the problem matters to the audience.
- Method: explain intuition before symbols.
- Results: state the conclusion before figure details.
- Statistics: give intuitive interpretation, not only values.
- Limitations: be honest and specific.
- Summary: connect the contribution to the audience's research direction.

## Page Brief Fields

Every Route A page in `design_spec.md` section IX should include:

```yaml
content_type: results_chart
page_rhythm: dense
visual_requirement: source_figure
citation_footer: ["[1]"]
bottom_banner_text: "One sentence claim."
speaker_note_goal: "Explain the evidence and transition to the next claim."
```

For TechnicalRoute pages, include route job id, Version A / B paths, and consecutive PPT page ids.

## Closing Page Rule

The summary / conclusion page and the final thank-you / Q&A page must be separate slides. Do not combine 总结, Summary, or conclusion bullets with 谢谢大家, Thank you, acknowledgements, or Q&A prompts on one slide.

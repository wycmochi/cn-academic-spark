# Route C Proposal
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 4 判断为开题报告、研究计划或 proposal defense 时读取；它规定研究问题、技术路线、可行性、计划进度和预期成果页面。

Use this route for thesis proposal defense, opening report, undergraduate capstone proposal, grant-style academic proposal, or research plan.

## Selection Signals

Choose Route C when:
- the input is a proposal, opening report, research plan, or grant application;
- it contains research objectives, planned methods, schedule, feasibility, or expected results;
- reviewers care about value, feasibility, technical route, timeline, expected contribution, and risk control.

Route C must distinguish existing evidence from planned work.

## Narrative Skeleton

Use a problem-to-plan axis:

```text
problem and value -> research status -> gap -> objectives and content -> technical route -> research framework -> key questions -> methods -> schedule -> expected contribution -> feasibility and risk
```

## Default Page Structure

```text
P01 Cover: title, student, advisor, discipline, institution, defense date
P02 Agenda
P03 Research Background And Significance
P04 Research Status: foreign / domestic or stream-based
P05 Research Gap / Problem To Solve
P06 Research Objectives
P07 Research Content: 3-5 work packages
P08 Key Scientific Questions
P09 Technical Route: Step 5.5 required if complex
P10 Research Framework: variables, modules, outputs
P11 Main Method / Model: include formulas if needed
P12 Data Source / Experiment Design
P13 Research Schedule: Gantt chart
P14 Expected Results
P15 Innovation Points: no more than three
P16 Feasibility And Risk Plan
P17 References
P18 Acknowledgement / Q&A
```

Typical length: 14-18 slides.

## Required Pages

Route C should include:
- research background;
- research status;
- gap / problem;
- objectives;
- research content;
- TechnicalRoute page pair if route is complex;
- research framework page when variables or modules are numerous;
- method / model page;
- data or experiment design page;
- Gantt chart page;
- expected contribution page;
- feasibility and risk page;
- reference page.
- standalone summary page before the final thank-you / Q&A page.

## TechnicalRoute Placement

Use SKILL.md Step 5.5 when the proposal includes:
- multi-stage data collection and analysis;
- experiment plus model plus validation;
- multiple variables, constructs, or modules;
- difficult-to-explain research content;
- a route that reviewers must understand quickly.

The route pages must be consecutive:
- `<module_number> Research Route: Editable Template Version`
- `<module_number> Research Route: AI Reference Version`

The editable template version is the authoritative version for PPT editing. The AI version is a reference option for visual comparison.

## Gantt Chart Rules

Use `content_type: gantt`.

Preferred implementation:
- use `templates/charts/gantt_chart.svg`;
- make tasks editable where possible;
- show task name, start period, duration, and milestone;
- use restrained blue tones for normal tasks;
- use a small warning or accent color for writing, review, or defense milestones only when useful.

A full-page Gantt may omit bottom banner to avoid covering the timeline. Keep title, date scale, and milestone labels readable.

Suggested task types:
- literature review;
- data collection and cleaning;
- method design and prototype;
- experiment and comparison;
- paper writing and submission;
- midterm check;
- pre-defense;
- final defense.

## Formula Page Rules

Proposal formulas should help reviewers understand:
- variable definitions;
- model objective;
- estimation strategy;
- metric construction;
- robustness logic.

Use `formula_step` by default:
- step title;
- rendered formula PNG;
- result expression if needed;
- one explanation sentence.

Use `formula_paragraph` when formulas belong to different sections, such as variable definition, objective function, estimation strategy, and robustness handling.

Formula order must match the technical route and research design. Do not create a Word-like page with formulas scattered in paragraphs.

## Innovation Page Rules

Innovation points:
- no more than three;
- classify when possible: theoretical, methodological, application, data, or system contribution;
- each point must be specific and testable;
- avoid vague claims such as "important theoretical and practical value."

## Feasibility And Risk Rules

Feasibility should cite or state concrete support:
- available dataset;
- equipment or platform;
- pilot result;
- collaborator or field access;
- prior code / method basis;
- schedule buffer.

Risk plan should name:
- risk;
- trigger condition;
- fallback method;
- impact on schedule.

## Citation Rules

Route C has high citation requirements:
- research status pages need markers for major claims;
- reference page is required;
- sources must be verifiable;
- do not accept vague sources such as "found online" or "senior student said."

Use GB/T 7714 numbering. Keep reference page numbering aligned with body markers.

## Speaker Notes Focus

- Background: state the research value in one sentence.
- Research status: progress from existing work to gap.
- TechnicalRoute: speak along nodes and identify where innovation appears.
- Gantt: speak by milestone, not month by month.
- Innovation: be concrete and limited.
- Feasibility: state what has already been secured.
- Risk: show control, not uncertainty avoidance.

## Page Brief Fields

Every Route C page should include:

```yaml
content_type: gantt
page_rhythm: dense
visual_requirement: chart
citations: ["[5]"]
planned_vs_completed: planned
bottom_banner_text: "One proposal-specific claim."
```

For planned pages, mark whether the content is `completed_basis`, `planned_method`, `expected_result`, or `risk_control`.

## Closing Page Rule

The summary / conclusion page and the final thank-you / Q&A page must be separate slides. Do not combine 总结, Summary, or conclusion bullets with 谢谢大家, Thank you, acknowledgements, or Q&A prompts on one slide.

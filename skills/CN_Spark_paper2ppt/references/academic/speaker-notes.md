# Academic Speaker Notes
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 6 写 notes/total.md 时读取；它规定中文学术汇报的口播稿结构、语气、页间衔接和 TTS 友好写法。

Write speaker notes to `<project_path>/notes/total.md`. The master file uses one structural section per slide so `scripts/total_md_split.py` can split it into per-slide files. `scripts/notes_to_docx.py` then exports a standalone continuous DOCX manuscript: slide headings and filenames are not printed by default, and each emitted spoken paragraph is prefixed with `第 N 页：` before being appended in deck order. `scripts/svg_to_pptx.py` strips PPTX notes package parts; use the DOCX for all speaker notes.

## Output Format

Each slide section:

```markdown
# 07_model_results
<spoken note body>

---
```

The heading should match the SVG filename stem when possible. The heading is structural and should not be read by TTS.

## General Rules

- Write natural spoken academic prose.
- Use 100-180 Chinese characters or equivalent per ordinary slide.
- Allow up to about 250 Chinese characters or equivalent for core TechnicalRoute, Gantt, or conceptual framework pages.
- Use 2-5 sentences per slide.
- Do not copy slide text verbatim.
- Add background, intuition, evidence interpretation, and transition.
- End most slides with one transition sentence.
- Do not include bracketed stage directions, timing labels, `Key points:`, or checklist labels.

Recommended structure:

```text
One sentence stating the slide claim.
Two or three sentences explaining evidence, method, figure, formula, or context.
One sentence transitioning to the next slide.
```

## Academic Tone

Use formal but natural oral academic style:
- clear declarative sentences;
- limited first-person phrasing when useful;
- no empty praise;
- no marketing language;
- no exaggerated certainty beyond the source evidence;
- preserve uncertainty and limitations.

## Terminology And Mixed Language

For first occurrence of an English technical term:
- give the Chinese explanation in final Chinese notes;
- keep the English term if it is standard in the field.

Do not stack abbreviations. Define acronyms the first time.

For math:
- explain variable roles and intuition;
- do not mechanically read every symbol;
- convert awkward notation into spoken explanation.

For statistics:
- explain what the value means in context;
- do not only read the number.

## Figure, Formula, And Table Speech

For source figures:
1. Tell the audience where to look first.
2. State the visual pattern.
3. Interpret the pattern.
4. Link it to the slide title claim.

For formulas:
1. State what the formula calculates or optimizes.
2. Explain the most important variables.
3. Explain why this formula matters for the method.
4. Avoid reading every operator.

For complex tables:
1. Explain row and column meaning.
2. Identify one or two key comparisons.
3. State the takeaway.

## Route A Notes

Academic paper presentation:
- Cover: introduce the paper and state its main novelty in one sentence.
- Background: explain why the problem matters; do not read the abstract.
- Method: explain intuition before symbols.
- Results: state the conclusion before figure details.
- Limitations: be honest and specific.
- Summary: connect the contribution to the audience's research interest.

## Route B Notes

Course report / policy / case analysis:
- Background: use a concrete event, policy, or scenario to orient the audience.
- Data cards: explain what each number means.
- Case pages: tell the event or timeline before the analysis.
- Opinion pages: state the position clearly when the assignment allows it.
- Recommendations: tie suggestions back to evidence, not slogans.

## Route C Notes

Proposal / research plan:
- Background: state the research value in one sentence.
- Research status: organize by foreign / domestic work or by research streams, then identify the gap.
- TechnicalRoute: speak along the nodes and point out where the innovation appears.
- Gantt: speak by milestones, not month by month.
- Innovation: classify as theoretical, methodological, or application contribution when appropriate.
- Feasibility: state what data, equipment, collaborators, or pilot results are already available.
- Avoid weak phrases such as "if time permits" unless they are framed as a managed risk.

## Route D Notes

Literature review:
- Background: explain why this review is timely.
- Search method: state databases, keywords, inclusion logic, and final corpus when available.
- Conceptual framework: spend more time here; first explain the whole map, then each theme, then cross-theme relations.
- Theme detail: locate the theme in the framework before presenting evidence.
- Controversy: name the competing explanations clearly.
- Research gaps: explain why each gap is worth addressing.
- Review limitations: mention language, time span, database coverage, or selection bias where relevant.

## Transition Templates

Use transitions such as:
- "With that background in place, the next question is..."
- "This leads directly to the method design."
- "The same logic appears in the second evidence group."
- "In contrast, the next result shows a boundary condition."
- "Putting these findings together, the main implication is..."
- "For a review deck, this opens the next theme."

Avoid hard cuts such as "This is the background. Next is method."

## Citation Speech

When mentioning another work aloud:
- use author plus year or a short source name;
- do not read the full GB/T 7714 entry;
- keep tone neutral unless the slide is explicitly about controversy.

Example:
- Say "Smith 2024 reports a similar pattern" rather than reading the full journal entry.

## TTS-Friendly Rules

- Avoid long nested clauses.
- Avoid unexplained symbols.
- Avoid Markdown tables in notes.
- Avoid citation lists in spoken text.
- Write numbers in a way that TTS can pronounce clearly.
- Split overly long review-framework notes into short paragraphs.

## Self-Check

- [ ] Every slide has notes.
- [ ] Notes explain the slide rather than repeat it.
- [ ] Formula and chart pages include intuition.
- [ ] TechnicalRoute pages explain the route order.
- [ ] Route D concept-framework notes are detailed enough.
- [ ] Notes do not contain headings or labels that TTS would read awkwardly.

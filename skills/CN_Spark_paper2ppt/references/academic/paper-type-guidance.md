# Paper Type Guidance
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 4 被 Strategist 读取；它先判断论文类型，再决定叙事结构、章节组织和带数字模块的页面标题格式。

## Read Timing In Step 4

Read this file **after** the deck route has been selected:
- Route A: single academic paper.
- Route B: course report / policy report / case analysis.
- Route C: proposal / research plan / opening defense.
- Route D: literature review / review synthesis.

Then classify the source by paper type before writing the final module structure, page roster, or slide titles. This file internalizes the Paper-Type Guidance logic locally; do not read external skill paths at runtime.

## 1. Classify The Paper First

Use the title, abstract, section headings, figures, and stated contribution to classify the source before writing the outline.

| Paper type | Signals | Default narrative |
|---|---|---|
| Discovery / mechanism | New phenomenon, mechanism, causal explanation, experimental evidence. | question-to-evidence |
| Methods / AI / tool / algorithm | Model, pipeline, software, benchmarked method, ablation. | problem-to-solution |
| Resource / dataset / atlas / omics / benchmark | Dataset, atlas, cohort, catalog, public resource, validation. | workflow-to-validation |
| Clinical / population / intervention | Study design, population, exposure, outcome, inference. | design-to-inference |
| Materials / chemistry / physics / engineering | Synthesis, structure, property, performance, mechanism. | property-to-mechanism or design-to-performance |
| Review / perspective | Evidence map, conceptual synthesis, future directions. | evidence-map |

If a paper spans multiple types, pick one dominant narrative and use the secondary type only for individual slides. Example: a method paper with a clinical case study remains `Methods / AI / tool / algorithm`; the clinical evidence appears in evaluation and implication slides.

## 2. Paper-Type Narrative Frameworks

### Discovery / Mechanism Papers

Use a question-to-evidence arc:
1. Phenomenon and importance.
2. Unknown mechanism or unresolved causal link.
3. Hypothesis or research question.
4. Experimental design and key measurements.
5. Evidence chain, ordered from observation to mechanism.
6. Integrated model or mechanism diagram.
7. Limitations and next experiments.

Recommended modules:
- `1 Research Background`
- `2 Scientific Question`
- `3 Experimental Design`
- `4 Evidence Chain`
- `5 Mechanism Model`
- `6 Limitations And Outlook`

Title examples:
- `2 Scientific Question: The Causal Link Remains Unresolved`
- `4 Evidence Chain: Multi-Level Experiments Support The Proposed Mechanism`
- `5 Mechanism Model: Integrated Pathway Explains The Observed Phenotype`

### Methods / AI / Tool / Algorithm Papers

Use a problem-to-solution arc:
1. Current bottleneck.
2. Proposed method or system.
3. Workflow, architecture, or pipeline.
4. Evaluation design, datasets, and baselines.
5. Performance compared with baselines.
6. Ablation, robustness, uncertainty, or failure cases.
7. Reuse scenarios and limitations.

Recommended modules:
- `1 Problem Definition`
- `2 Method Framework`
- `3 Technical Route`
- `4 Model Results`
- `5 Robustness And Ablation`
- `6 Reuse And Limitations`

Title examples:
- `1 Problem Definition: Existing Metrics Miss Dynamic Exposure`
- `2 Method Framework: Multi-Source Features Drive Predictive Modeling`
- `4 Model Results: Variable Importance Ranking`
- `4 Model Results: Network Structure ALE Analysis`
- `5 Robustness And Ablation: Sensitivity Tests Confirm Stable Performance`

### Resource / Dataset / Atlas / Omics / Benchmark Papers

Use a workflow-to-validation arc:
1. Why the resource is needed.
2. Dataset, cohort, sample, or benchmark design.
3. Generation and quality-control workflow.
4. Main landscape, atlas, catalog, or benchmark map.
5. Validation and reproducibility.
6. Example biological, clinical, or technical insights.
7. Access, reuse, and boundaries.

Recommended modules:
- `1 Resource Motivation`
- `2 Data Construction`
- `3 Quality Control`
- `4 Resource Landscape`
- `5 Validation Evidence`
- `6 Reuse Boundary`

Title examples:
- `2 Data Construction: Multi-Cohort Sampling Builds The Resource Base`
- `3 Quality Control: Batch Effects Are Reduced Across Platforms`
- `4 Resource Landscape: Atlas View Reveals Major Structural Patterns`

### Clinical / Population / Intervention Studies

Use a design-to-inference arc:
1. Clinical or public-health problem.
2. Study question.
3. Cohort, trial, sampling, or observational design.
4. Endpoints, exposures, variables, and confounders.
5. Primary result.
6. Subgroup, sensitivity, secondary, or mediation analyses.
7. Bias, limitations, practical implication.

Recommended modules:
- `1 Clinical Problem`
- `2 Study Design`
- `3 Variables And Endpoints`
- `4 Primary Results`
- `5 Sensitivity Analysis`
- `6 Practical Implications`

Title examples:
- `2 Study Design: Cohort Construction Supports Causal Interpretation`
- `4 Primary Results: Exposure Shows A Stable Association With Outcome`
- `5 Sensitivity Analysis: Subgroup Patterns Clarify Boundary Conditions`

### Materials / Chemistry / Physics / Engineering Papers

Use a property-to-mechanism or design-to-performance arc:
1. Target property or technical challenge.
2. Design principle.
3. Synthesis, fabrication, computational setup, or experimental platform.
4. Characterization.
5. Performance evidence.
6. Mechanism or structure-property relationship.
7. Scalability, stability, manufacturability, or application boundary.

Recommended modules:
- `1 Technical Challenge`
- `2 Design Principle`
- `3 Fabrication And Characterization`
- `4 Performance Results`
- `5 Mechanism Analysis`
- `6 Application Boundary`

Title examples:
- `2 Design Principle: Interface Engineering Improves Charge Transport`
- `4 Performance Results: Device Efficiency Exceeds Baseline Materials`
- `5 Mechanism Analysis: Structure-Property Coupling Explains Stability`

### Reviews And Perspectives

Use an evidence-map arc:
1. Why the topic matters now.
2. Conceptual framework.
3. Theme 1.
4. Theme 2.
5. Theme 3.
6. Controversy or unresolved problem.
7. Author synthesis.
8. Future directions.

Recommended modules:
- `1 Topic Rationale`
- `2 Conceptual Framework`
- `3 Evidence Map`
- `4 Controversies`
- `5 Synthesis`
- `6 Future Directions`

Title examples:
- `2 Conceptual Framework: Three Dimensions Organize The Literature`
- `3 Evidence Map: Existing Studies Cluster Around Mechanism And Application`
- `4 Controversies: Measurement Choices Drive Divergent Conclusions`

## 3. Map Type To Deck Modules

Use 4-6 major modules. Choose modules from background gap, research question, data / design, methods, results, mechanism, validation, limitations, implications, and conclusion according to paper type.

Rules:
- Keep the module sequence aligned with the chosen narrative arc.
- Put technical-route pages inside the module where the method, research design, or conceptual framework is introduced.
- Do not copy source section headings directly when they are vague, such as `Results`, `Discussion`, or `Experiment 1`; convert them into evidence-based slide claims.
- For Route D reviews, treat `Theme 1 / Theme 2 / Theme 3` as customizable evidence clusters, not literal titles.

## 4. Slide Title Rule

For body content pages, use `<module_number> <module_title>: <slide_subtitle_or_evidence_conclusion>`.

Rules:
- Use Arabic numerals.
- Keep the same module number inside one module.
- Put a colon between the module title and the slide subtitle.
- Write a claim, evidence conclusion, method function, or framework role after the colon.
- Keep Chinese output natural for oral academic reporting; preserve English technical terms when translation reduces precision.
- Cover, agenda, section dividers, acknowledgements, and reference pages may omit this rule.
- Summary pages may use `Summary: ...` when they synthesize the whole deck, but body slides must keep the numbered module format.

Examples:
- `1 Research Question: Static Exposure Metrics Miss Daily Mobility`
- `2 Data And Methods: Multi-Source Mobility Records Build Dynamic Exposure`
- `4 Model Results: Variable Importance Ranking`
- `4 Model Results: Network ALE Structure Analysis`

## 5. Chinese Academic Writing Style

Use language suitable for spoken academic reporting:
- Avoid rigid translation from English section titles.
- Avoid long paragraphs and overpacked nominal phrases.
- Prefer evidence-based interpretation over vague praise.
- Use concise but precise phrases; one slide title should fit one line whenever possible.
- Use formula, figure, or table evidence in the body when it is the natural proof for the title claim.

## 6. Route-Specific Notes

Route A single paper:
- Preserve the article's core contribution and evidence order.
- Give result modules enough pages for figures, formulas, and complex tables.

Route B course report / policy report / case analysis:
- Use the paper-type arc only when the source is actually a research paper; otherwise adapt it to problem, analysis, evidence, implication, and recommendation.

Route C proposal / research plan:
- Use the closest paper-type arc as the target research logic, but convert result pages into planned data, planned method, expected result, feasibility, and risk-control pages.

Route D literature review:
- Use review / perspective by default unless the review is explicitly organized around a method benchmark, resource atlas, or clinical evidence map.

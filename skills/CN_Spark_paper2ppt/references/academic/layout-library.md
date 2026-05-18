# Academic Layout Library
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 4 和 Step 6 被读取；它把学术页面的 content_type 映射到具体版式、图文比例和底部横幅要求。

This file maps `content_type` in `design_spec.md` section IX to academic slide layout logic. The actual rendering path is SVG to DrawingML. Use selected layout SVGs, chart templates, and `spec_lock.md` fields first; this file defines the academic intent and constraints behind each layout.

## Global Academic Layout Constants

Default visual character:
- restrained academic style;
- white or very light background;
- readable dark text;
- one main evidence object per content page whenever possible;
- citation footer above bottom banner;
- small corner radius, normally `rx=6` on a 1280 x 720 canvas.

Default zones:
- header / title zone;
- content evidence zone;
- citation footer zone;
- bottom banner zone;
- page number / logo zone.

Do not let body content collide with the citation footer, bottom banner, page number, or logo.

## Common Elements

Most evidence and argument pages include:
1. Page title following the numbered module title rule.
2. Main evidence object: source figure, chart, formula PNG, complex table screenshot, or route diagram.
3. Short interpretation text.
4. Citation footer when cited material appears.
5. Bottom banner with one claim-like sentence.

Exceptions:
- cover;
- agenda;
- section divider;
- acknowledgements;
- references page;
- full-page Gantt when the timeline needs the whole canvas;
- TechnicalRoute pages already occupied by route visuals.

## Content Type Map

| `content_type` | Use for | Preferred layout |
|---|---|---|
| `cover` | Title page | Template cover, no citation footer unless required by source paper metadata |
| `toc` | Agenda | 4-6 module anchors, minimal visuals |
| `text_flow` | Background, problem framing, discussion | Text-led layout with one supporting visual or deliberate whitespace |
| `bullet_analysis` | Four to six analytical points, or 2-3 grouped evidence blocks | Compact multi-column bullets with figure, table, card, or small chart support |
| `pipeline` | Simple process | Full-width process; complex routes use Step 5.5 TechnicalRoute pair |
| `matrix_framework` | Variables, dimensions, method modules | Three-column or input-process-output framework |
| `results_chart` | Experimental, empirical, or model results | Hero figure / chart plus narrow interpretation rail |
| `table_compare` | Comparison across methods, policies, cases, or studies | Native SVG table; screenshot only for source tables that must preserve formatting |
| `formula_step` | Stepwise derivation or model explanation | Modular formula panels with rendered formula PNGs |
| `formula_paragraph` | Many formulas plus explanation | Sectioned formula groups with concise prose |
| `gantt` | Proposal schedule | Use `templates/charts/gantt_chart.svg` or equivalent editable chart; full-page layout allowed |
| `policy_stat_cards` | Route B data cards | 2-4 cards with big numbers, labels, and sources |
| `conceptual_framework` | Route D synthesis | Matrix, thinking map, or evolution timeline |
| `theme_detail` | Route D theme page | Method lineage, representative evidence, or table comparison |
| `evidence_matrix` | Literature comparison | Native SVG table; markers in cells, references resolved elsewhere |
| `references_page` | Bibliography | Dense numbered list, often two columns |
| `conclusion` | Summary, outlook, implication | Open layout with 3-4 claims and more whitespace |

## Layout Selection Rules

Choose layout by evidence role, not by habit:

```text
One dense source figure?          -> results_chart
Two or more figures to compare?   -> grid or top-bottom comparison
Research route or workflow?       -> pipeline or TechnicalRoute Step 5.5
Three dimensions / variables?     -> matrix_framework
Numeric comparison?               -> table_compare or chart template
Review synthesis?                 -> conceptual_framework or evidence_matrix
Formula drives the method?        -> formula_step or formula_paragraph
Proposal schedule?                -> gantt
Only summary / implication?       -> conclusion
```

Do not turn every page into a 1:1 left-right split. Let the layout follow the slide's argumentative role.

## Evidence Page Rule

For `results_chart`:
- the main figure or chart should occupy 65-80% of the content area;
- interpretation rail should be narrow and concise;
- one conclusion sentence plus 2-3 supporting notes is enough;
- cite the figure source;
- do not shrink a dense paper figure into a small side panel.

If the original figure is too dense:
- crop the relevant subpanel;
- preserve labels and scale bars;
- cite the original full figure;
- do not blur or over-compress.

## Table Rules

For editable tables:
- use native SVG table geometry;
- use a strong header row;
- use zebra rows when it improves scanning;
- align numeric columns consistently;
- keep row height stable;
- cite data source below or in footer.

For complex source table screenshots:
- use `crop: meet`;
- keep row / column labels visible;
- add source caption and citation marker;
- use screenshot only when redrawing would risk data errors.

## Pipeline And TechnicalRoute Rules

Simple process pages:
- 3-5 steps can be hand-drawn as editable SVG;
- one direction unless feedback is source-grounded;
- concise labels;
- no decorative branching.

Complex research routes:
- use SKILL.md Step 5.5;
- generate Version A editable template SVG and Version B AI reference image;
- insert as consecutive pages;
- mark both as TechnicalRoute pages.

## Formula Layout Rules

Formula explanation blocks are rendered as transparent PNGs using:

```bash
python3 scripts/latex_formula_to_png.py --block-json <project_path>/notes/formula_01.json --out <project_path>/images/formulas/formula_block_01.png --font-size 30 --dpi 260 --color "#111111"
```

Read `formula-rendering.md` for the mandatory rendering and QA contract. Before drawing formula pages, inspect `templates/formula/formula_templates_index.json`; use `formula_explanation_block` for the common pattern shown by the user's examples. The final visual object is one PNG containing formula role, formula, `???`, and variable definitions.

`formula_step`:
- 1-5 formula block PNG modules per slide;
- each module is inserted as one image with `data-formula-block-png="true"`;
- adjacent modules are separated by `stroke="#A6A6A6"`, `stroke-width="1.5"`, `stroke-dasharray="8 6"` dashed lines tagged `data-formula-separator="true"`;
- formula PNGs, explanation text, and separator lines must never overlap or stack;
- use for algorithms, model steps, metric construction, and estimation procedures.

`formula_paragraph`:
- 2-3 sectioned formula block PNGs if formulas belong to distinct conceptual sections;
- split across multiple slides when there are more than five formula blocks or when readability would drop.

Do not scatter formula title, formula, and interpretation into separate SVG text boxes. Separate formula blocks with gray 1.5pt dashed lines. Formula order must match the method route or research design.

## Route D Conceptual Framework Options

`conceptual_framework` should use one of three forms:

| Form | Use when | Constraints |
|---|---|---|
| Theme matrix | Many papers per theme, dense reference comparison | Full-width table; reference cells use markers only |
| Thinking map | 3-6 themes with clear hierarchy | Center topic, 3-5 first-level branches, node count normally <=15 |
| Evolution timeline | Methods or ideas evolve over time | Horizontal time axis, dated stages, relations between generations |

When in doubt, use the theme matrix. It is the most academic and easiest to audit.

## Route B Policy / Case Layouts

`policy_stat_cards`:
- 2-4 cards per row;
- big numeric value;
- short label;
- source note;
- avoid unsupported decorative photos.

Policy quotation:
- light panel;
- vertical accent bar;
- source marker;
- no oversized quote decoration.

Case page:
- image or timeline first;
- narrative second;
- cite image and data source.

## Route C Gantt Rules

Use `gantt` for proposal schedules.

Preferred:
- editable chart template `templates/charts/gantt_chart.svg`;
- tasks with start and duration;
- milestones as diamond markers;
- restrained blue palette with one warning / writing-period accent if needed.

Full-page Gantt may omit bottom banner to avoid covering the timeline, but it still needs a title and source / assumption note when relevant.

## Reference Page Layout

Use `references_page` for Route C and Route D.

Rules:
- two columns allowed;
- 10 px or equivalent readable size;
- continue numbering across multiple pages;
- no bottom banner if it crowds the list;
- mixed-font runs remain required;
- keep page titles concise.

## Visual Coverage Rule

Except TechnicalRoute pages, summary pages, and planning / implication pages, every slide must contain at least one meaningful visual:
- source figure;
- complex table screenshot;
- chart;
- formula PNG;
- route diagram;
- dataset / map / model visual.

Decorative icons do not satisfy this requirement.

## Self-Check

- [ ] `content_type` is declared for every body page.
- [ ] Layout matches the page's evidence role.
- [ ] Non-exempt pages include a meaningful visual.
- [ ] Citation footer space is reserved when needed.
- [ ] Bottom banner does not overlap content.
- [ ] Dense source figures are cropped or enlarged enough to read.
- [ ] Formula pages use rendered formula block PNGs containing both formulas and explanations; max five per slide with gray 1.5pt dashed separators.
- [ ] Complex routes use TechnicalRoute dual pages.

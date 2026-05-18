# Template Resources

## Design Specification & Outline Reference

`design_spec_reference.md` is an all-in-one reference template for defining:
1.  **Visual Specifications**: Canvas dimensions, color scheme, typography, layout principles
2.  **Content Outline**: Slide-by-slide page structure planning
3.  **Technical Constraints**: Hard requirements for SVG generation and PPT compatibility

[View Design Spec Reference](./design_spec_reference.md)

## Page Layout Templates

The `layouts/` directory contains pre-built page layout templates organized by design style:

- **General**: Versatile modern style, clean and flexible
- **Consultant**: Consulting style, professional and structured
- **Consultant Top**: Top-tier consulting style (MBB-level)
- **Academic Defense**: Academic defense style, research-oriented

- **Human browsing**: [layouts/README.md](./layouts/README.md)
- **Slim lookup (discovery only)**: [layouts/layouts_index.json](./layouts/layouts_index.json) — used to answer "what templates exist?". Step 3 triggers on an explicit directory path supplied by the user, not on names from this index.

## Visualization Templates

The `charts/` directory contains 70 standardized visualization templates. For backward compatibility, the directory name remains `charts/`, but its scope includes charts, infographics, process diagrams, relationship diagrams, strategic frameworks, and system architecture diagrams:

- KPI Cards
- Bar Chart / Stacked Bar Chart
- Line Chart / Dual-Axis Line Chart
- Donut Chart
- Radar Chart
- Funnel Chart
- Matrix (2x2)
- Timeline
- Gantt Chart
- Process Flow
- Org Chart
- Layered Architecture / Module Composition / Hub with Described Spokes / Pipeline with Stages / Client-Server Flow

- **Library index (single source of truth)**: [charts/charts_index.json](./charts/charts_index.json)
- **Directory overview**: [charts/README.md](./charts/README.md)

## Icon Library

The `icons/` directory contains 11,600+ vector icons across five libraries:

| Library | Style | Count |
|---------|-------|-------|
| `chunk-filled` | fill / straight-line geometry | 640 |
| `tabler-filled` | fill / bezier-curve forms | 1000+ |
| `tabler-outline` | stroke / line | 5000+ |
| `phosphor-duotone` | duotone / single color + 0.2 opacity backplate | 1200+ |
| `simple-icons` | brand logos (company / product marks) | 3400+ |

- **Usage & style rules**: [icons/README.md](./icons/README.md)
- **Search icons**: `ls skills/CN_Spark_paper2ppt/templates/icons/<library>/ | grep <keyword>`

## Formula Templates

The `formula/` directory contains academic formula explanation block templates. These templates are layout shells only: complete equations must be rendered by `scripts/latex_formula_to_png.py` as transparent PNGs and inserted into the formula image slot.

- **Formula template index**: [formula/formula_templates_index.json](./formula/formula_templates_index.json)

## JSON-First Resource Selection

Before using any template asset in a generated PPT, read the relevant index first and record the selected key in `design_spec.md` / `spec_lock.md`:

| Resource | Required index before use | Downstream use |
|---|---|---|
| Layout deck templates | `layouts/layouts_index.json` | Step 3 template choice and project template copy |
| Charts / diagrams / framework blocks | `charts/charts_index.json` | Step 6 SVG page composition |
| TechnicalRoute templates and gallery refs | `technicalroute/templates/templates_index.json`, `technicalroute/Custom_gallery/*/trans-manifest.json` | Step 5.5 Version A/B route diagram generation |
| Formula block shells | `formula/formula_templates_index.json`, `formula/formula_block_schema.json` | Formula PNG rendering and placement |
| Icons | `icons/README.md` plus one selected library directory | `<use data-icon="library/name" .../>` placeholders expanded by finalization/export |

`resource_index.json` is the compact machine-readable map of these index-first rules.

# TechnicalRoute Color And Typography
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在 Step 5.5 写路线图 spec_lock 时读取；它让技术路线图继承整套 PPT 的颜色、字体、强调色和圆角规范。

TechnicalRoute pages must look like part of the same academic deck. They inherit the parent `design_spec.md` and `spec_lock.md`. If the user supplied a PPTX template and it has been registered, that template palette has the highest priority.

## Palette Priority

Use this order:
1. User-provided PPTX template palette and institution identity, when present.
2. Project `spec_lock.md` color roles.
3. Project `design_spec.md` color strategy.
4. TechnicalRoute fallback named palettes in this file.
5. Neutral academic blue if no other information exists.

Do not let Custom_gallery, literature references, or AI image defaults override the user PPTX template palette.

## Route Color Roles

Write resolved colors into route `spec_lock.md` with HEX values:

```yaml
colors:
  primary: "#1F4E79"
  secondary: "#2E7D32"
  accent: "#C00000"
  muted: "#888888"
  surface: "#F5F8FB"
  text: "#1A1A1A"
  brick_red: "#A23B2A"
```

Rules:
- Use a four-role semantic budget: primary, secondary, accent, muted.
- White and light surface tints are allowed as backgrounds.
- Accent area should normally stay below 5% of the diagram.
- Brick red `#A23B2A` is for concise high-priority text only, with bold weight.
- Do not recolor the whole diagram with brick red or accent red.
- Use muted gray for captions, transition labels, and weak annotations.

## Fallback Named Palettes

These are fallback choices only. Do not use them when project or user-template colors exist.

| Name | primary | secondary | accent | muted | Typical fit |
|---|---|---|---|---|---|
| `academic_blue_green` | `#1F4E79` | `#2E7D32` | `#C00000` | `#888888` | geography, public health, social science |
| `academic_blue_teal` | `#005B8C` | `#00897B` | `#FFB300` | `#888888` | economics, management, education |
| `academic_purple_green` | `#7E57C2` | `#43A047` | `#EF5350` | `#757575` | machine learning, computation, data science |
| `academic_navy_amber` | `#1A237E` | `#FF8F00` | `#D32F2F` | `#888888` | engineering, materials, physics |
| `academic_indigo_lime` | `#283593` | `#9E9D24` | `#C62828` | `#888888` | biology, chemistry, agriculture |
| `academic_blue_pink` | `#1565C0` | `#C2185B` | `#FBC02D` | `#888888` | medicine, clinical, public health |
| `academic_grey_red` | `#37474F` | `#C62828` | `#FFB300` | `#90A4AE` | policy, law, governance, risk |
| `academic_neutral_blue` | `#1F4E79` | `#90A4AE` | `#C00000` | `#888888` | neutral academic deck |

## Typography

Default mixed-font strategy:
- Chinese text: `Microsoft YaHei` or `Source Han Sans SC`.
- Latin letters, numbers, and technical abbreviations: `Times New Roman` for academic text, or the parent deck Latin font if locked.
- Code and model identifiers: `Inter Mono` or `Roboto Mono` only when a monospaced distinction is useful.
- Formula appearance: LaTeX-style serif. For normal PPT pages, render formulas through `scripts/latex_formula_to_png.py`.

When building SVG text:
- Use mixed-font `<tspan>` segmentation for Chinese, Latin, numbers, and symbols.
- Keep all text editable in Version A.
- Do not use `<foreignObject>`.
- Do not split one phrase into multiple overlapping text boxes.

## Font Sizes For 1280 x 720 SVG

| Role | Size |
|---|---:|
| route page title | 28-34 px |
| diagram title inside figure | 22-28 px |
| panel / stage label | 15-20 px |
| node body text | 13-16 px |
| arrow label / caption | 11-13 px |
| formula text inside method diagram | 18-24 px |

Adjust down only when the template has a documented dense layout. Never shrink below legibility to force too much content into one diagram.

## Shape Radius

Default values:

```yaml
shape_radius:
  node_rx: 6
  dense_node_rx: 3
  card_rx: 6
  large_panel_rx: 8
```

Use smaller corners for dense academic route diagrams. Avoid very round card-like UI shapes unless the selected template requires them. If the user asks where to adjust the default, modify `shape_radius.node_rx` in the route `spec_lock.md` or the corresponding template-level `spec_lock_reference.md`.

## Emphasis Rule

High-priority text may be bold and brick red:

```yaml
emphasis:
  color: "#A23B2A"
  weight: 700
  use_for: key finding | central risk | decisive constraint
```

Use it once or twice per route page. Do not use brick red for ordinary labels.

## Do Not

- Do not introduce five or more saturated hues.
- Do not use gradients, glows, large shadows, or decorative color blobs.
- Do not let AI generation invent a new palette.
- Do not use the same font family for all Chinese and Latin text when mixed-font rules are available.
- Do not use saturated backgrounds behind formulas.

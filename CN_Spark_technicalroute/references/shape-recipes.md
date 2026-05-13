# Shape Recipes · 视觉原子积木

> 这些是构成所有 archetype 的**原子视觉元素**。Agent 在 prompt 合成时根据 archetype + sub_variant 选取需要的 recipe 拼装。每个 recipe 都是参数化的，不绑定具体颜色 / 内容。

---

## R1 · Panel（圆角矩形 + 可选顶端徽章）

参数：

- `radius` — 圆角半径（默认 12px）
- `border` — `none | thin (1px) | medium (2px)`
- `fill` — `primary | secondary | surface | none`
- `badge` — `none | number_circle | step_pill | top_color_bar | corner_icon`
- `padding` — `compact (16px) | normal (24px) | airy (36px)`

何时用：
- `quad` panel → fill=surface / border=thin / badge=number_circle
- `method core-steps` step 卡 → border=thin / badge=top_color_bar
- `workflow horizontal-pipeline` 阶段卡 → fill=secondary 浅版本 / border=none

---

## R2 · Badge（编号 / Step 标识）

参数：

- `shape` — `circle | pill | hexagon | none`
- `text` — `<数字>` / `<"Step N">` / `<图标 hint>`
- `placement` — `top_left | top_center | floating_top`
- `size` — `compact (28px) | normal (40px) | large (56px)`

变体：

| variant | 视觉 | 用途 |
|---|---|---|
| `number_circle` | 实心圆 + 反白数字 | thinking quad 四个 panel 的编号 |
| `step_pill` | 矩形 pill，深色底白字 "Step N: 名" | method core-steps / vertical-stack |
| `tag_pill` | 轻量浅底 pill | workflow 列标题 |

---

## R3 · Arrow（连接 / 流向）

参数：

- `kind` — `straight | elbow | dashed | curved-mild`（**禁用** freestyle 弯曲）
- `weight` — `thin (2px) | medium (3px) | heavy (5–6px)`
- `head` — `triangle | open | chevron | none`
- `label` — `none | italic_muted`（仅 italic + muted grey 时显示）

何时用：

| archetype | kind | weight | head | label |
|---|---|---|---|---|
| `thinking cascade` panel 间 | straight | thin | chevron | none |
| `method core-steps` step 间 | straight | thin | open | none |
| `workflow horizontal-pipeline` 列间 | straight | heavy | triangle | italic_muted |
| `workflow circular` 阶段间 | curved-mild (弧形) | medium | triangle | none |
| 反馈环 / 迭代 | dashed | medium | triangle (双向) | optional |

---

## R4 · Banner（贯通横幅）

参数：

- `position` — `top | bottom | middle`
- `width_pct` — 默认 100%
- `height_px` — `40 | 56 | 72`（最终输出 1080 高时；其他尺寸按比例）
- `fill_role` — `primary | accent`
- `text` — yaml 提供
- `icon` — `none | leading_icon`

何时用：

- thinking 的 `bottom_anchor` → bottom + accent fill + leading_icon (target / lightbulb / question)
- method 顶部的标题带（可选） → top + primary fill + leading_icon
- workflow 的 confluence label → middle + secondary fill

---

## R5 · Formula Box（公式区）

参数：

- `bg` — 始终用 muted 浅灰（如 `#F5F8FB`），**不要**饱和色
- `border` — none（用底色区隔即可）
- `padding` — `28px`
- `font_style` — LaTeX serif + math italics for variables + roman for indices
- `caption` — 下方 14px muted 一行"含义：…"或"Meaning:…"

仅用于 archetype=method 的 step / formula 卡。

---

## R6 · Data Cylinder Stack（多层圆柱体）

参数：

- `layers` — 3–5 个（超过看不清）
- `tilt_deg` — `≤ 5°`
- `colors` — 2 种主色循环，**不要** 5 种不同色
- `label_per_layer` — 可选，每层一个 9px hint 文本

仅用于 workflow horizontal-pipeline 的 Extraction 列（或类似"多源数据汇总"语义的地方）。

---

## R7 · Tree / Network 节点群

参数：

- `node_count` — `≤ 8`（多了图模型识别不清）
- `colors` — `branch` 主色 / `leaf` 强调色 / `root` muted（**不要**每节点一种）
- `arrangement` — `horizontal_row | vertical_layer | radial`

用于 workflow funnel / mechanism block / 算法树（如 XGBoost、决策树、神经网络示意）。

---

## R8 · Mini Chart（小图缩略）

参数：

- `kind` — `scatter | bar | line | heatmap | shap`
- `size` — 高度 `≤ 80px`（嵌在卡内），**不要**占满整列
- `colors` — 沿用主图配色，不另起一套

用于 workflow 的 Process / Results 列，作为方法 / 数据 / 输出的视觉代表。

---

## R9 · Symbol Legend Strip（符号说明带）

参数：

- `position` — `below_step_cards`（method archetype）
- `style` — 横向一行 `符号说明:` + 多个 [sym | desc] 对
- `bg` — 极浅灰半透明带或纯白

仅用于 method archetype 当 `symbols` 字段非空。

---

## R10 · Assumption Cards（假设 / 前提卡）

参数：

- `count` — `0–3`
- `layout` — 横向并排
- `icon` — 圆形 + 抽象 icon（balance / lock / filter / clock 等）
- `colors` — 三种 muted 主色循环
- `text` — `<label>` (bold) + `<note>` (muted)

仅用于 method archetype 当 `assumptions` 字段非空。

---

## 拼装规则（agent 在 prompt 中调用）

prompt 中用类似下面的伪 DSL 描述要画的东西：

```
RECIPE: R1 panel, R2 badge=number_circle, R3 arrow=none (quad panels 并列)
RECIPE: R5 formula_box, R9 symbol_strip below
RECIPE: R6 cylinder_stack layers=4 tilt=3deg
```

`generate_route_image.py prompt` 会把这些 RECIPE 注入到 prompt 的 [STRUCTURE] 块中，让图像模型按 recipe 名识别要画什么。

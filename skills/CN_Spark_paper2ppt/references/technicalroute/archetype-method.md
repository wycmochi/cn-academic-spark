# Archetype · 技术方法类（抽象形状定义）

> 用户场景：把**单个模型 / 算法 / 数学方法**的"核心思想 + 公式 + 步骤 + 含义 + 假设"一图说清楚。
>
> ⚠️ 本文件**不绑定任何具体方法 / 公式 / 学科**。所有形状参数是 placeholder，由 `content.yaml` 实例化。

## 何时选这一类

满足下列**任一**即可：

- 输入含 ≥ 1 个公式（LaTeX、数学符号、伪代码均算）；
- 内容描述"Step 1 / Step 2 / Step N"的执行序列；
- 想说清楚"为什么这样写、含义是什么、有什么前提"。

如果只是"为什么做这件事"且没有公式 → [archetype-thinking.md](archetype-thinking.md)；如果是"全文 Data→Methods→Results"的整链路 → [archetype-workflow.md](archetype-workflow.md)。

---

## 四个 sub-variant

| sub-variant | 何时用 | 默认 panel 数 | 论证流向 | 关键视觉 |
|---|---|---|---|---|
| **`core-steps`** | 1 个核心思想 + N 个步骤（N=2–4），步骤独立可读 | core idea + N steps | 左 → 右（核心 → 步骤） | core idea 卡 + step 卡（顶部色条 + 公式区 + 含义） |
| **`vertical-stack`** | 步骤太多需要垂直堆叠 / 算法层级 | N=4–8 步骤 | 自上而下 | 编号 + 长条形 step + 右侧含义 |
| **`formula-grid`** | 多个公式并列展示，需要对比 / 标识不同情形 | 2×2 或 1×N 公式格 | 网格阅读 | 公式卡 + 编号 (1)(2)(3) + 注释 |
| **`mechanism-block`** | 算法的"输入 / 内部机制 / 输出"三段 | 3 大块 | 左 → 中 → 右 | 输入卡 + 中间机制图（带箭头） + 输出卡 |

在 `content.yaml` 中由 `sub_variant: core-steps|vertical-stack|formula-grid|mechanism-block` 指定。

启发式判定：

- 有 `core_idea` 字段 + 2–4 个 `steps` → `core-steps`
- ≥ 5 个 `steps` → `vertical-stack`
- 多个公式但无 step 语义 → `formula-grid`
- 显式描述 input / process / output → `mechanism-block`

---

## 通用视觉约束

| 维度 | 约束 |
|---|---|
| 公式渲染 | 由图像模型按 LaTeX 风格画出（不要截图嵌入 PNG）；公式底浅灰 `#F5F8FB`，**不要**饱和色块 |
| 含义注释 | 公式下方一行，14px muted grey，开头"含义："或"Meaning:" |
| step 顶端色条 | 同一 archetype 内颜色循环（不要每个 step 一种颜色，最多 2 种主色交替） |
| 假设 / 前提卡 | 底部可选 0–3 个圆角小卡，圆形 icon + 1 行标签 + 1 行 muted note |
| 符号说明 | 若公式含 ≥ 3 个自定义符号，单独一条横向 "符号说明" 带 |
| 不要 | 在公式间画箭头 / 在 step 卡上加阴影 / 用 emoji 代替图标 / 渐变色填充 |

---

## 抽象骨架

### Sub-variant `core-steps`

```
[💡 core_idea card]  →  [Step 1 card]  →  [Step 2 card]  →  ...
                           formula_box       formula_box
                           "含义:..."        "含义:..."

       ───── 符号说明：[symbols] ─────  (可选)

[assumption_1]  [assumption_2]  [assumption_3]   (可选，0–3 个)
```

### Sub-variant `vertical-stack`

```
┌───── Step 1: label ─────┐
│ formula   | meaning      │
├───── Step 2: label ─────┤
│ formula   | meaning      │
├─────  ...                ┤
```

### Sub-variant `formula-grid`

```
[(1) formula_1]   [(2) formula_2]
   note_1            note_2
[(3) formula_3]   [(4) formula_4]
   note_3            note_4
```

### Sub-variant `mechanism-block`

```
[Input]   ─→   [Mechanism diagram]   ─→   [Output]
  list           （内部小图 / 流程 / 节点）        list
```

---

## 内容字段（generic schema）

```yaml
archetype: method
sub_variant: core-steps | vertical-stack | formula-grid | mechanism-block
title: <主标题>
core_idea:                              # 仅 core-steps 必填；其他可选
  text: <≤ 50 字描述核心思想>
  visual_hint: <可选，给图像模型的视觉 hint：lightbulb / network / sphere / ...>
steps:                                  # core-steps / vertical-stack 用
  - id: S1
    label: <step 标题>
    formula_latex: <可选，原始 LaTeX 字符串，如 R_j = \\frac{S_j}{\\sum D_k}>
    formula_inline: <可选，纯文本备份>
    interpretation: <一行含义，≤ 60 字>
    color_role: primary | secondary | accent     # 顶端色条角色，不绑 HEX
formulas:                               # formula-grid 用
  - id: F1
    label: <"(1)" / "(a)" / 子标题>
    formula_latex: <LaTeX>
    note: <一行注释>
mechanism:                              # mechanism-block 用
  inputs:
    - <input item>
  process: <一段文字描述内部机制>
  process_visual_hint: <"layered" / "tree" / "iterative loop" / ...>
  outputs:
    - <output item>
symbols:                                # 可选
  - sym: <符号>
    desc: <含义>
assumptions:                            # 可选 0–3 条
  - label: <短标签>
    note: <一行 muted 注释>
    icon_hint: <"balance" / "lock" / "filter" / ...>
color_scheme: <见 color-typography.md>
```

---

## 不要做的事

- ❌ 把公式渲染成 PNG 后嵌入 — 必须由图像模型用 LaTeX 风格直接画；
- ❌ 在 step 之间画粗箭头 — step 间用细横线 / chevron 即可；
- ❌ 公式 panel 里挤超过 1 行含义；
- ❌ 假设卡 ≥ 5 个 — 上限 3；
- ❌ 假设 `formula_latex` 是某个具体公式（如 2SFCA）— 公式由 yaml 提供，本文档不写死；
- ❌ **沿用本文档历史版本中的任何具体方法名 / HEX / 学科**。

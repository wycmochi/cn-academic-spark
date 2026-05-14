# Content Schema · `content.yaml` 通用契约

> 三种 archetype 共享一份 schema 顶层，再按 archetype 分支扩展。本文件是**完整字段表 + 类型 + 必填 / 可选标记**。`scripts/content_schema.py` 用本文件作为校验源。

---

## 顶层必填字段（所有 archetype 共享）

```yaml
archetype: thinking | method | workflow         # 必填
sub_variant: <根据 archetype 列出的 sub-variant>  # 选填，缺省由启发式判定
title: <主标题>                                   # 必填
subtitle: <副标题>                                # 选填
color_scheme: <见 color-typography.md 命名色板>    # 选填，缺省 "discipline_default"
density: airy | balanced | dense                 # 选填，缺省值随 archetype（thinking=balanced，method=airy，workflow=dense）
canvas: "16:9" | "4:3" | "square" | "long"        # 选填，缺省 "16:9"
glossary_preserve:                                # 选填 — 必须逐字保留的术语清单
  - <术语 1>
  - <术语 2>
```

`glossary_preserve` 是**最重要**的 stability 字段：列在里面的每个字符串都会被原样塞进 image prompt 的 "CHINESE CONTENT" 块和 negative 中的 "do not translate" 段。

---

## Archetype = `thinking` 扩展字段

```yaml
sections:                       # 必填，长度 2–6
  - id: P<n>                    # 必填
    label: <段标题>              # 必填
    icon_hint: <抽象图标语义>     # 选填
    points: [<bullet>...]       # 选填，每条 ≤ 25 字
    table_2x2:                   # 选填，与 points 互斥
      - [<cell11>, <cell12>]
      - [<cell21>, <cell22>]
    contrast:                    # 选填，仅 twin sub-variant 用
      old: [<...>]
      new: [<...>]
bottom_anchor:                  # 选填
  kind: question | claim | call_to_action
  text: <≤ 40 字>
top_bridge:                     # 选填，仅 twin sub-variant
  text: <≤ 30 字>
```

## Archetype = `method` 扩展字段

```yaml
core_idea:                       # core-steps 必填
  text: <≤ 50 字>
  visual_hint: <抽象 hint>

steps:                           # core-steps / vertical-stack 用
  - id: S<n>
    label: <step 标题>
    formula_latex: <LaTeX 原文>
    formula_inline: <纯文本备份>
    interpretation: <≤ 60 字>
    color_role: primary | secondary | accent

formulas:                        # formula-grid 用
  - id: F<n>
    label: <"(1)" / "(a)" 等>
    formula_latex: <LaTeX>
    note: <≤ 60 字>

mechanism:                       # mechanism-block 用
  inputs: [<input>...]
  process: <段落 ≤ 200 字>
  process_visual_hint: layered | tree | iterative_loop | black_box | neural_net
  outputs: [<output>...]

symbols:                         # 选填
  - sym: <符号>
    desc: <含义>

assumptions:                     # 选填，0–3 条
  - label: <≤ 15 字>
    note: <≤ 40 字>
    icon_hint: balance | lock | filter | clock | ...
```

## Archetype = `workflow` 扩展字段

```yaml
# horizontal-pipeline 用
columns:
  - id: C<n>
    label: <列标题>
    items:                       # 数据 / 输入项
      - name: <英 / 中名>
        source: <来源 / 出版方>
        logo_hint: <可选>
    blocks:                      # 处理 / 模型块
      - name: <块名>
        kind: tool | algorithm | dataset | concept
        visual_hint: scatter_map | cylinder_stack | tree | shap_bars | heatmap | network | scatter_with_fit_line
        sub_label: <选填>
    arrow_label: <列间标签 italic>

# twin-track 用
tracks:
  - id: T<A|B>
    label: <轨标题>
    blocks: [<...>]
confluence:
  label: <汇合节点名>
  visual_hint: diamond | circle | merge_box
output:
  label: <最终输出>

# funnel 用
inputs: [<input>...]
core:
  label: <核心机制名>
  visual_hint: black_box | neural_net | decision_tree

# circular 用
stages:
  - id: S<n>
    label: <阶段名>
    icon_hint: <选填>
```

---

## 通用约束

| 字段 | 长度 / 类型上限 | 越界时行为 |
|---|---|---|
| `title` | ≤ 30 字 | 截断 + warning |
| `subtitle` | ≤ 60 字 | 截断 + warning |
| `label` (panel / step / col) | ≤ 12 字 | 截断 + warning |
| `points[]` 单条 | ≤ 25 字 | 截断 + warning |
| `interpretation` | ≤ 60 字 | 截断 + warning |
| `bottom_anchor.text` | ≤ 40 字 | 截断 + warning |
| `glossary_preserve` | ≤ 20 条 | 超过则只保留前 20，warning |
| `points[]` 长度 | 0–4 | > 4 报错 |
| `sections` 长度 | 2–6 | 越界报错 |
| `steps` 长度 | 1–8 | 越界报错 |
| `assumptions` 长度 | 0–3 | > 3 报错 |
| `columns` 长度 (horizontal-pipeline) | 2–5 | 越界报错 |

---

## 校验

```bash
python3 scripts/content_schema.py validate <project>/content.yaml
```

输出：

- `OK` — 通过；
- `OK with N warnings` — 列出 warning 项（如截断），允许继续；
- `FAIL` — 报错并阻塞 prompt 合成。

---

## 最小可工作示例（三种 archetype 各一份骨架，**不含具体学科 / 内容**）

```yaml
# thinking — quad
archetype: thinking
sub_variant: quad
title: "<标题>"
sections:
  - { id: P1, label: "<P1>", points: ["<...>", "<...>"] }
  - { id: P2, label: "<P2>", points: ["<...>"] }
  - { id: P3, label: "<P3>", points: ["<...>"] }
  - { id: P4, label: "<P4>", table_2x2: [["<a>","<b>"],["<c>","<d>"]] }
bottom_anchor: { kind: question, text: "<核心问题>" }
glossary_preserve: ["<术语1>", "<术语2>"]
```

```yaml
# method — core-steps
archetype: method
sub_variant: core-steps
title: "<标题>"
core_idea: { text: "<核心思想 ≤ 50 字>" }
steps:
  - { id: S1, label: "<Step 1>", formula_latex: "...", interpretation: "..." }
  - { id: S2, label: "<Step 2>", formula_latex: "...", interpretation: "..." }
symbols: [{ sym: "x", desc: "<含义>" }]
assumptions: [{ label: "<前提>", note: "<注释>" }]
```

```yaml
# workflow — horizontal-pipeline
archetype: workflow
sub_variant: horizontal-pipeline
title: "<标题>"
columns:
  - { id: C1, label: "Data",    items: [{name:"...", source:"..."}],    arrow_label: "<...>" }
  - { id: C2, label: "Process", blocks: [{name:"...", kind:"tool"}],    arrow_label: "<...>" }
  - { id: C3, label: "Methods", blocks: [{name:"...", kind:"algorithm", visual_hint:"tree"}] }
density: dense
```

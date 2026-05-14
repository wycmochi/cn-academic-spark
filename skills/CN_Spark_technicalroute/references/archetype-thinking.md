# Archetype · 思考路线类（抽象形状定义）

> 用户场景：把"**为什么做这件事**"一图说清楚 — 研究背景 / 研究问题 / 理论基础 / 研究意义 这一链路。
>
> ⚠️ 本文件**不绑定任何具体案例 / 学科 / 主题**。所有形状参数是 placeholder，由 `content.yaml`（用户提供）实例化。Agent 看到任何具体内容（例如"拆迁安置""可达性""学术蓝"）都**不应**理解为约束，只能理解为本文档作者写时的示意。

## 何时选这一类

满足下列**任一**即可：

- 内容是"问题缘起 + 背景 / 现状 + 理论支撑 + 价值"，不含具体公式 / 数据流；
- 用户的输入材料属于：研究背景页、论文 Introduction、综述前几页、开题汇报的"研究意义"部分；
- 论证关系是**并列呼应**（4 个角度同时支撑一个核心问题），不是**因果依赖**。

如果内容含公式 / Step 1+2、或含数据 → 模型 → 结果的链路，请切换到 [archetype-method.md](archetype-method.md) 或 [archetype-workflow.md](archetype-workflow.md)。

---

## 三个 sub-variant（按用户内容的形状挑一个）

| sub-variant | 何时用 | 默认 panel 数 | 论证流向 | 关键视觉 |
|---|---|---|---|---|
| **`quad`** | 4 个相对独立的角度同时支撑核心问题 | 4 | 2×2 网格，并列 | 编号徽章 + 底部贯通横幅 |
| **`cascade`** | 链路是"现实痛点 → 既有不足 → 我们的补足 → 因此重要" | 3–5 节点垂直堆叠 | 自上而下，相邻节点用浅箭头串 | 节点 + 步进式箭头 |
| **`twin`** | 强对比："既有研究 VS 本文" / "现状 VS 应然" | 2 大列 + 顶部 / 底部桥接条 | 左右并置 + 上下桥接 | 双色对比 + 桥接横条 |

每种 sub-variant 都参考下方"通用视觉约束"。在 `content.yaml` 中由用户字段 `sub_variant: quad|cascade|twin` 指定；不指定则按"panel 数"启发式判定：

- `len(sections) == 4 且为并列` → `quad`
- `len(sections) ∈ {3,4,5} 且为顺序` → `cascade`
- `2 大段对比` → `twin`

---

## 通用视觉约束（三种 sub-variant 共享）

| 维度 | 约束 |
|---|---|
| panel 形态 | 圆角矩形 `rx ≈ 12px`，1px 细描边或纯填充；不要阴影 / 渐变 / 立体 |
| 标签徽章 | `quad` 用圆形编号；`cascade` 用半圆 step；`twin` 用顶端 pill 标签 |
| 主色 | 来自 `content.yaml.color_scheme`（默认 `discipline_palette` 由 [color-typography.md](color-typography.md) 给出） |
| 强调色 | 仅当 `content.yaml.core_question` 非空时用一次（底部横幅 / 中央焦点） |
| 图标 | 每个 panel 至多 1 个主图标 + 每条 bullet 至多 1 个 inline icon；线性 / 中等粗细，**不要**用 emoji |
| 字号 | 标题 18–22，副标题 14–16，bullet 12–14（最终输出 1080×1920 像素时） |
| 留白 | panel 内左右各 ≥ 24px，bullet 行高 ≥ 1.4 |
| 论证收束 | 底部留 1 行"核心问题"或"主张" — 由 `content.yaml.bottom_anchor` 提供，不存在则**不画** |

---

## 抽象骨架（Mermaid 形状描述，agent 阅读用）

### Sub-variant `quad`

```
[P1.label] [P2.label]
[P3.label] [P4.label]
   ⤓
[bottom_anchor?]   ← 仅当 yaml 提供
```

### Sub-variant `cascade`

```
[P1.label] ▼
[P2.label] ▼
[P3.label] ▼
[P4.label]
   ⤓
[bottom_anchor?]
```

### Sub-variant `twin`

```
[top_bridge?]
[L.label] | [R.label]
[L bullets] | [R bullets]
[bottom_bridge?]
```

---

## 内容字段（generic schema，用户填）

```yaml
archetype: thinking
sub_variant: quad | cascade | twin     # 缺省时按上面启发式判定
title: <主标题>
subtitle: <可选副标题>
sections:                               # quad: 通常 4；cascade: 3–5；twin: 2
  - id: P1
    label: <段落标题>
    icon_hint: <可选，描述图标语义如 "policy" / "data-source" / "gap">
    points:                             # 0–4 条 bullet
      - <bullet text>
    table_2x2:                          # 可选，仅当该段是 2×2 矩阵
      - [<cell11>, <cell12>]
      - [<cell21>, <cell22>]
    contrast:                           # 可选，仅 twin sub-variant
      old: [<...>]
      new: [<...>]
bottom_anchor:                          # 可选 — 底部一行强调
  kind: question | claim | call_to_action
  text: <≤ 40 字>
top_bridge:                             # 可选 — 仅 twin sub-variant
  text: <≤ 30 字>
color_scheme: <由 color-typography.md 列出的命名色板>
```

### 字段语义

- `label` — panel 顶端短标题；agent **必须**用 yaml 给的，不要"美化"或翻译；
- `points` — 每条 ≤ 25 字；超过则截断 + 主代理告警；
- `icon_hint` — 不是绑定字符串，是给图像模型的 hint；可以是"建筑 / 法规 / 数据流 / 路径"这类抽象词；
- `table_2x2` — 若该 panel 是 4 象限矩阵（如"理论 / 方法 / 实证 / 政策"意义），用此字段替代 `points`；
- `bottom_anchor.kind` — `question`（默认强调红） / `claim`（默认主色加深） / `call_to_action`（默认强调橙），具体配色见 [color-typography.md](color-typography.md)。

---

## 不要做的事（硬约束）

- ❌ 在 `quad` panel 之间画粗箭头 — `quad` 是并列关系；
- ❌ 在 `cascade` 节点中插入公式 / 数据流；
- ❌ 在 `twin` 的左右两列里堆完全无关的内容（必须可对比）；
- ❌ 给 panel 加 stock photo / 头像 / 渐变背景；
- ❌ 把 `bottom_anchor.text` 写超过 40 字；
- ❌ 假设主色是某个具体 HEX — 主色来自 `content.yaml.color_scheme`，不是本文档；
- ❌ **把本文档以前出现过的任何例句（"拆迁安置"等）误当成约束沿用**。

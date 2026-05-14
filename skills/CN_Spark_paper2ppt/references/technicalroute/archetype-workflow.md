# Archetype · 全文思路类（抽象形状定义）

> 用户场景：把**整篇研究**的 数据 → 处理 → 提取 → 方法 → 结果（或类似多阶段链路）一图说清楚。
>
> ⚠️ 本文件**不绑定任何具体学科 / 数据源 / 模型**。所有形状参数是 placeholder，由 `content.yaml` 实例化。

## 何时选这一类

满足下列**任一**即可：

- 内容是"从原始材料到最终输出"的整条流水线；
- 含 ≥ 2 个串行阶段，且阶段之间有明确的数据 / 信息流；
- 描述包含多源输入（多种数据 / 资料 / 视角汇入）。

如果只有 1 个核心方法在做"step by step" → [archetype-method.md](archetype-method.md)；如果只是讲"为什么做" → [archetype-thinking.md](archetype-thinking.md)。

---

## 四个 sub-variant

| sub-variant | 何时用 | 默认列数 | 论证流向 | 关键视觉 |
|---|---|---|---|---|
| **`horizontal-pipeline`** | 经典左 → 右流水线（Data → Process → Model → Result） | N = 3–5 列 | 严格左 → 右 | 列标题 + 阶段卡 + 列间过渡箭头（带标签） |
| **`twin-track`** | 两条并行管线最后汇合（如"定量 + 定性" / "理论 + 实证"） | 2 条平行 + 1 汇合 | 上下并行 → 末端汇合 | 两条轨 + 汇合菱形 / 圆 |
| **`funnel`** | 多源输入 → 单一输出 / 模型 / 决策 | 输入扇形 → 1 个核心 | 左扇形 → 中心 | 多个输入块 + 中央核心 + 单输出 |
| **`circular`** | 阶段是循环的（迭代算法 / 闭环系统） | 4–6 阶段 | 环形顺时针 | 环形排列 + 弧形箭头 |

在 `content.yaml` 中由 `sub_variant: horizontal-pipeline|twin-track|funnel|circular` 指定。

启发式判定：

- 默认 `horizontal-pipeline`；
- 两条平行链 → `twin-track`；
- 多源汇聚到单点 → `funnel`；
- 有"迭代 / 反馈 / 闭环"语义 → `circular`。

---

## 通用视觉约束

| 维度 | 约束 |
|---|---|
| 列 / 阶段标题 | 列顶端 14–16px **bold** 短标签，不加 box（保持视觉轻盈） |
| 阶段卡内 | 卡内可放：logo 缩略（数据源）/ 工具 icon + 名（处理工具）/ 多层圆柱体（多源数据栈）/ 模型节点（方法）/ 小图（结果） |
| 列间过渡箭头 | 粗箭头（4–6px），带 italic muted grey **标签**（如 "weighted" / "extracted" / "predicted" / "validated"） |
| 多源数据栈 | 圆柱体（cylinder）堆叠 N=3–5 层，颜色循环，倾斜 ≤ 5° 给微 3D 暗示但不加重阴影 |
| 模型节点 | 分支树 / 神经网络 / 模块组合，颜色 ≤ 2 种 |
| 结果显示 | 条形图 / 散点图 / 热图 缩略嵌入；**不要**把实证结果图占满整列 |
| 整体节奏 | **海报式高密** — 必要时填满画布，但元素不重叠 |
| 不要 | 数据列用 emoji / 列间没有过渡标签 / 模型并列堆没有顺序 / 在结果列里画"实证地图截图" |

---

## 抽象骨架

### Sub-variant `horizontal-pipeline`

```
[Col 1 label]      [Col 2 label]       [Col 3 label]       [Col N label]
┌───────────┐  →  ┌───────────┐   →   ┌───────────┐   →   ┌───────────┐
│  item 1   │     │  block 1   │      │ visual:    │      │ result 1   │
│  item 2   │     │  block 2   │      │ cylinder / │      │ result 2   │
│  ...      │     │  ...       │      │ tree /     │      │ ...        │
└───────────┘     └───────────┘       │ network    │      └───────────┘
                                       └───────────┘
       "label_12"      "label_23"          "label_34"
```

### Sub-variant `twin-track`

```
[Track A: label] → block → block → block ──┐
                                            ▷ [Confluence node]  → [Output]
[Track B: label] → block → block → block ──┘
```

### Sub-variant `funnel`

```
[Input 1] ─┐
[Input 2] ─┤
[Input 3] ─┼─→ [Core mechanism] ─→ [Output]
[Input N] ─┘
```

### Sub-variant `circular`

```
       [Stage 1]
      ↗         ↘
[Stage 4]      [Stage 2]
      ↖         ↙
       [Stage 3]
```

---

## 内容字段（generic schema）

```yaml
archetype: workflow
sub_variant: horizontal-pipeline | twin-track | funnel | circular
title: <主标题>
columns:                                # horizontal-pipeline 用
  - id: C1
    label: <列标题>
    items:                              # 数据源 / 输入项
      - name: <英文 / 中文名>
        source: <来源 / 出版方>
        logo_hint: <可选 hint 给图像模型>
    blocks:                             # 处理 / 模型块
      - name: <块标题>
        kind: tool | algorithm | dataset | concept
        visual_hint: <"scatter_map" / "cylinder_stack" / "tree" / "shap_bars" / ...>
        sub_label: <可选副标>
    arrow_label: <列间过渡箭头标签，italic>
tracks:                                 # twin-track 用
  - id: TA
    label: <轨标题>
    blocks: [<...>]
  - id: TB
    label: <轨标题>
    blocks: [<...>]
confluence:
  label: <汇合节点名>
  visual_hint: <"diamond" / "circle" / "merge_box">
output:
  label: <最终输出>
inputs:                                 # funnel 用
  - <input name>
core:                                   # funnel 用
  label: <核心机制名>
  visual_hint: <"black_box" / "neural_net" / "decision_tree">
stages:                                 # circular 用
  - id: S1
    label: <阶段名>
    icon_hint: <可选>
color_scheme: <见 color-typography.md>
density: dense | balanced | airy        # 默认 dense (workflow 类常是海报式)
```

---

## 不要做的事

- ❌ 数据列用 emoji 代替 logo / tool icon — 必须有"品牌感"或专业感的可识别 mark；
- ❌ 列间没有过渡箭头 + 标签 — 标签是 workflow 类视觉灵魂；
- ❌ 把模型 / 算法列堆成平行无序 — 必须自上而下表达 "先 X 再 Y 再 Z"；
- ❌ 在结果列塞整张地图截图 / 大表格 — 用缩略图代表；
- ❌ 给阶段卡加 panel 编号徽章（这是 thinking 类的特征，workflow 用列标题而非编号）；
- ❌ **沿用本文档历史版本中的任何具体数据源 / 工具 / 学科 / HEX**。

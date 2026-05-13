# Archetype Atlas

> 抽象骨架 SVG 集合 — 每个文件描述 archetype × sub_variant 的**结构**，**不含**任何具体学科内容。
>
> 双用途：
> - **机器读** — `generate_route_image.py prompt --reference-mode atlas_only` 解析 `<desc>` 元素中的布局描述注入 prompt；
> - **人读** — 用户 / agent 浏览 SVG 即可知道这个 sub_variant 长什么样。

## 文件清单

| 文件 | archetype | sub_variant | 说明 |
|---|---|---|---|
| `thinking-quad.svg` | thinking | quad | 2×2 panel + 底部强调横幅 |
| `thinking-cascade.svg` | thinking | cascade | 垂直堆叠 + step pill + 浅箭头 |
| `thinking-twin.svg` | thinking | twin | 双列对比 + 顶部 / 底部桥接条 |
| `method-core-steps.svg` | method | core-steps | 核心思想 + 2–4 Step + 公式底色浅 + 假设底排 |
| `method-vertical-stack.svg` | method | vertical-stack | 长条 step 垂直堆 + 公式中段 + 含义右段 |
| `method-formula-grid.svg` | method | formula-grid | 2×2 / 1×N 公式网格 + 编号 tag |
| `method-mechanism-block.svg` | method | mechanism-block | Input → Mechanism → Output 三大块 |
| `workflow-horizontal-pipeline.svg` | workflow | horizontal-pipeline | 左→右 N 列 + 列间过渡箭头标签 |
| `workflow-twin-track.svg` | workflow | twin-track | 双轨平行 + 末端汇合 |
| `workflow-funnel.svg` | workflow | funnel | 多输入 → 中心机制 → 单输出 |
| `workflow-circular.svg` | workflow | circular | 环形顺时针 N 阶段 |

## SVG 内部约定

每个 SVG 文件都包含：

```xml
<svg viewBox="0 0 1280 720" ...>
  <title>archetype / sub_variant</title>
  <desc>
    Layout: <一段供 agent 阅读的英文 layout 描述>
    Recipes used: R1, R2, R3, R4, R5 ...   ← 引用 shape-recipes.md 的 recipe id
    Slots: <文本占位符列表，例如 {{P1.label}} {{P1.points}}>
  </desc>
  <!-- 形状本体：用占位符颜色 / 占位符文本，不写具体内容 -->
</svg>
```

## 占位符约定

所有要被 yaml 内容替换的文字位置都用 `{{<path>}}` 表示（如 `{{title}}`、`{{P1.label}}`、`{{steps[0].formula_latex}}`）。颜色用 CSS variable 形式 `var(--primary)` / `var(--secondary)` / `var(--accent)` / `var(--muted)` / `var(--surface)`，由 prompt 合成时替换为 `color-typography.md` 中命名色板的 HEX。

## 怎么扩展

新增 sub_variant 时：

1. 在 archetype-*.md 中加这个 sub_variant 的描述；
2. 在 shape-recipes.md 中确认所需 recipe 都已有，缺则补；
3. 在本目录加一份 `<archetype>-<sub_variant>.svg`，遵守上面的内部约定；
4. 把本 README 表格补一行。

---

> 用户的具体例子（mobility / 2SFCA / causal XGBoost 等）**不**保存到本目录。如果用户希望保留某张图作为风格 anchor，请放到 `../Custom_gallery/` 而不是这里。

# Diagram Templates · 学术示意图拓扑模板

每种拓扑下面给出：用什么场合、节点/边规则、布局参数默认值、配色、实现入口。**没有大段代码**，实现都在 `scripts/diagram_templates.py` / `scripts/workflow.py` 里，按本文件叙述去 import 对应函数即可。

## 共享视觉常量

- 主色 `#1F3864`，副色 `#4472C4`，浅底 `#F0F4FA`，强调 `#C00000`，灰 `#888888`；
- 字体：SVG 用 Arial（跨平台一致）；嵌 PPT 中文用微软雅黑、英文/数字 Times New Roman；
- 节点字号：主标题 14pt，副标题 10pt，引用角标 8pt；
- 节点圆角 `rx=8`；
- 箭头粗细 2pt，颜色 `#555555`。

## 拓扑 1 · 横向流程图（Pipeline）

**何时用**：技术路线、实验流程、数据处理 pipeline、Route A / C 的 P6。

**节点规则**：
- 4–6 个节点，沿水平线均匀分布；
- 每个节点圆角矩形，宽 = 画布宽 / (节点数 + 节点数-1)，高 ≈ 宽 × 0.4；
- 节点内：1 行主标题（≤ 8 字）+ 1 行副标题（≤ 12 字，可省）；
- 起止节点用椭圆替代圆角矩形以暗示"开始 / 结束"。

**边规则**：
- 单向直箭头从节点右侧到下一节点左侧；
- 反馈环用虚线 + 双向箭头从末端拐回起点；
- 并行分支用菱形判断节点 + 两条 elbow connector。

**布局参数（默认）**：
- 画布 1200 × 300（独立 SVG）/ 27 × 6 cm（嵌 PPT）；
- 节点间距 = 节点宽 × 0.25；
- 上下垂直居中。

**实现**：
- 独立 SVG → `generate_svg_flow(nodes, edges, out_path)`；
- 嵌 PPT → `make_pipeline_slide(prs, ..., stages=[...], arrows=[...], ...)`。

## 拓扑 2 · 纵向流程图

**何时用**：算法 stack、模型层级、抽象 → 具体的层级流程。

**节点规则**：节点圆角矩形，沿垂直线均匀堆叠，顶层最抽象。

**边规则**：单向箭头从下指向上（"被支撑"含义）或上指向下（"派生"含义），全图统一一种方向。

**布局参数**：画布 600 × 1000（独立 SVG）/ 16 × 18 cm（嵌 PPT）。

**实现**：用横向流程图函数加 `orientation="vertical"` 参数（如 `diagram_templates.py` 提供）。

## 拓扑 3 · 三段式研究框架（Matrix Framework）

**何时用**：研究框架、系统架构、左维度 + 中模块 + 右产出，Route A / C 的 P7。

**结构**：
- 三列等宽或 3:5:3 不等宽；
- 每列顶端深蓝条做"列标题"（30% 高度）；
- 每列下方 3–5 张浅灰底卡片，垂直堆叠；
- 跨列关系用细灰直线连接（不用粗箭头，避免与 pipeline 混淆）。

**节点规则**：
- 列标题 14pt 白；
- 卡片内 12pt 主标题 + 10pt 副；
- 卡片高度 ≈ 列宽 × 0.3，间距 = 卡片高 × 0.2。

**实现**：嵌 PPT → `make_matrix_framework_slide(prs, ..., row_groups=[...], mid_nodes=[...], right_texts=[...], ...)`。

## 拓扑 4 · 思维导图（Radial Mind Map）

**何时用**：综述主题分解、概念分类、Route D 的 P6 概念框架（形式 B）。

**结构**：
- 中心节点 = 综述主题（圆角矩形深蓝白字 16pt）；
- 一级分支 3–5 个，沿圆周均匀分布（角度间隔 = 360° / 一级数）；
- 二级分支挂在一级末端，朝外伸；
- 三级分支可选，朝外继续；
- 节点间用直线或 elbow connector，**无箭头**（思维导图无方向）。

**布局参数**：
- 画布 1400 × 900（独立 SVG）/ 30 × 17 cm（嵌 PPT）；
- 中心节点位于画布中心；
- 一级分支节点距中心 = 画布短边 × 0.25；
- 二级分支节点距一级 = 画布短边 × 0.18；
- 节点最多总共 15 个，超过则拆图或换矩阵表。

**配色梯度**：中心 `#1F3864` → 一级 `#4472C4` → 二级 `#8FAADC`，文字相应反转（深底白字 / 浅底深字）。

**引用**：每个叶子节点旁紧贴 8pt 灰文本框写 `[n]`，对应 PPT 页脚或参考文献页。

**实现**：嵌 PPT → `make_mind_map_slide(prs, ..., center_node=..., level1_nodes=[...], level2_groups={...}, leaf_citations={...})`（在 `diagram_templates.py` 中实现，签名稳定）。独立 SVG 用 `generate_radial_svg(...)`。

## 拓扑 5 · 网络图（Concept Network）

**何时用**：主题间联系、引用网络、争议结构、Route D 的 P12。

**结构**：
- 节点 = 主题，边 = 关系（依赖 / 矛盾 / 互补）；
- 节点位置可手工指定，或用力导向（force-directed）启发式；
- 边按关系类型用不同样式：依赖 = 实线箭头、矛盾 = 红虚线无箭头、互补 = 蓝实线无箭头；
- 图旁加图例。

**节点规则**：圆角矩形，主标题 12pt，节点大小可与该主题文献量正相关（半径 ∝ √文献数）。

**布局参数**：
- 节点数 ≤ 8 时手工放置；> 8 用简易力导向（在 `diagram_templates.py` 中实现）；
- 画布 1200 × 800（独立 SVG）。

**实现**：嵌 PPT → `make_network_slide(prs, ..., nodes=[...], edges=[...], ...)`。节点字典支持 `id / title / size / fill / citation`，边字典支持 `from / to / kind / label`。

## 拓扑 6 · 演化时间轴（Evolution Timeline）

**何时用**：方法代际更迭、技术演进、Route D 的 P6 概念框架（形式 C）。

**结构**：
- 顶部水平箭头线 + 5–10 年一格的年份刻度；
- 每个时间段下方挂 1–3 个节点（圆角矩形）；
- 跨时段关系用斜箭头连节点（"催生" 实线、"替代" 虚线、"挑战" 红线）；
- 颜色梯度：早期 `#888888` → 中期 `#4472C4` → 近期 `#C00000`。

**节点规则**：节点宽度按年份所占像素自适应，主标题 12pt + 年份 10pt。

**布局参数**：画布 1600 × 700（独立 SVG）/ 30 × 14 cm（嵌 PPT）。

**实现**：嵌 PPT → `make_timeline_slide(prs, ..., timeline_points=[...], relation_edges=[...], ...)`。时间点字典支持 `id / year / title / subtitle / citation`，关系边支持 `from / to / kind`。

## 拓扑 7 · 概念矩阵（Concept Matrix）

**何时用**：综述方法对比、文献证据矩阵、Route D 的 P6 形式 A。

**结构**：原生 PPT 表格（不是 SVG），不在本技能 SVG 路径里实现。详见
[../CN_Spark_paper2ppt/references/layout-library.md](../CN_Spark_paper2ppt/references/layout-library.md) 的 `evidence_matrix` 与 `conceptual_framework` 形式 A。

本技能的角色：当 paper2ppt 需要把矩阵表里的"代表方法谱系"再做一张小型示意图时，调本技能出 SVG。

## 拓扑挑选决策

```
要表达"按顺序做了 A → B → C"           → 横向流程图
要表达"从抽象到具体的层级"             → 纵向流程图
要表达"维度 × 模块 × 产出"             → 三段式研究框架
要表达"一个主题分成几个分支"           → 思维导图
要表达"主题之间的多对多联系 / 争议"     → 网络图
要表达"方法随时间的演化"               → 演化时间轴
要表达"行 × 列对照"                    → 概念矩阵（用 PPT 原生表）
```

## 与 paper2ppt 的协作约定

paper2ppt 调用本技能时传入：

```python
{
    "archetype": "pipeline" | "matrix_framework" | "mind_map" | "network" | "timeline",
    "nodes": [...],
    "edges": [...],
    "theme_color": "1F3864",   # 与该 PPT 的主题色一致
    "target": "svg" | "pptx_shapes",
    "citations": {node_id: "[3]"},  # 可选
}
```

返回：

```python
{
    "svg_path": "workflow_output/diagram_<n>.svg",
    "shape_script": "...python-pptx 形状脚本片段...",  # target=pptx_shapes 时
    "manifest": {...},
}
```

引文角标 `[n]` 在节点上加上即可，完整 GB/T 7714 条目由 paper2ppt 在该页页脚 / 参考文献页处理，**本技能不写引文条目**。

## 实现入口（写代码时再打开）

```python
from CN_Spark_workflow.scripts.workflow import (
    extract_keywords_from_text,
    pdf_to_images,
    is_diagram_image,
    generate_svg_flow,
    run_workflow_extract_svg,
)
from CN_Spark_workflow.scripts.diagram_templates import (
    make_pipeline_slide,
    make_matrix_framework_slide,
    make_mind_map_slide,
    make_network_slide,
    make_timeline_slide,
)
```

新增 / 改拓扑时：先在本文件加叙述、定参数、给协作约定，再到 `diagram_templates.py` 实现，函数签名稳定不破坏既有调用。

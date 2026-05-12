# Layout Library · 版式说明与适配规则

本文件描述每种 `content_type` 对应的版式逻辑与默认参数。**没有大段代码** — 实际 python-pptx 实现在 `scripts/layout_library.py`，按本文件叙述去 import 对应函数即可。

## 全局视觉常量（默认值）

颜色 / 字体 / 版心都在 `scripts/layout_library.py` 顶部三个 dict：`THEME` / `FONTS` / `LAYOUT`。要换主题色 / 字号 / 版心，**只改这三个 dict**，不要改各版式函数内部。

默认值：

- 幻灯片 33.87 × 19.05 cm（脚本中以 `slide_w=29.7 / slide_h=21.0` 占位，按 16:9 调整即可）；
- 主色深蓝 `#1F3864`，副色 `#4472C4`，浅底灰 `#F0F4FA`；
- 字体：标题区 `微软雅黑 20pt 加粗 白`、横幅文字 `微软雅黑 11pt 白`、正文 `微软雅黑 14pt`、图注 `微软雅黑 9pt 灰`、引文 `8pt #888888`（中英混排）；
- 版心：左右 1.5cm，顶部 2.0cm，header 高 1.6cm，底部 banner 高 1.1cm。

要换备选主题（墨绿 / 深灰 / 校色），改 `THEME` 即可，所有版式联动跟随。

## 通用元素

每页除封面、甘特图全图页、参考文献页外都包括：

1. **顶部 header**：左上幻灯片编号（28pt 白），右侧主标题（20pt 白）；深蓝底色覆盖整个 header 高度。`add_header(...)`。
2. **底部 banner**：深蓝底，11pt 白字，写本页一句话主旨。`add_bottom_banner(...)`。
3. **引文页脚**（如本页有引用）：紧贴 banner 上方，8pt 灰，详见 [citation-style.md](citation-style.md)。
4. **右上 logo 占位符**：3.0 × 1.0 cm，用户后续替换。

## 各 content_type 版式

### `cover` · 封面

全屏深蓝底 + 居中标题 32pt 白色加粗；副标题/作者/单位/日期分行居中。无 header、无 banner、无 logo（logo 可放右下小尺寸）。

### `toc` · 目录

左侧章节列表（4–6 条），每条 18pt 加粗 + 一行 12pt 副标题。当前章节加深蓝竖线高亮（用于过渡页时）。无图。

### `text_flow` · 背景 / 引言型

2–4 条要点（14pt），左侧短段落 + 右侧一张可选小型示意图。如果完全无图就用左 60% 文字 + 右 40% 留白做"喘息"，**不**强行塞图。

### `bullet_analysis` · 要点分析

3–5 条短 bullet（≤ 12 字 / 条）+ 右侧支持图或表。bullet 数字 / 项目符号用主题副色。

### `pipeline` · 技术路线 / 流程

**全宽水平流程图**。4–6 个圆角矩形节点 + 单向箭头连接线。
- 节点宽度按页宽均匀分布；
- 节点内深蓝底 + 14pt 白字主标题 + 10pt 白字副标题；
- 箭头深灰 (`#555555`)，2pt；
- 不要做成 1:1 左右栏。

如有阶段性分支（菱形判断、并行分支），用 `add_shape(MSO_SHAPE.DIAMOND)` 做判断节点 + 两条 elbow connector 分出去。

### `matrix_framework` · 研究框架 / 三维结构

三段式：左维度 / 中模块 / 右产出。或左输入 / 中处理 / 右输出。

- 三列等宽或 3:5:3 不等宽；
- 每列顶端一个深蓝条做"标题"，下方放 3–5 个浅灰底卡片；
- 跨列关系用细灰直线表示（不用粗箭头，避免与 pipeline 混淆）。

### `results_chart` · 关键证据

**hero figure 主导版式**。一张主图占页面 65–80%，右侧或下方一条**窄解读条**：

- 解读条字数 ≤ 60 字；
- 一句话结论 + 2–3 条要点；
- 配色克制；
- 图右下 / 标题处加 "图来源：[n]"；
- 页脚加该 [n] 的完整条目。

**绝对不要 1:1 左右栏装一张密集图**。

### `table_compare` · 对比表

python-pptx 原生 `add_table` 实现，行=维度，列=主体/方案。
- 表头深蓝底白字加粗 12pt；
- 数据行斑马底 (`#FFFFFF` / `#F0F4FA`)；
- 单元格水平居中、垂直居中；
- 数字列使用 Times New Roman；
- 表下加 9pt 灰图注 + 来源；
- 不允许把表格替换成截图。

### `gantt` · 甘特图（Route C 必有）

整页一张 matplotlib 渲染的 PNG，**不加底部横幅**避免遮挡。生成参数与配色见 [route-proposal.md](route-proposal.md) 的"甘特图"一节。这是路线 C 中**唯一允许位图**的页（matplotlib 输出无法在 ppt 中逐节点编辑，作为代价由用户改数据后重生成）。

### `policy_stat_cards` · 数据卡阵列（Route B 常用）

2–4 张深底卡片横向排列，每张包含：
- 大号黄色数字 28pt 加粗（Times New Roman）；
- 13pt 白色标签；
- 8pt 灰来源（"来源：国家统计局 2024 公报"）。

### `conclusion` · 结论 / 展望

左成果右展望两栏，开放排版无多余框线；3–4 条对照 bullet。可在底部加一行加粗主张作为收尾。

### `conceptual_framework` · 概念框架（Route D 必有）

三选一形式（详细规则与挑选逻辑见 [route-literature-review.md](route-literature-review.md) 的"核心页"一节）：

#### 形式 A · 主题矩阵表

全宽 `add_table`，行=主题（≤ 6 行），列=核心方法/主要结论/代表文献/备注。文献列只放 `[n]`。表头深蓝白字 12pt 加粗，数据 10pt，文献列字号 9pt。表下加"详见参考文献页 P{n}"。

#### 形式 B · 主题思维导图

全矢量 Shape 实现，居中放射布局：
- 中心节点 = 综述主题（圆角矩形深蓝白字 16pt）；
- 一级分支 3–5 个，从中心向外按角度均匀分布（72° / 90° / 120° 间隔）；
- 二级分支挂在一级分支末端，最多 3 层；
- 节点之间用 `add_connector(MSO_CONNECTOR.STRAIGHT)` 或 `MSO_CONNECTOR.ELBOW`，无箭头（思维导图不带方向）；
- 每个叶子节点旁紧贴 8pt 文本框 `[n]` 对应文献编号；
- 颜色梯度：中心深蓝 → 一级中蓝 → 二级浅蓝；
- 节点最多 15 个，超过则做分页或换矩阵表。

#### 形式 C · 演化流程图

横轴时间（左老右新），顶部水平箭头线 + 年份刻度。每个时间段下方挂 1–3 个节点，跨时段关系用斜箭头表达"催生 / 替代 / 挑战"。颜色：早期灰 → 中期蓝 → 近期红。

实现入口：
- `make_conceptual_framework_slide(..., framework_type="mind_map", framework_data=...)`
- `make_conceptual_framework_slide(..., framework_type="network", framework_data=...)`
- `make_conceptual_framework_slide(..., framework_type="timeline", framework_data=...)`

内部直接调用的可复用函数：
- `make_mind_map_slide`
- `make_network_slide`
- `make_timeline_slide`

### `theme_detail` · 主题详述（Route D）

两种小变体：
- **方法谱系页**：用 `matrix_framework` 三列结构（方法分类 / 代表算法 / 优缺点）；
- **结论证据页**：用 `results_chart`（hero 图 + 解读条）或 `table_compare`（数据集×指标）。

### `evidence_matrix` · 文献证据矩阵（Route D）

类似 `table_compare`，但行=代表论文，列=数据集/方法/指标/年份。每行末加 `[n]`，页脚或下一页给完整 GB/T 7714 条目。

### `references_full` · 完整参考文献页（Route C / D 必有）

全宽两栏 10pt 列表，按引用顺序编号。中文字符微软雅黑、数字与拉丁字符 Times New Roman 逐 run 写入。可跨多页，每页保留 header 但**不加 banner**。

## 版式适配规则（关键）

不要把每页都套成 1:1 左右栏。让版式跟随**内容密度**与**该页的论证角色**：

- **图主导页**：hero figure 占 65–80%，文字成"窄解读条"；
- **文主导页**：文字栏占 60–70%，图作小型示意；
- **流程主导页**：全宽，不要分栏；
- **对比页**：原生表格全宽；
- **总结页**：开放排版，留白多于装饰。

具体决策树：

```
该页有 1 张密集图？        → results_chart（hero + 窄解读）
该页有 ≥ 2 张图要对比？    → 上下分栏或全宽宫格
该页是流程 / 路线？        → pipeline 全宽
该页是三维结构 / 框架？    → matrix_framework 三列
该页是数据对照表？         → table_compare 原生表
该页是综述主题概念框架？   → conceptual_framework 三选一
该页只是要点 + 没图？      → bullet_analysis 文左留白右
该页只是过渡 / 标语？      → 居中放大主张
```

## 公式版式规则

学术 PPT 里的公式页默认也纳入版式库，目标是服务**学术内容理解与表达**，而不是只做符号排版。

### `formula_modular` · 模块化步骤公式页

默认优先形式，适合公式较多但每步解释较短的页面：
- 页面由 3–4 个纵向模块组成；
- 每个模块顺序固定为：步骤标题 → 核心公式 → 结果式 → 一句说明；
- 适用于技术路线、模型流程、指标构造、估计步骤；
- 实现入口：`scripts/route_helpers.py:make_formula_slide(..., formula_mode="modular", ...)`。

### `formula_sectioned` · 标题分段公式页

适合公式之间存在明显流程切换、条件切换或需要较多说明的页面：
- 每段顶部用深色标题条分隔；
- 标题下先放解释，再放对应公式组；
- 适用于“变量定义 / 目标函数 / 求解策略”“早期方法 / 中期方法 / 近期方法”这类结构；
- 实现入口：`make_formula_slide(..., formula_mode="sectioned", ...)`。

### 选择原则

- 默认优先 `formula_modular`；
- 只有在中间说明文字较多、公式属于不同流程模块时，才切换到 `formula_sectioned`；
- 复杂公式继续用 `formula_to_png`，但页面组织必须由 `make_formula_slide` 统一管理，不允许零散摆放。

## 版式与引文的协作

任何版式只要本页含引用，都要预留**页脚引文带**（高约 1.5–2.0 cm，紧贴 banner 上方；如无 banner 则贴页面底 0.5cm）。版式函数在 `scripts/layout_library.py` 中已经把页脚带的 y 坐标算好，调用 `add_citation_footer(slide, citations_for_this_slide)` 即可，不要自己另算位置。多 run 中英混排实现见 [citation-style.md](citation-style.md)。

## 实现入口（编码时再打开）

需要写代码时直接 import：

```python
from CN_Spark_paper2ppt.scripts.layout_library import (
    THEME, FONTS, LAYOUT,
    add_header, add_bottom_banner, add_citation_footer,
    make_cover_slide,
    make_pipeline_slide, make_matrix_framework_slide,
    make_conceptual_framework_slide,    # Route D
)
from CN_Spark_paper2ppt.scripts.route_helpers import (
    make_gantt_slide, formula_to_png, make_formula_slide,
    insert_policy_image, insert_policy_stat_card,
)
```

`scripts/` 目录里的函数签名稳定；要扩展版式时新增同名风格的函数即可，不要修改既有函数签名以免影响其他路线。

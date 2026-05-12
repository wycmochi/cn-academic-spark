---
name: cn_spark_workflow
description: >
  学术示意图 / 流程图 / 技术路线图 / 研究框架图 / 概念框架图 / 思维导图 / 综述地图的
  生成与解析子技能。可独立调用（用户只想要单张图），也可以由 paper2ppt 在生成 PPT 中
  某一页时调用（典型如开题报告的技术路线页、文献综述的概念框架页）。
  输入可以是：关键词与节点描述、一段文字（自动抽关键词与流程节点）、或者一张已有图（用于检测、
  解析与重绘）。输出默认是矢量 SVG 或可写入 python-pptx 的形状脚本，保证可编辑可复用。
---

# Purpose
为学术 PPT 生产**真正学术风格**、**矢量可编辑**的流程图、技术路线图、研究框架图、概念框架图、思维导图与综述地图。

输出**不是**位图截图，而是 SVG / 矢量形状描述 / 可写入 python-pptx 的脚本，方便后续在 PowerPoint / WPS 中逐节点编辑、调色、复用。

# Core Principle · 学术示意图四件事

学术示意图与营销 PPT 装饰图最大的区别在于：

1. **节点是概念，不是装饰**。每个节点要有明确的指代（一个步骤、一个模块、一个主题、一个文献），听众能在 3 秒内读懂。
2. **关系是论证，不是连线美感**。每条连线要有可命名的关系（顺序 / 因果 / 依赖 / 派生 / 对照 / 包含），不要为了画面平衡随便连。
3. **方向感来源于论证轴**，不是来源于画布。横向流程 = 时间 / 工序；纵向流程 = 抽象层级；放射 = 主题分类；网络 = 多对多关系。先想清楚论证轴再选拓扑。
4. **配色克制 + 单种字体**。学术图色应不超过 3 种主色 + 1 种强调色；中文用微软雅黑、英文/数字用 Arial 或 Times New Roman；图内字号 ≤ 12pt 配合 PPT 投屏可读。

# Lean Operating Mode

默认走最短链路：

**做：**
- 接收用户给的节点列表 + 关系列表 → 直接出图；
- 没有列表时，从一段输入文字里抽关键词、推断节点；
- 输入是已有图时，用边缘检测+启发式判断是不是流程图，再尝试解析；
- 输出 SVG（独立使用）或形状脚本（嵌入 PPT）。

**默认不做：**
- 不调用任何商业绘图 SaaS；
- 不安装重型依赖（OpenCV / Detectron2 之类）只为做一张示意图；
- 不爬付费数据库（爬虫只对配置过的 seed 站点做轻量请求）；
- 不让 OCR 和图像分析阻塞主流程：能用就用，不能用就退化为"用户请提供节点列表"。

# Toolchain Policy

跨平台 Python 优先：

- **PIL (Pillow)** — 图像基本处理与边缘检测启发式；
- **xml.etree** — SVG 写出，不引入额外依赖；
- **PyMuPDF / pdftoppm** — PDF 页面转 PNG（可选；pdftoppm 系统命令存在就用，否则跳过）；
- **python-pptx** — 当输出形式是"嵌入 PPT 的矢量形状"时用其 `add_shape` / `add_connector`；
- **requests + bs4 + pytesseract** — 全部可选，用于学术站点检索与图内文字识别。

# Accepted Inputs

可以是以下任意一种：

1. **节点 + 关系列表**（最理想）：用户直接给 `nodes = ["文献调研", "数据采集", ...]` 与 `edges = [(0,1), (1,2), ...]`；
2. **一段描述文字**：从中抽 3–5 个关键词与流程节点（用 `extract_keywords_from_text`）；
3. **一组关键词**：用于在 seed 站点（ScienceDirect / Google Scholar / CNKI）检索相关论文标题，再综合提取节点；
4. **一张已有图**（PNG / PDF）：先做边缘检测判断是否流程图，能解析则解析，不能解析则建议用户改为节点列表输入。

# Default Fast Path

1. 判定输入类型；
2. 如果输入是 PDF，先 `pdf_to_images`，再 `is_diagram_image` 过滤；
3. 如果输入是描述文字，`extract_keywords_from_text` 抽关键词，让用户确认抽出的节点是否正确；
4. 选择拓扑类型（详见 [diagram-templates.md](references/diagram-templates.md)）；
5. 调 `generate_svg_flow` 出 SVG，或调 `make_pipeline_slide` / `make_matrix_framework_slide` 写入 PPT；
6. 写 `output/diagram_manifest.md`：节点、关系、源、配色记录，便于复用。

# Diagram Archetypes · 选拓扑

学术示意图的常见拓扑只有这几种，按论证轴选：

| 论证轴 | 拓扑 | 何时用 |
|---|---|---|
| 时间 / 工序 | **横向流程图（pipeline）** | 技术路线、实验流程、数据处理 pipeline |
| 抽象层级 / 输入→输出 | **纵向流程图** | 算法 stack、模型层级 |
| 维度 × 模块 × 输出 | **三段式研究框架（matrix framework）** | 研究框架、系统架构 |
| 中心 → 分支 | **思维导图（radial mind map）** | 综述主题、概念分解 |
| 多对多关系 | **网络图（concept network）** | 主题间联系、引用网络、争议结构 |
| 时间维度 + 演化关系 | **演化时间轴** | 方法代际更迭、技术演进 |
| 行 × 列对比 | **矩阵表（concept matrix）** | 综述方法对比、文献证据矩阵 |

详细每种拓扑的节点/边规则、配色、字号、布局算法见 [diagram-templates.md](references/diagram-templates.md)。

# Style Rules · 学术示意图风格

- **配色**：主色与 PPT 主题色一致（默认深蓝 `#1F3864`），副色浅蓝 `#4472C4`，背景灰 `#F0F4FA`，强调红 `#C00000`（仅用于关键节点 / 风险节点），不超过 4 色；
- **节点形状**：标准节点圆角矩形 `rx=8`；判断节点菱形；起止节点椭圆；并发分支用粗短斜线汇合；
- **字号**：节点主标题 14pt，副标题 10pt，全图说明 9pt；
- **字体**：中文微软雅黑、英文/数字 Arial（SVG 用 Arial 跨平台一致；PPT 内嵌用 Times New Roman 与正文匹配）；
- **箭头**：单向用细箭头（2pt 深灰 `#555555`），双向 / 反馈用虚线 + 双向箭头；
- **不要**：渐变填充、阴影、3D 立体、装饰图标、emoji、模糊背景；
- **空间**：节点间最小间距 ≥ 节点高度的一半；不允许文字跑出节点框。

# Citation in Diagrams · 图内引用

如果示意图节点的来源是某篇文献（如"Smith 2024 提出的 RAG 架构"），处理方式：

- 节点标题正下方加 8pt 灰色 `[3]` 角标；
- 该图被嵌入 PPT 时，由 paper2ppt 在该页页脚补完整 GB/T 7714 条目（见 [../CN_Spark_paper2ppt/references/citation-style.md](../CN_Spark_paper2ppt/references/citation-style.md)）；
- 整张图来源于某文献时（重绘他人原图），在图右下加 9pt 灰 `图来源：[3]`，并在 paper2ppt 页脚列条目。

# Workflow（5 步）

## Step 1 · 判定输入与目标拓扑

询问用户（或从输入推断）：节点是给定的还是要从文本抽取？输出用途是独立 SVG 还是嵌入到 PPT 某一页？目标拓扑是流程 / 框架 / 思维导图 / 网络 / 矩阵？

## Step 2 · 抽取或确认节点与关系

- 输入文字 → `extract_keywords_from_text` 抽关键词 → 与用户确认节点定名；
- 输入图 → `is_diagram_image` 过滤 → 给用户展示候选图 → 由用户口述节点与关系；
- 输入是 PDF → `pdf_to_images` + `is_diagram_image` → 同上。

确认后，节点与关系都用结构化 list 表示，存入 `diagram_manifest.md`。

## Step 3 · 选拓扑、定布局参数

按"Diagram Archetypes"表选拓扑。布局参数（节点尺寸、间距、画布大小）用 [diagram-templates.md](references/diagram-templates.md) 中的默认值，不要自己拍脑袋定。

## Step 4 · 生成

- 独立 SVG：调 `generate_svg_flow` 或 `diagram_templates.py` 中对应的 SVG 生成器；
- 嵌入 PPT：调 `make_pipeline_slide` / `make_matrix_framework_slide`，或者直接给出 python-pptx 形状脚本片段让 paper2ppt 填入对应页。

**默认输出矢量**。除非显式要求位图，不要输出 PNG。

## Step 5 · 检查与回写

- 重开 SVG 检查节点字数是否溢出节点框；
- 嵌入 PPT 时，重开 .pptx 看每个 shape 是否在版心内；
- 把生成参数写入 `diagram_manifest.md`，便于后续修改 / 复用。

# Output Files

```
workflow_output/
├── diagram_<n>.svg                ← 独立 SVG（默认）
├── diagram_<n>.shapes.py          ← 嵌入 PPT 的形状脚本片段（可选）
├── diagram_manifest.md            ← 节点 / 关系 / 配色 / 来源 / 用途
└── candidates/                    ← 从 PDF / 图中抽出的候选图（如有）
```

# Quality Rules

- 输出必须是矢量形式（SVG 或 python-pptx 形状），除非用户明确要位图；
- 节点不允许跑出画布；
- 文字不允许溢出节点框；
- 配色不超过 4 色；
- 任何来自他文献的节点 / 整图必须有来源标记并能与 paper2ppt 的引文页脚对接；
- 不允许使用未在节点列表中出现的节点（防止"画图过程中无中生有"）。

# Fallback Rules

- 输入图无法解析 → 直接提示用户给节点列表；
- 系统没有 pdftoppm → 跳过 PDF 渲染，直接接受用户上传的 PNG / 节点列表；
- 没有 requests / bs4 → seed 站点检索退化为"返回搜索 URL 让用户自己点开"，不阻塞主流程；
- 节点数 > 15 → 建议用户拆分为两张子图或换用矩阵表。

# References Index

| 文件 | 内容 | 何时读 |
|---|---|---|
| [references/diagram-templates.md](references/diagram-templates.md) | 各拓扑的布局参数、配色、节点规则、SVG / PPT 实现指引 | Step 3 选拓扑前 |
| [references/seed_urls.md](references/seed_urls.md) | seed 学术站点列表 | 仅当需要从关键词反查文献时 |
| [references/seed_sites.json](references/seed_sites.json) | seed 站点的检索 URL 模板（机器读） | 仅当需要从关键词反查文献时 |

`scripts/workflow.py` 是主流程实现（关键词抽取、PDF→图、检测、SVG 生成）；`scripts/diagram_templates.py` 是各拓扑的 PPT 形状写入函数。**只有真正写代码时才打开**。

# 与 paper2ppt 的协作

被 paper2ppt 调用的典型场景：

- Route A 的 P6 技术路线页 → 横向流程图；
- Route A / C 的 P7 / P10 研究框架页 → 三段式 matrix framework；
- Route C 的 P9 / P10 → 同上；
- Route D 的 P6 概念框架页 → 思维导图 / 矩阵表 / 演化流程图三选一；
- Route D 的 P12 主题间联系 → 网络图。

调用形式：paper2ppt 把 `nodes / edges / archetype / theme_color` 传过来，本技能返回可直接 `slide.shapes.add_*` 的脚本片段或 SVG 路径。两边都不直接渲染位图。

---
name: cn_spark_paper2ppt
description: >
  把一份完整的学术材料（论文、报告、开题书、读书笔记、综述提纲、PDF、Word、Markdown 或粘贴文本）转换为一整套中文学术 .pptx。
  覆盖四类汇报场景：学术论文讲解 / 课程报告 / 开题报告 / 文献综述。
  生成内容包括：三级大纲、每页文字、每页选图、矢量流程图与研究框架、底部横幅、文内引文与页脚 GB/T 7714 引用、备注区演讲词。
  最终交付的是**可编辑可复用的 .pptx**，不是 Markdown 大纲。当用户上传学术材料且要求做幻灯片/答辩/汇报时调用本技能。
---

# Purpose
把学术材料转换成一整套**中文、矢量可编辑、含学术引文与演讲词**的 `.pptx` 幻灯片。

输出物**必须是真正的 .pptx 文件**，而不是 Markdown 提纲或脚本。所有流程图、研究框架、表格都用 python-pptx 的原生形状/连接线/表格写出来，让用户在 PowerPoint 或 WPS 中可以直接双击修改、复用排版。

# Core Principle · 论证主轴优先于章节顺序

用论文/报告的**论证逻辑**作为幻灯片骨架，不是机械复制章节顺序。无论哪条路线，每张证据型幻灯片都要能回答听众脑子里的下一个问题：

1. 这件事为什么重要？
2. 当前空缺/瓶颈/争议是什么？
3. 我们做了什么？
4. 关键证据是什么？
5. 为什么应该相信这个证据？
6. 这件事新在哪、能怎么复用？
7. 它的边界与开放问题是什么？

这条主轴比"标题页→目录→前言→方法→结果→结论"的固定模板更重要。

# Lean Operating Mode

默认走最短的、能产出可用 PPT 的链路：

**做：**
- 只读理解论证所必需的源材料；
- 只抽取真正会出现在幻灯片里的图/表；
- 直接生成 `.pptx` 作为主交付物；
- 做轻量结构检查（重开 `.pptx`、点幻灯片数、点嵌入图数、点备注是否存在）；
- 写一份精炼的 `qa_report.md`。

**默认不做（除非用户明确要求）：**
- 把全文每张图、每页、每个补充材料都批量提取；
- 在文本可选时执行 OCR；
- 把全文落地成长 markdown 脚本；
- 装新依赖只为完成一份常规 PPT；
- 调起 LibreOffice/桌面办公软件去渲染每一页预览。

# Toolchain Policy

跨平台 Python 优先，不绑 OS：

- **PyMuPDF** — 元信息、文本、图注、关键页渲染；
- **Pillow** — 图像裁切；
- **python-pptx** — 幻灯片创作与重开验证（这是主工具）；
- **matplotlib** — 甘特图、必要的图表与 LaTeX 公式 PNG；
- **zipfile + python-pptx 二次打开** — 包结构校验。

LibreOffice / soffice 当作可选预览渲染器，存在就用，不存在就跳过。绝不引入 Keynote / AppleScript / Windows 自动化 / 指定 OS 字体路径。字体只用「微软雅黑 / 宋体 / Times New Roman」这类 Office/WPS 都自带的安全字体。

# Accepted Inputs

可以是以下任意一种或组合：

- 完整论文 PDF / 报告 PDF；
- 补充材料、补充图表；
- 转成 docx / md 的论文文本；
- 摘要 + 结果 + 图注；
- 结构化读书笔记或综述提纲；
- 手工粘贴的文本；
- `input/source.md`；
- 用户自带的 `.pptx` 模板。

默认输出语言：简体中文。技术术语、基因/蛋白/模型/数据集名、统计量、缩写在更精确时保留英文原文。

# Default Fast Path（普通可选文本 PDF）

1. 用 PyMuPDF 抽元信息、摘要、各级标题、图注、表注。
2. **先判断路线**（A/B/C/D 见下文），再决定要哪几页图。
3. 仅当图位不清时，渲染低分辨率联系表（contact sheet）。
4. 仅对入选的图/表所在页做高分渲染并裁切；命名清晰。
5. 直接用 python-pptx 写 `.pptx`：原生表格、原生形状、原生连接线、原生备注；图片仅在原视觉本身是证据时插入。
6. 重开 `.pptx` 验证结构；有 LibreOffice 时再渲一份预览。

# Workflow（7 步）

下文 7 步是主线。每条路线（A/B/C/D）会在第 1、3、4、5 步上各自有微调，具体在
[references/route-academic-paper.md](references/route-academic-paper.md) /
[references/route-course-report.md](references/route-course-report.md) /
[references/route-proposal.md](references/route-proposal.md) /
[references/route-literature-review.md](references/route-literature-review.md) 中分别给出。

## Step 1 · 解析输入材料，生成三级大纲

抽取（如有）：题目、作者、机构、期刊/会议、年份、DOI；研究领域与子领域；论文/报告类型；
核心问题与知识空缺；主张/假设；研究设计与数据；关键方法与对照；主要结果与定量发现；
关键图表与图注；验证/鲁棒性/敏感性分析；局限性；学术或社会意义。

不要编造材料里没有的数字、机制、文献或图细节。
用两遍阅读：先抓元信息、摘要、标题、图注；再只读支撑入选幻灯片所必需的结果与方法段落。

大纲产出形式（用于第 2 步给用户看）：

- 研究背景 / 引言 — `text_flow`
- 文献综述 / 相关工作 — `bullet_analysis`
- 方法 / 模型 / 技术路线 — `pipeline` 或 `matrix_framework`
- 实验 / 结果 — `results_chart`
- 结论 / 展望 — `conclusion`
- 每节都要预留 `bottom_banner`（中国学术 PPT 的标志性元素，深蓝底白字一句话主旨）。

## Step 2 · 路线分流 + 用户确认大纲

按下表判定路线，**只读对应那一份 route 文件**：

| 输入类型 | 路线 | 必读 references |
|---|---|---|
| 学术论文（期刊/会议、单篇） | **Route A** | [route-academic-paper.md](references/route-academic-paper.md) |
| 课程报告（含时政背景、政策图） | **Route B** | [route-course-report.md](references/route-course-report.md) |
| 开题报告（含甘特图、研究计划） | **Route C** | [route-proposal.md](references/route-proposal.md) |
| 文献综述 / Review / 综述讲解 | **Route D** | [route-literature-review.md](references/route-literature-review.md) |
| 混合 / 不确定 | 先按 Step 1 出大纲，再问用户落到哪一路线 | — |

把大纲用结构化文本展示给用户：

```
第1页  封面
第2页  目录
第3页  [1] 研究背景 ——（text_flow）
       核心论点：……
       底部横幅：……
第4页  [1.1] 研究动机 ——（bullet_analysis）
       ……
```

用户回应：
- 同意 → Step 3；
- 修改某几页 → 原地更新大纲、复述被改页、再次确认；
- 上传新大纲文件 → 解析替换原大纲、再次展示。

## Step 3 · 收集风格偏好

一次性列出，用户逐条回复：

1. 汇报类型：毕业答辩 / 组会 / 课程 / 综述讲解 / 其他
2. 预计时长（分钟）→ 自动估算页数（约 1.5 分钟/页，综述讲解可放宽到 2 分钟/页）
3. 是否有学校 / 实验室 Logo（上传或告知校名）
4. 配色偏好：深蓝经典（默认） / 墨绿学术 / 深灰简约 / 跟随学校色
5. **引文偏好**：默认 GB/T 7714，可选 APA / MLA — 见 [citation-style.md](references/citation-style.md)
6. 路线专属问题（例：Route B 是否要插入时政图、Route C 甘特图时间窗、Route D 综述跨度）

## Step 4 · 选版式

按大纲中的 `content_type` 字段，从 [layout-library.md](references/layout-library.md) 选版式。各路线必有的版式：

- Route A：必有 `pipeline`（技术路线）、`matrix_framework`（研究框架）。
- Route B：`text_flow` 页中插入时政图占位符。
- Route C：必有 `pipeline`、`matrix_framework`、`gantt`（甘特图）。
- Route D：必有 `conceptual_framework`（概念框架矩阵 / 思维导图 / 流程图，三选一）、`theme_detail`（主题详述）、`evidence_matrix`（文献证据矩阵）。

版式不是死板的左右 1:1。让版式跟随内容密度调整：图密则图为主、文密则文为主，参见 layout-library.md 里的"版式适配规则"一节。

## Step 5 · 用 python-pptx 生成 .pptx

**生成规范：**

- 幻灯片尺寸：33.87 cm × 19.05 cm（16:9 学术宽屏）。
- 所有文字框、形状、连接线均为**矢量 Shape**，保证打开后 100% 可编辑可复用。
- 流程图、研究框架图、概念框架图：用 `add_shape` + `add_connector` 写，不要用整张截图代替。
- 表格：能写成原生 `shapes.add_table` 时优先用原生表，仅在数据具体且无歧义时；纯版式型对比表（例如综述方法对比）必须原生表。
- 公式：能用 Unicode 近似就用 Unicode；复杂公式用 matplotlib 渲染为透明 PNG 后 `add_picture`。
- 引文页脚：每张引用了文献的页都必须有 8pt 灰色 GB/T 7714 完整条目，字符按"中文-微软雅黑 / 数字与拉丁字符-Times New Roman"分 run 写入。详见 [citation-style.md](references/citation-style.md)。
- 演讲词：写入 `slide.notes_slide.notes_text_frame`，详见 [speaker-notes.md](references/speaker-notes.md)。

**视觉常量**（颜色 `THEME` / 字体 `FONTS` / 版心 `LAYOUT`）默认值已在 `scripts/layout_library.py` 顶部，直接 import 使用即可；要换主题色就改这三个 dict 然后重新生成。无需为此再读其他 md。

**Step 5b · 演讲词同步生成**

每页 100–180 字（约 45–90 秒口播）；正式但自然；不照读 PPT，而是解释 / 补充 / 衔接。重要数据要给"直觉解读"。具体写法、衔接语、口播 vs 书面差异见 [speaker-notes.md](references/speaker-notes.md)。

## Step 6 · 静态预览与迭代

有 LibreOffice 就转 PDF + pdftoppm 出预览图，嵌入一个简易 HTML 给用户浏览。没有就跳过这步，直接走 Step 7。

预览到的常见问题：图缺失、文字溢出、流程图箭头乱、引文页脚被横幅压住、备注遗漏。按用户自然语言反馈（"第3页箭头太密""换墨绿色""综述地图右下角加上 Smith 2024"）改对应页代码并重出。

## Step 7 · 交付 .pptx

把最终 `.pptx` 放到约定输出位置（`output/final_presentation_cn.pptx`），并写 `output/qa_report.md` 报告：页数、引文页数、含图页数、备注覆盖率、已知遗留问题、需手工跟进项。

提醒用户：
- 所有元素可在 PowerPoint / WPS 中直接编辑；
- 演讲词在"备注"视图查看；
- Logo 占位符在每页右上角，双击替换即可；
- 引文页脚是矢量文本，可整条复制到 Word / EndNote。

# 四条路线的选用

| 用户场景 | 路线 | 论证骨架 | 标志性页 |
|---|---|---|---|
| 单篇论文/会议论文讲解 | A | question-to-evidence / problem-to-solution | 技术路线、研究框架、关键证据 3-4 页 |
| 课程报告（政策/时政/案例） | B | 背景-问题-分析-建议 | 时政图、政策卡片、数据统计卡 |
| 开题报告 | C | problem-to-plan | 研究框架、技术路线、**甘特图** |
| 文献综述 / Review | D | evidence-map | **概念框架可视化（矩阵/思维导图/流程图）**、主题详述、研究空缺 |

详细页面骨架与版式选择在各 route 文件里。**不要在主 SKILL 这里展开各路线的细节，到对应文件里读。**

# Citation Rules · 引文规范（四条路线通用）

无论走哪一条路线，只要正文出现了他人文献的观点、数据、图表，必须满足：

1. **正文内角标**：在引用的那句话末尾加 `[n]`（中英文都用方括号阿拉伯数字，与页脚条目一一对应）。
2. **页脚完整条目**：该页底端用 **8pt 浅灰** (`#888888`) 列出完整 GB/T 7714 引用，置于 `bottom_banner` 上方。中文文献用中文，英文文献保留英文原文不翻译。
3. **混合字体**：中文字符用 *微软雅黑*；数字、英文字母、符号、年份、卷期、页码、DOI 一律用 *Times New Roman*。在 python-pptx 中用多个 `run` 拼接同一段文本，逐 run 设置 `font.name`。
4. **格式默认 GB/T 7714**，示例：
   - 中文期刊：`董文鸳. 我国谷歌学术搜索研究综述[J]. 新世纪图书馆, 2011, 9: 43-45.`
   - 英文期刊：`Smith J, Doe A. Title of the paper[J]. Nature, 2024, 612(7940): 215-223.`
   - 中文会议：`张三. 文章标题[C]//会议名称. 出版地: 出版社, 2020: 12-18.`
   - 中文专著：`李四. 书名[M]. 北京: 高等教育出版社, 2019.`
5. **同页多引**：从上到下按引用顺序排列；同一文献在同一页多次引用只列一次条目。
6. **图引用**：来自他文的图，在图右下/标题处再加一行 `图来源：[3]`；同时把该 `[3]` 写入页脚条目。

完整示例（python-pptx 多 run 写法、各类型条目模板、Route D 综述海量引文的分页处理）见
[citation-style.md](references/citation-style.md)。

# Style Rules · 学术风格硬约束

- 背景白或极浅；正文深色高对比；最多一两种克制强调色。
- 一页一个核心论点；标题用"结论式标题"（说出该页的主张），不要只放章节标签。
- 证据型页采取"图占主、文为辅"的非对称版式；不要默认 1:1 分栏。
- 中文口语风格的报告语言；保留英文术语；不要堆砌形容词；不要营销腔。
- 流程图与研究框架图：节点用矩形/圆角矩形，连接线用单向箭头，配色克制；不放装饰素材。
- 表格：浅色斑马底，仅用深色描表头；不要全表加粗、不要过度框线。
- 不要把每页都堆成"标题 + 4 条 bullet + 一张图"的模板复制；用版式服务于内容。

# Output Files

```
output/
├── final_presentation_cn.pptx     ← 主交付物
├── qa_report.md                   ← 短的质量报告
├── assets/figures/                ← 入选的原图与裁切（如有）
└── asset_manifest.md              ← 图片溯源（仅在抽了原图时生成）
```

可选（仅在显式需要 / 便于校对时生成）：

```
output/ppt_outline_cn.md          ← 三级大纲（路线 / 论证 / 页面用途）
output/figure_plan.md             ← 选图理由与落点
output/ppt_script_cn_with_figures.md   ← 逐页脚本（含中文图注与口播）
output/rendered/                  ← 预览 PNG（有 LibreOffice 时）
```

# Quality Rules

- 必须产出 `.pptx`，不要止步于 markdown 大纲或脚本；
- 不编造数据、方法、文献、图细节；
- 引用过的地方必须有页脚完整条目，不允许只在正文角标而页脚空着；
- 不允许把流程图退化为整张位图截图；
- 不允许把可写成原生表格的对比表用图片代替；
- 备注区不允许大段空白；
- 不允许在普通幻灯片上塞超过 6 条 bullet。

# Fallback Rules

- 部分内容缺失：仍尽量产出可用 PPT 框架，缺数据用占位符并在 `qa_report.md` 注明；
- python-pptx 不可用：退化为产出大纲 + 图计划 + 引文条目（仍按本规范），并在报告里说明不能生成 .pptx 的原因；
- 没有 LibreOffice：跳过预览页，但仍重开 .pptx 做结构校验。

# References Index（按需读取，不要一次全开）

| 文件 | 内容 | 何时读 |
|---|---|---|
| [references/route-academic-paper.md](references/route-academic-paper.md) | Route A 学术论文路线细则 | 路线 A 时 |
| [references/route-course-report.md](references/route-course-report.md) | Route B 课程报告路线细则、时政图处理 | 路线 B 时 |
| [references/route-proposal.md](references/route-proposal.md) | Route C 开题报告路线细则、甘特图 | 路线 C 时 |
| [references/route-literature-review.md](references/route-literature-review.md) | **Route D 文献综述路线细则、概念框架可视化** | 路线 D 时 |
| [references/citation-style.md](references/citation-style.md) | GB/T 7714 引用规范、混合字体、python-pptx 多 run 写法 | **任何路线写引用时必读** |
| [references/layout-library.md](references/layout-library.md) | 版式适配规则、各 content_type 的版式叙述与默认参数 | Step 4–5 |
| [references/speaker-notes.md](references/speaker-notes.md) | 演讲词撰写规范、衔接、口播 vs 书面 | Step 5b |

`scripts/layout_library.py` 是版式实现，`scripts/route_helpers.py` 是甘特图/公式/政策卡的实现。只有在真正写 / 改 python 代码时才打开它们；阅读思考阶段全部在 references 里完成。

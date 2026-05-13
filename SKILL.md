---
name: chinese-academic-ppt
description: >
  中国大陆学生学术 PPT 全流程生成的分发器。识别用户的学术汇报场景（论文答辩、组会汇报、
  课程报告、开题报告、文献综述、综述讲解、研究路线讲解等），并把任务交给对应子技能。
  当用户说"帮我做PPT""答辩PPT""开题报告PPT""文献综述PPT""组会汇报""学术幻灯片""技术路线图"
  "示意图""流程图""概念框架图""思维导图"等时必须调用本技能，即使没有出现"学术"二字。
  本技能不直接生成内容，只负责路由：整套 PPT 走 paper2ppt（SVG→DrawingML 流水线），
  单张学术示意图走 technicalroute（文献样式检索 + AI 生图），二者皆有则按需同时调用。
---

# Chinese Academic PPT · Master Router

本技能是一个分发器，不直接生成内容。它判断用户的需求落在以下哪一类，再把工作交给对应的子技能：

| 用户意图 | 子技能 | 入口文件 |
|---|---|---|
| 生成 / 修改一整套 `.pptx` 学术幻灯片 | `CN_Spark_paper2ppt` | [CN_Spark_paper2ppt/SKILL.md](CN_Spark_paper2ppt/SKILL.md) |
| 生成单张学术示意图（技术路线 / 研究框架 / 思考脉络 / 全文流程） | `CN_Spark_technicalroute` | [CN_Spark_technicalroute/SKILL.md](CN_Spark_technicalroute/SKILL.md) |
| 两类都要（典型情况：完整 PPT 中含若干自绘图） | 同时调用两个 | 两个 SKILL.md 都读 |

## 路由判别

按以下顺序判断：

1. 用户文字里出现 **"PPT / 幻灯片 / slide / 答辩 / 汇报 / 开题 / 综述讲解 / 课程报告"** → 走 `CN_Spark_paper2ppt`。
2. 用户文字里出现 **"流程图 / 技术路线 / 研究框架 / 示意图 / 架构图 / 概念框架图 / 思维导图 / 综述地图 / 研究思路"** → 走 `CN_Spark_technicalroute`。
3. 两类词同时出现，或用户上传了论文 / 报告且要求"做成一整套含图的 PPT" → **两个都读**。
4. 用户给的是单张图片要解析或重绘 → 只走 `CN_Spark_technicalroute`。
5. 不确定时，先读 `CN_Spark_paper2ppt/SKILL.md`（这是更常见的需求）。

## 两个子技能的核心 pipeline 速记

`CN_Spark_paper2ppt`（继承自 ppt-master，加学术层）：

```
Source Document → Outline (Strategist) → Design Spec → [Image Acquisition]
   → SVG Pages (Executor Academic) → Quality Check → DrawingML (svg_to_pptx)
```

`CN_Spark_technicalroute`（AI 生成技术路线图）：

```
判定 archetype（思考路线 / 技术方法 / 全文思路） → 文献样式检索 (≥ 5 篇)
   → 风格特征抽取 → Prompt 合成 → image_gen.py (Gemini 3 Pro Image) → 嵌入 / 独立输出
```

## 联合调用时的默认顺序

当两个子技能都需要：

1. 先用 `CN_Spark_paper2ppt` 解析输入材料、生成大纲、确定哪些页面需要自绘图（典型：技术路线页、研究框架页、文献综述概念框架页）。
2. 在 paper2ppt 的 Step 5 把这些图的需求（archetype、节点要点、配色）交给 `CN_Spark_technicalroute`。
3. `CN_Spark_technicalroute` 走"文献样式检索 → image_gen.py 生图" 后返回 PNG，paper2ppt 用 `<image>` 节点嵌入对应 SVG 页面。
4. `CN_Spark_paper2ppt` 把页面 SVG 拼齐后跑 `svg_to_pptx.py` 导出原生 DrawingML PPTX，并写好引文页脚、演讲词与底部横幅。
5. **全程保持矢量与可编辑性** — 不让任何流程图退化成位图截图，文字与图形不挤一起。

## 阅读策略（节省 token）

- 进入本技能后**只读对应子技能的 `SKILL.md`**，不要一次加载全部 references。
- 子技能 `SKILL.md` 内会指明哪一份 route 文件、哪一份引文规范、哪一份版式说明该读，跟随其指引即可。
- `scripts/*.py` 是实现，**只有在真正写代码时才打开**；日常思考与对齐用 references/*.md 即可。
- ppt-master 通用规则在 `CN_Spark_paper2ppt/references/` 顶层；中文学术专属规则在 `CN_Spark_paper2ppt/references/academic/`。

## 学术性硬约束（无论走哪条路线都必须满足）

1. 输出必须是**可编辑可复用的 `.pptx`**：矢量 Shape + 原生表格 + 原生连接线，不允许把流程图退化为整张截图。
2. 任何论点、数据、图表如来源于他人文献，必须**在正文出现处加文内标注**（`[1]` / `[作者, 年份]`），并在该页**底端用灰色 8pt 列出完整 GB/T 7714 引用**。中文文献用中文，英文文献用英文；中文字符用 *微软雅黑*，数字与拉丁字符用 *Times New Roman*。
3. 演讲词写入备注区，按学术口语规范（见子技能里的 speaker-notes 章节）。
4. 不编造未在材料中出现的数据、机构、文献。
5. 自绘技术路线 / 研究框架图禁止退化为位图占位；走 `CN_Spark_technicalroute` 的 AI 生图链路，且嵌入时保留为 `<image>` 节点而非整页截图。

子技能会在自己的 SKILL.md 里复述并细化这些约束，本路由不重复展开。

## 文件树速查

```
CN_Academic_PPT_Spark_Skill/
├── SKILL.md                            ← 本文件（路由）
├── README.md                           ← 安装与使用说明
├── .claude-plugin/                     ← Claude marketplace 元数据
├── CN_Spark_paper2ppt/                 ← 完整 PPT 生成（SVG→DrawingML）
│   ├── SKILL.md                        ← 7 步主流水线 + 学术 4 路线
│   ├── templates/                      ← 复用 ppt-master 的版式 / 图表 / 图标库
│   │   ├── layouts/                    ← 含 academic_defense / medical_university 等
│   │   ├── charts/                     ← 70+ 图表 / 信息图模板
│   │   └── icons/                      ← tabler / phosphor / simple-icons / chunk
│   ├── scripts/                        ← 复用 ppt-master 的 svg_to_pptx / finalize_svg / image_gen / ...
│   ├── workflows/                      ← topic-research / create-template / resume-execute / verify-charts / ...
│   └── references/
│       ├── strategist.md / executor-base.md / ...  ← 通用（继承 ppt-master）
│       └── academic/                   ← 中文学术专属
│           ├── executor-academic.md    ← ⭐ 学术执行器
│           ├── citation-style.md       ← GB/T 7714 + tspan 混合字体
│           ├── speaker-notes.md        ← 演讲词规范
│           ├── layout-library.md       ← 版式适配
│           ├── route-academic-paper.md ← Route A
│           ├── route-course-report.md  ← Route B
│           ├── route-proposal.md       ← Route C
│           └── route-literature-review.md ← Route D
└── CN_Spark_technicalroute/            ← 单张学术示意图（AI 生图）
    ├── SKILL.md                        ← 6 步：判类 → 检索 → 风格画像 → prompt → 生图 → 嵌入
    ├── references/
    │   ├── archetype-thinking.md       ← 思考路线类（4 panel + 红色横幅）
    │   ├── archetype-method.md         ← 技术方法类（核心思想 + Step + 假设）
    │   ├── archetype-workflow.md       ← 全文思路类（Data → Methods 横向 pipeline）
    │   ├── image-prompt-templates.md   ← 三类英文骨架 prompt + negative prompt
    │   ├── seed_sites.json             ← 学术站点检索 URL 模板
    │   └── seed_urls.md                ← 站点适配与降级说明
    └── scripts/
        ├── literature_search.py        ← 检索计划 + manifest 记录 + 离线模式
        └── generate_route_image.py     ← prompt 合成 + 调 image_gen.py + 嵌入 SVG
```

判别完毕后，跳到对应子技能的 SKILL.md 继续。

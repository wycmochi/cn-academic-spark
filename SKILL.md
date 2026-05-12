---
name: chinese-academic-ppt
description: >
  中国大陆学生学术 PPT 全流程生成的分发器。识别用户的学术汇报场景（论文答辩、组会汇报、
  课程报告、开题报告、文献综述、综述讲解、研究路线讲解等），并把任务交给对应子技能。
  当用户说"帮我做PPT""答辩PPT""开题报告PPT""文献综述PPT""组会汇报""学术幻灯片""技术路线图"
  "示意图""流程图""概念框架图""思维导图"等时必须调用本技能，即使没有出现"学术"二字。
  本技能不直接生成内容，只负责路由：整套 PPT 走 paper2ppt，单张学术图走 workflow，
  二者皆有则按需同时调用。
---

# Chinese Academic PPT · Master Router

本技能是一个分发器，不直接生成内容。它判断用户的需求落在以下哪一类，再把工作交给对应的子技能：

| 用户意图 | 子技能 | 入口文件 |
|---|---|---|
| 生成 / 修改一整套 `.pptx` 学术幻灯片 | `CN_Spark_paper2ppt` | [CN_Spark_paper2ppt/SKILL.md](CN_Spark_paper2ppt/SKILL.md) |
| 生成 / 解析单个学术示意图（技术路线、研究框架、概念图、综述地图、思维导图） | `CN_Spark_workflow` | [CN_Spark_workflow/SKILL.md](CN_Spark_workflow/SKILL.md) |
| 两类都要（典型情况：完整PPT中含若干自绘图） | 同时调用两个 | 两个 SKILL.md 都读 |

## 路由判别

按以下顺序判断：

1. 用户文字里出现 **"PPT / 幻灯片 / slide / 答辩 / 汇报 / 开题 / 综述讲解 / 课程报告"** → 走 `CN_Spark_paper2ppt`。
2. 用户文字里出现 **"流程图 / 技术路线 / 研究框架 / 示意图 / 架构图 / 概念框架图 / 思维导图 / 综述地图"** → 走 `CN_Spark_workflow`。
3. 两类词同时出现，或用户上传了论文/报告且要求"做成一整套含图的 PPT" → **两个都读**。
4. 用户给的是单张图片要解析或重绘 → 只走 `CN_Spark_workflow`。
5. 不确定时，先读 `CN_Spark_paper2ppt/SKILL.md`（这是更常见的需求）。

## 联合调用时的默认顺序

当两个子技能都需要：

1. 先用 `CN_Spark_paper2ppt` 解析输入材料、生成大纲、确定哪些页面需要自绘图（典型如：技术路线页、研究框架页、文献综述的概念框架页）。
2. 把这些图的需求（节点、关系、风格）交给 `CN_Spark_workflow`，得到可编辑的 SVG/PNG/原生形状脚本。
3. `CN_Spark_paper2ppt` 把资产嵌入对应页面，并用 python-pptx 写好引文页脚、演讲词与底部横幅。
4. 全程保持矢量与可编辑性 — 不要让自绘图退化成位图截图。

## 阅读策略（节省 token）

- 进入本技能后**只读对应子技能的 `SKILL.md`**，不要一次加载全部 references。
- 子技能 `SKILL.md` 内会指明哪一份 route 文件、哪一份引文规范、哪一份版式说明该读，跟随其指引即可。
- `scripts/*.py` 是实现，**只有在真正写代码时才打开**；日常思考与对齐用 references/*.md 即可。

## 学术性硬约束（无论走哪条路线都必须满足）

1. 输出必须是**可编辑可复用的 `.pptx`**：矢量 Shape + 原生表格 + 原生连接线，不允许把流程图退化为整张截图。
2. 任何论点、数据、图表如来源于他人文献，必须**在正文出现处加文内标注（[1] / [作者, 年份]）**，并在该页**底端用灰色 8pt 列出完整 GB/T 7714 引用**。中文文献用中文，英文文献用英文；中文字符用 *微软雅黑*，数字与拉丁字符用 *Times New Roman*。
3. 演讲词写入备注区，按学术口语规范（见子技能里的 speaker-notes 章节）。
4. 不编造未在材料中出现的数据、机构、文献。

子技能会在自己的 SKILL.md 里复述并细化这些约束，本路由不重复展开。

## 文件树速查

```
CN_Academic_PPT_Spark_Skill/
├── SKILL.md                          ← 本文件（路由）
├── CN_Spark_paper2ppt/               ← 完整 PPT 生成
│   ├── SKILL.md                      ← 4 条路线 + 引文 + 版式 + 演讲词的主干
│   ├── references/                   ← 路线规则、引文样式、版式与演讲词指南
│   └── scripts/                      ← 实际 python-pptx 实现
└── CN_Spark_workflow/                ← 单图（流程图/框架图/概念图）生成与解析
    ├── SKILL.md
    ├── references/
    └── scripts/
```

判别完毕后，跳到对应子技能的 SKILL.md 继续。

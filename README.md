# CN-Academic-Spark

面向中文学术汇报场景的 Claude / Codex skill 集合。核心目标是让模型**真正理解学术内容并把它讲清楚**，而不只是机械生成幻灯片。

仓库现在是一个 **Claude marketplace 捆绑（bundle）**，市场里统一显示为 `cn-academic-spark`。`skills/` 下两个**相互独立、可分别调用**的子 skill：

| 子 skill (frontmatter `name`) | 目录 | 用途 | 入口 SKILL.md |
|---|---|---|---|
| `cn-academic-spark-ppt-engine` | `skills/CN_Spark_paper2ppt/` | 完整中文学术 `.pptx` 生成 | [skills/CN_Spark_paper2ppt/SKILL.md](skills/CN_Spark_paper2ppt/SKILL.md) |
| `cn-academic-spark-technicalroute-engine` | `skills/CN_Spark_technicalroute/` | 单张学术示意图（技术路线 / 研究框架 / 思考脉络 / 全文流程） | [skills/CN_Spark_technicalroute/SKILL.md](skills/CN_Spark_technicalroute/SKILL.md) |

> 1.1.0 起 marketplace 只注册一个 plugin（`cn-academic-spark`），`source: "./"`，子 skill 通过 `skills/<name>/` 目录被 Claude Code 自然发现。没有"路由 skill"，没有额外的展示名，IDE 直接按子 skill 自己的 frontmatter description 触发。

## 两个 skill 的关系（融合 + 各自独立）

- **PPT engine** 内部串入了 TechnicalRoute engine 作为子流程：当 Strategist 判定某页是技术路线 / 研究框架 / 思考脉络 / 全文流程图时，PPT engine 的 **Step 5.5** 会自动驱动 TechnicalRoute engine 的 8 步 contract-first 流水线，确保该页是**可编辑学术图**而不是位图截图。
- **TechnicalRoute engine** 同时完全可独立调用 —— 用户只要一张图、不要 PPT 时，只用这一个 skill 就够了。

## 我应该让 Claude 调哪一个？

按以下顺序判断：

1. 用户文字里出现 **"PPT / 幻灯片 / slide / 答辩 / 汇报 / 开题 / 综述讲解 / 课程报告"** → 走 `cn-academic-spark-ppt-engine`。
2. 用户文字里出现 **"流程图 / 技术路线 / 研究框架 / 示意图 / 架构图 / 概念框架图 / 思维导图 / 综述地图 / 研究思路"**，且**不要 PPT** → 走 `cn-academic-spark-technicalroute-engine`。
3. 两类词同时出现，或用户上传了论文 / 报告且要求"做成一整套含图的 PPT" → 调 PPT engine 一个就够，它会在 Step 5.5 自动调 TR engine。
4. 用户给的是单张图片要解析或重绘 → 只走 TR engine。

适合场景：

- 论文答辩 / journal club / 组会汇报
- 开题报告 / 课程报告 / 文献综述讲解
- 把研究思路转成"结构化、可讲清楚、矢量可编辑"的 PPT 与图示
- 给单篇论文 / 综述 / 课题做一张高质量"全文思路图"或"研究框架图"

---

## Install

```bash
git clone https://github.com/wycmochi/CN-Academic-PPT-Skills.git
cd CN-Academic-PPT-Skills
```

### Claude Code（推荐）

**方式 A · 捆绑安装（两个 skill 都装，最常用）**

```bash
# macOS / Linux
mkdir -p ~/.claude/skills
cp -R skills/CN_Spark_paper2ppt        ~/.claude/skills/
cp -R skills/CN_Spark_technicalroute   ~/.claude/skills/

# Windows (PowerShell)
mkdir -Force $HOME\.claude\skills
Copy-Item -Recurse skills\CN_Spark_paper2ppt      $HOME\.claude\skills\
Copy-Item -Recurse skills\CN_Spark_technicalroute $HOME\.claude\skills\
```

**方式 B · 只装其中一个**

只想做 PPT：

```bash
cp -R skills/CN_Spark_paper2ppt ~/.claude/skills/
```

只想做单张技术路线图：

```bash
cp -R skills/CN_Spark_technicalroute ~/.claude/skills/
```

> ⚠️ 单独安装 TR engine 时，它的 `scripts/generate_route_image.py` 默认会找同级目录下的 `CN_Spark_paper2ppt/scripts/image_gen.py` 作为生图后端。如果你**只装了** TR engine，请设置以下任一环境变量：
>
> ```bash
> export IMAGE_GEN_PATH=/abs/path/to/image_gen.py            # 直接指向脚本
> # 或者
> export PAPER2PPT_ROOT=/abs/path/to/CN_Spark_paper2ppt      # 指向 PPT engine 根
> ```

之后重启 Claude Code 会话即可。触发词示例：

```text
帮我把这篇论文做成中文答辩 PPT，里面要含一张全文研究思路的技术路线图。
请根据这段研究设计画一个思考路线类的研究框架图。
帮我把这张论文里的研究框架做成可编辑的矢量示意图。
```

### Claude marketplace（可选）

仓库根 `.claude-plugin/marketplace.json` 已经把整套捆绑注册成**一个** plugin：

| Plugin name | 类别 | source |
|---|---|---|
| `cn-academic-spark` | `academic` | `./`（整个仓库） |

1. Claude → Customize → Connectors → GitHub Integration，把本仓库授权连上；
2. Skills / Plugins 市场搜 `cn-academic-spark`；
3. 安装后 `skills/` 下的两个子 skill 会一起被发现。

### Codex

```bash
mkdir -p ~/.codex/skills
cp -R skills/CN_Spark_paper2ppt        ~/.codex/skills/
cp -R skills/CN_Spark_technicalroute   ~/.codex/skills/
```

### 其他 agent / IDE

最小可迁移单元 = **一个子 skill 目录**（`skills/CN_Spark_paper2ppt/` 或 `skills/CN_Spark_technicalroute/`，含 `SKILL.md` + `references/` + `scripts/` + 必要时 `templates/` / `assets/` / `workflows/`）。把它整体复制到目标工具的 prompt 库 / agent 配置目录即可。`scripts/*.py` 仅在工具确实会执行 shell 命令时才需要挂载。

---

## 依赖与运行环境

PPT engine 复用 Python 工具链，需要 Python ≥ 3.10：

```bash
cd skills/CN_Spark_paper2ppt
pip install -r requirements.txt
cp .env.example .env   # 然后填 GEMINI_API_KEY / OPENAI_API_KEY 等
```

TechnicalRoute engine 默认调 PPT engine 的 `scripts/image_gen.py` 做生图，默认 backend = **Gemini 3 Pro Image（nano banana pro）**。`.env` 中至少配 `IMAGE_BACKEND=gemini` 与 `GEMINI_API_KEY=...`。备选后端：Qwen Image 2.0 Pro、OpenAI gpt-image-2、Volcengine Seedream，全部通过环境变量切换。

---

## Skill Overview

### `cn-academic-spark-ppt-engine`（PPT engine）

面向"完整汇报"。

- 输入：论文 PDF / DOCX、报告、读书笔记、综述提纲、`input/source.md`、对话粘贴文本、用户 `.pptx` 模板等任意一种或组合。
- 流程（7 步主流水线 + Step 5.5 融合段，详见 [skills/CN_Spark_paper2ppt/SKILL.md](skills/CN_Spark_paper2ppt/SKILL.md)）：
  1. 源材料 → Markdown（PyMuPDF / pandoc / docx）
  2. 项目初始化（`project_manager.py init`）
  3. 模板选择（学院风默认 `academic_defense`）
  4. Strategist 八项确认 + 路线分流（Route A/B/C/D）+ 大纲 → `design_spec.md` / `spec_lock.md`
  5. 图片获取（用户 / AI / web 三路）
  5.5. **内联 TechnicalRoute 子流程**（融合段）：所有"自绘示意图"自动转给 TR engine，按 contract-first 8 步出可编辑图
  6. Executor 逐页生成 SVG（`executor-academic.md`），每页含底部横幅 + 引文页脚 + 演讲词
  7. 后处理 `finalize_svg.py` → 导出 `svg_to_pptx.py` 得原生 DrawingML `.pptx`
- 学术硬约束（强制）：
  - GB/T 7714 引文页脚 + 中英文混合字体 tspan
  - 备注区演讲词（每页 100–180 字）
  - 底部横幅一句话主旨
  - 论证主轴优先于章节顺序
  - 不编造未在材料中出现的数据 / 文献

### `cn-academic-spark-technicalroute-engine`（TechnicalRoute engine）

面向"单张学术示意图"。

- 三类拓扑（详见 [skills/CN_Spark_technicalroute/SKILL.md](skills/CN_Spark_technicalroute/SKILL.md)）：
  - **思考路线类** — 研究背景 / 问题 / 理论 / 意义（"为什么做"）
  - **技术方法类** — 单模型的核心思想 + Step + 公式 + 假设
  - **全文思路类** — Data → Methods → Results 横向 ML pipeline
- 流程（contract → audit，8 步）：
  1. **Diagram Contract**（论证 + panel 映射 + 术语保留）
  2. `content.yaml`（字段必须派生自 contract）
  3. 公开学术文献检索 (≥ 5 篇) + Custom_gallery 同学科参考图
  4. 评估检索质量 → 决定 `literature` / `offline` / `atlas_only` 模式
  5. 风格特征抽取（panel 数 / 配色 / 图标密度 / 流向）→ `style_profile.md`
  6. Prompt 合成 → `prompt.md`
  7. 调 `image_gen.py`（Gemini / Qwen 等）；优先尝试 `assets/templates/` 模板装配矢量 SVG
  8. QA Audit（hard + soft + reviewer-risk 清单）
- 输出：可编辑 SVG（命中模板时）或 PNG + `_prompt.txt` 复现记录 + `style_refs/manifest.json` 文献元信息

---

## 联合调用示例

```text
帮我把这篇 PDF 做成 15 分钟的答辩 PPT，第 6 页要一张全文思路类的技术路线图。
```

执行顺序：

1. PPT engine 解析 PDF → 出大纲 → Strategist 八项确认 → 在 `design_spec.md §IX` 中把 P6 标记为"技术路线（embed_technicalroute: true）"；
2. PPT engine 进入 Step 5.5：把 P6 的内容要点（archetype + 节点 + 主题色 + glossary）传给 TR engine；
3. TR engine 走 contract → content.yaml → 检索 → prompt → image_gen → audit 8 步，返回可编辑 SVG 或 PNG；
4. PPT engine 把返回结果嵌入 `svg_output/06_research_workflow.svg`，并把 TR engine 返回的 reference 文献合并到该页引文页脚；
5. 后续 SVG → `svg_to_pptx` → 最终 `.pptx`。

---

## Repository Structure

```text
CN-Academic-Spark/
├── README.md                           ← 本文件（也是入口；根目录已无 SKILL.md）
├── LICENSE
├── updateCLI.md                        ← Git 上传指南
├── .claude-plugin/
│   └── marketplace.json                ← 注册单 plugin: cn-academic-spark
└── skills/
    ├── CN_Spark_paper2ppt/             ← cn-academic-spark-ppt-engine
    │   ├── SKILL.md                    ← 7 + 1 步主流水线（含 Step 5.5 融合段）
    │   ├── templates/                  ← layouts / charts / icons
    │   ├── scripts/                    ← svg_to_pptx / finalize_svg / image_gen / ...
    │   ├── workflows/
    │   ├── references/
    │   │   ├── *.md                    ← 通用 strategist / executor / image / animation ...
    │   │   └── academic/               ← ⭐ 中文学术专属
    │   ├── requirements.txt
    │   └── .env.example
    └── CN_Spark_technicalroute/        ← cn-academic-spark-technicalroute-engine
        ├── SKILL.md                    ← 8 步 contract → audit
        ├── assets/
        │   ├── templates/              ← 可编辑 SVG 模板（首选装配源）
        │   ├── Custom_gallery/         ← 各学科真实学术图风格参考
        │   ├── design_spec_reference.md
        │   └── spec_lock_reference.md
        ├── references/
        │   ├── diagram-contract.md
        │   ├── archetype-{thinking,method,workflow}.md
        │   ├── content-schema.md / shape-recipes.md / color-typography.md
        │   ├── handling-no-references.md
        │   ├── image-prompt-templates.md
        │   ├── seed_sites.json / seed_urls.md
        │   └── qa-checklist.md
        └── scripts/
            ├── literature_search.py
            ├── content_schema.py
            └── generate_route_image.py ← 支持 IMAGE_GEN_PATH / PAPER2PPT_ROOT 覆盖
```

---

## Notes

- 本仓库强调**学术表达质量**，不只追求自动化生成。
- 公式、图示、框架、引文、speaker notes 都围绕"让学术内容更容易被理解和讲述"来设计。
- 字体、主题色、版心等默认样式可在 `skills/CN_Spark_paper2ppt/templates/layouts/<chosen>/design_spec.md` 中改。
- 想新增一份"实验室专属模板"，参见 [skills/CN_Spark_paper2ppt/workflows/create-template.md](skills/CN_Spark_paper2ppt/workflows/create-template.md)。

---

## Acknowledgement

本仓库站在两位前辈的肩膀上：

- **[Yuan1z0825](https://github.com/Yuan1z0825) · `nature-skills`** — 提供了"论文→PPT"分流与 GB/T 7714 引文等中文学术细节的最初灵感；本仓库的 marketplace 单 plugin + `skills/` 子目录布局也参考了该项目。
- **`ppt-master` 项目作者** — 提供了"Source → Outline → SVG → DrawingML"的整套工程化流水线（templates / scripts / strategist / executor / svg_to_pptx）。PPT engine 的 `templates/` `scripts/` `workflows/` 与通用 `references/*.md` 主要参考并复用自该项目，并按中文学术场景叠加了 `references/academic/` 学术执行器与四路线版式。

在这两份工作之上，本仓库进一步做了：

- **中文学术执行器**（[`executor-academic.md`](skills/CN_Spark_paper2ppt/references/academic/executor-academic.md)）—— 底部横幅 / 引文页脚 / 模块化公式页 / 矩阵证据表的 SVG 写法。
- **四路线版式分流** —— Route A 学术论文 / Route B 课程报告 / Route C 开题 / Route D 综述。
- **技术路线 contract-first 链路** —— TR engine 的核心：先写 Diagram Contract，再走文献检索 + Custom_gallery 同学科参考 + 矢量模板装配 + AI 生图，输出**优先矢量可编辑**的学术示意图。
- **PPT engine ↔ TR engine 融合段**（PPT engine Step 5.5）—— 一份学术 deck 中所有自绘示意图自动统一走 contract-first 链路，保证矢量与学术性。
- **GB/T 7714 引文 + 混合字体 SVG `<tspan>` 写法** —— 中文走微软雅黑、数字 / 拉丁字符走 Times New Roman 的硬约束在 SVG 层面落地。

目标不是简单复制，而是在原有启发上把中文学术 PPT 的理解、组织和表达做得更细、更稳、更可复用。

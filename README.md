# CN-Academic-PPT-Skills

面向中文学术汇报场景的可复用 Claude / Codex skill 集合。核心目标是让模型**真正理解学术内容并把它讲清楚**，而不只是机械生成幻灯片。

仓库由两个子 skill 组成：

| 子 skill | 角色 | 流水线 |
|---|---|---|
| `CN_Spark_paper2ppt` | 把整篇论文 / 报告 / 综述 → 一整套中文学术 `.pptx` | `Source → Outline → SVG → DrawingML` |
| `CN_Spark_technicalroute` | 把研究思路 → 一张高质量学术示意图（技术路线 / 研究框架 / 思考脉络） | `判类 → 文献样式检索 → Prompt → AI 生图 → 嵌入` |

适合：
- 论文答辩 / journal club / 组会汇报
- 开题报告 / 课程报告 / 文献综述讲解
- 把学术内容转化为**结构化、可讲清楚、可矢量编辑**的 PPT 与图示

---

## Install

仓库根目录（`CN-Academic-PPT-Skills/`）已经包含 Claude marketplace 与 Codex 可识别的目录结构。下面按 IDE 分别给最短安装命令。请把 `<repo>` 替换成你 `git clone` 后的本地路径。

```bash
git clone https://github.com/wycmochi/CN-Academic-PPT-Skills.git
cd CN-Academic-PPT-Skills
```

### Claude Code（推荐）

把整个仓库放到 `~/.claude/skills/` 即可被 Claude Code 扫描到。**目录名必须是 `CN-Academic-PPT-Skills`**，路由 `SKILL.md` 在根目录。

```bash
# macOS / Linux
mkdir -p ~/.claude/skills
cp -R . ~/.claude/skills/CN-Academic-PPT-Skills

# Windows (PowerShell)
mkdir -Force $HOME\.claude\skills
Copy-Item -Recurse . $HOME\.claude\skills\CN-Academic-PPT-Skills
```

如果你只要其中一个子 skill，也可以单独安装：

```bash
cp -R CN_Spark_paper2ppt        ~/.claude/skills/
cp -R CN_Spark_technicalroute   ~/.claude/skills/
```

之后重启 Claude Code 会话即可。触发方式：

```text
帮我把这篇论文做成中文答辩 PPT，里面要含一张全文研究思路的技术路线图。
请根据这段研究设计画一个思考路线类的研究框架图。
```

### Claude marketplace（可选）

仓库根有 `.claude-plugin/plugin.json` 和 `marketplace.json`，可直接以仓库 URL 作为 plugin source：

1. Claude → Customize → Connectors → GitHub Integration，把本仓库授权连上；
2. Skills / Plugins 市场搜 `cn-academic-ppt-skills`；
3. 安装即可。

> 搜不到时，关键词也可以是 `paper2ppt` / `chinese academic` / `technicalroute`。

### Codex

```bash
mkdir -p ~/.codex/skills
cp -R . ~/.codex/skills/CN-Academic-PPT-Skills
```

Codex 默认会扫描 `~/.codex/skills/<name>/SKILL.md`。和 Claude Code 一样，你也可以只放子 skill：

```bash
cp -R CN_Spark_paper2ppt        ~/.codex/skills/
cp -R CN_Spark_technicalroute   ~/.codex/skills/
```

### 其他 agent / IDE

最小可迁移单元 = **一个子 skill 目录**（含 `SKILL.md` + `references/` + `scripts/` + 必要时 `templates/` / `workflows/`）。把它整体复制到目标工具的 prompt 库 / agent 配置目录即可。`scripts/*.py` 仅在工具确实会执行 shell 命令时才需要挂载。

---

## 依赖与运行环境

`CN_Spark_paper2ppt` 复用了 ppt-master 的脚本栈，需要 Python ≥ 3.10 与若干第三方库（python-pptx / lxml / Pillow / PyMuPDF 等）：

```bash
cd CN_Spark_paper2ppt
pip install -r requirements.txt
cp .env.example .env   # 然后填 GEMINI_API_KEY / OPENAI_API_KEY 等
```

`CN_Spark_technicalroute` 默认调用 `CN_Spark_paper2ppt/scripts/image_gen.py`（多后端生图），默认 backend = **Gemini 3 Pro Image（nano banana pro）**。`.env` 中至少配 `IMAGE_BACKEND=gemini` 与 `GEMINI_API_KEY=...`。备选后端：Qwen Image 2.0 Pro、OpenAI gpt-image-2、Volcengine Seedream，全部通过环境变量切换。

---

## Skill Overview

### `CN_Spark_paper2ppt`

面向"完整汇报"。

- 输入：论文 PDF / DOCX、报告、读书笔记、综述提纲、`input/source.md`、对话粘贴文本、用户 `.pptx` 模板等任意一种或组合。
- 流程（7 步，详见 [CN_Spark_paper2ppt/SKILL.md](CN_Spark_paper2ppt/SKILL.md)）：
  1. 源材料 → Markdown（PyMuPDF / pandoc / docx）
  2. 项目初始化（`project_manager.py init`）
  3. 模板选择（学院风默认 `academic_defense`）
  4. Strategist 八项确认 + 路线分流（Route A/B/C/D）+ 大纲 → `design_spec.md` / `spec_lock.md`
  5. 图片获取（用户 / AI / web 三路）
  6. Executor 逐页生成 SVG（用 `executor-academic.md`），每页含底部横幅 + 引文页脚 + 演讲词
  7. 后处理 `finalize_svg.py` → 导出 `svg_to_pptx.py` 得原生 DrawingML `.pptx`
- 学术硬约束（强制满足）：
  - GB/T 7714 引文页脚 + 中英文混合字体 tspan
  - 备注区演讲词（每页 100–180 字）
  - 底部横幅一句话主旨
  - 论证主轴优先于章节顺序
  - 不编造未在材料中出现的数据 / 文献

### `CN_Spark_technicalroute`

面向"单张学术示意图"。

- 三类拓扑（详见 [CN_Spark_technicalroute/SKILL.md](CN_Spark_technicalroute/SKILL.md)）：
  - **思考路线类** — 研究背景 / 问题 / 理论 / 意义；4 panel + 红色横幅承载核心问题
  - **技术方法类** — 单模型的核心思想 + Step + 公式 + 假设；左中右横向 + 底部 3 假设卡
  - **全文思路类** — 数据 → 预处理 → 提取 → 方法的横向 ML pipeline + 多层圆柱体 + SHAP
- 流程（6 步）：
  1. 类别判定 + 内容要点收集（`content.yaml`）
  2. **从公开学术文献中检索 ≥ 5 张同主题技术路线 / 框架图**（`seed_sites.json` 驱动，IDE 用 `WebSearch` + `WebFetch`；无网络时降级为用户上传 ≥ 3 张参考图）
  3. 风格特征抽取（panel 数 / 配色 / 图标密度 / 流向）→ `style_profile.md`
  4. Prompt 合成（英文骨架 + 中文 content 块 + negative）→ `prompt.md`
  5. 调 `image_gen.py`（默认 Gemini 3 Pro Image，参考图作为风格 anchor）
  6. 验收 → 可选嵌入 paper2ppt 某一页 SVG
- 输出：`.png` 主图 + `_prompt.txt` 复现记录 + `style_refs/manifest.json` 文献元信息。

---

## 联合调用

最常见的场景：一份论文 → 整套中文学术 PPT，其中第 6 页是"全文研究思路"图。

```text
帮我把这篇 PDF 做成 15 分钟的答辩 PPT，第 6 页要一张全文思路类的技术路线图。
```

执行顺序：

1. `CN_Spark_paper2ppt` 解析 PDF → 出大纲 → Strategist 八项确认 → 在 `design_spec.md §IX` 中把 P6 标记为"技术路线，需要调 technicalroute"；
2. 进入 P6 时 `CN_Spark_paper2ppt` 把内容要点（archetype + 节点 + 主题色）传给 `CN_Spark_technicalroute`；
3. `CN_Spark_technicalroute` 走"文献检索 → prompt 合成 → image_gen.py" 得 PNG；
4. 回到 `CN_Spark_paper2ppt` 用 `<image>` 标签把 PNG 嵌入 `svg_output/06_research_workflow.svg`；
5. 后续 SVG → svg_to_pptx → 最终 `.pptx`。

---

## Repository Structure

```text
CN-Academic-PPT-Skills/
├── SKILL.md                      ← 路由
├── README.md
├── LICENSE
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── CN_Spark_paper2ppt/           ← 完整 PPT 生成
│   ├── SKILL.md
│   ├── templates/                ← layouts / charts / icons（继承 ppt-master）
│   ├── scripts/                  ← svg_to_pptx / finalize_svg / image_gen / ...
│   ├── workflows/                ← topic-research / create-template / verify-charts / ...
│   ├── references/
│   │   ├── *.md                  ← 通用 strategist / executor / image / animation 等
│   │   └── academic/             ← ⭐ 中文学术专属
│   ├── requirements.txt
│   └── .env.example
└── CN_Spark_technicalroute/      ← 单图 AI 生图
    ├── SKILL.md
    ├── references/
    │   ├── archetype-thinking.md
    │   ├── archetype-method.md
    │   ├── archetype-workflow.md
    │   ├── image-prompt-templates.md
    │   ├── seed_sites.json
    │   └── seed_urls.md
    └── scripts/
        ├── literature_search.py
        └── generate_route_image.py
```

---

## Notes

- 本仓库强调**学术表达质量**，不是只追求自动化生成。
- 公式、图示、框架、引文、speaker notes 都围绕"让学术内容更容易被理解和讲述"来设计。
- 字体、主题色、版心等默认样式可在 `CN_Spark_paper2ppt/templates/layouts/<chosen>/design_spec.md` 中改。
- 想新增一份"实验室专属模板"，参见 [CN_Spark_paper2ppt/workflows/create-template.md](CN_Spark_paper2ppt/workflows/create-template.md)。

---

## Acknowledgement

本仓库站在两位前辈的肩膀上：

- **[Yuan1z0825](https://github.com/Yuan1z0825) · `nature-skills`** — 提供了"论文→PPT"分流与 GB/T 7714 引文等中文学术细节的最初灵感。
- **`ppt-master` 项目作者** — 提供了"Source → Outline → SVG → DrawingML"的整套工程化流水线（templates / scripts / strategist / executor / svg_to_pptx）。`CN_Spark_paper2ppt` 的 `templates/` `scripts/` `workflows/` 与通用 `references/*.md` 主要参考并复用自该项目，并按中文学术场景叠加了 `references/academic/` 学术执行器与四路线版式。

在这两份工作之上，本仓库进一步做了：

- **中文学术执行器**（[`executor-academic.md`](CN_Spark_paper2ppt/references/academic/executor-academic.md)）—— 底部横幅 / 引文页脚 / 模块化公式页 / 矩阵证据表的 SVG 写法。
- **四路线版式分流** —— Route A 学术论文 / Route B 课程报告 / Route C 开题 / Route D 综述。
- **技术路线 AI 生图链路** —— `CN_Spark_technicalroute` 区别于 ppt-master 的核心亮点：先从公开文献检索同主题 ≥ 5 张技术路线图作风格 anchor，再用 Gemini 3 Pro Image / Qwen Image 2.0 注入内容生成结构化学术 infographic。
- **GB/T 7714 引文 + 混合字体 SVG `<tspan>` 写法** —— 中文走微软雅黑、数字 / 拉丁字符走 Times New Roman 的硬约束在 SVG 层面落地。

目标不是简单复制，而是在原有启发上把中文学术 PPT 的理解、组织和表达做得更细、更稳、更可复用。

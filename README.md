# CN-Academic-Spark

CN-Academic-Spark 是一个面向中文学术汇报场景的 Codex skill 仓库。当前仓库只包含一个核心 skill：`cn-academic-spark-ppt-engine`，用于把论文、开题材料、课程报告、文献综述等学术材料转换为可编辑的中文学术 `.pptx`。

它不是通用的“文字转 PPT”提示词集合，而是一套包含流程规则、模板库、技术路线图模块、SVG 到 PPTX 脚本、论文图片 / 表格 / 公式处理约束的学术 PPT 生成工作流。

## 产品构成

| 组件 | 位置 | 作用 |
|---|---|---|
| 核心 skill | `skills/CN_Spark_paper2ppt/` | 学术 PPT 生成主入口，包含 source 解析、模板选择、页面规划、SVG 生成和 PPTX 导出流程。 |
| 学术规则 | `references/academic/` | 论文类型判断、中文学术标题、引用页脚、演讲备注、不同汇报场景的章节组织规则。 |
| 技术路线图模块 | `references/technicalroute/`、`templates/technicalroute/`、`scripts/technicalroute/` | 在同一个 skill 内完成研究路线图 / 框架图制作，包含模板可编辑版和 AI 参考图版。 |
| 模板与图表资源 | `templates/` | PPT 页面模板、图表模板、图标库、技术路线图 SVG skeleton 与 Custom_gallery。 |
| 工具脚本 | `scripts/` | PDF / Word / PPT / Excel 转 Markdown、模板导入、公式渲染、SVG 检查、SVG 转 PPTX 等。 |

## 产品亮点

| 常见产品做法 | CN-Academic-Spark 的方式 |
|---|---|
| 主要生成普通商务 PPT，学术论文结构需要用户自己改。 | 内置中文学术场景规则，区分论文汇报、开题、文献综述、课程 / 政策报告等路线。 |
| 技术路线图通常只是简单流程图，或直接生成不可编辑截图。 | 内置 TechnicalRoute 流程，同一研究路线图生成两页：模板可编辑 SVG 版 + AI 参考图版。 |
| AI 生图缺少可控参考，风格容易漂移。 | AI 技术路线图可参考 `Custom_gallery` 中的自定义风格对象，并结合论文内容生成。 |
| 用户上传 PPT 模板后，只能套色或截图复用。 | 提供 PPTX 模板导入流程，识别普通编辑页可编辑元素、主题色、字体、标题位置、logo / 校名 / 学院名等。 |
| 模板母版中的固定元素容易被重复识别，导致叠加。 | 明确区分 slide-local 可编辑元素与 master/layout 锁定元素，避免重复叠加固定文字、图标和装饰。 |
| 生成页经常缺少论文图、公式或证据对象。 | 设有高优先级视觉覆盖规则：除技术路线、总结、规划启示页外，每页至少包含图片、复杂表格截图、图表或公式。 |
| 中文、英文、数字混排容易字体混乱。 | 执行规则要求中文 / Latin / 数字使用 `<tspan>` 分段，并保留 GB/T 7714 引用页脚。 |
| 输出多为截图或半可编辑对象。 | 目标输出是真实 `.pptx`，先生成 SVG，再转换为 DrawingML，尽量保留可编辑结构。 |

## 安装

推荐先安装到 Codex 的 skills 目录。依赖下载只需要准备 Python 环境；后续脚本依赖会按 `requirements.txt` 安装，不需要手工逐个查找包。

### 1. 克隆仓库

```bash
git clone <this-repository-url>
cd CN_Academic_PPT_Spark_Skill
```

### 2. 安装到 Codex

macOS / Linux：

```bash
mkdir -p ~/.codex/skills
cp -R skills/CN_Spark_paper2ppt ~/.codex/skills/
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills"
Copy-Item -Recurse ".\skills\CN_Spark_paper2ppt" "$HOME\.codex\skills\"
```

重启 Codex 会话后，可以直接提出类似请求：

```text
请把这篇论文做成中文组会汇报 PPT，保留论文关键图表，并生成研究技术路线图。
```

### 3. 安装 Python 依赖

脚本执行依赖 Python。建议使用 Python 3.10+，然后在 skill 目录安装依赖：

```bash
cd skills/CN_Spark_paper2ppt
python -m pip install -r requirements.txt
```

如果通过 agent 自动执行完整流程，也应以这个 `requirements.txt` 为准安装依赖。公式渲染、PDF 解析、SVG 转 PPTX、模板导入等脚本都会读取这里的 Python 包配置。

AI 图片生成需要额外配置对应模型服务的环境变量。可参考：

```bash
cp .env.example .env
```

然后按本地环境填写 API key 或图像后端配置。

### 4. Claude Code 可选安装

如果使用 Claude Code，也可以复制同一个 skill 目录：

macOS / Linux：

```bash
mkdir -p ~/.claude/skills
cp -R skills/CN_Spark_paper2ppt ~/.claude/skills/
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills"
Copy-Item -Recurse ".\skills\CN_Spark_paper2ppt" "$HOME\.claude\skills\"
```

仓库根目录保留 `.claude-plugin/marketplace.json`，用于 Claude plugin 方式注册。当前 plugin 只指向本仓库内这一套 skill。

## 主要流程

### 这个 skill 是什么？

`cn-academic-spark-ppt-engine` 是一个中文学术 PPT 生成 skill。它把完整学术材料转成项目化产物：解析后的 Markdown、项目 `design_spec.md`、机器可读 `spec_lock.md`、逐页 SVG、演讲备注、图片 / 公式资源，以及最终 `.pptx`。

适用输入包括：

- 学术论文 PDF / Word / Markdown
- 开题报告、研究计划、课题申请材料
- 文献综述、journal club 材料
- 课程报告、政策报告、案例分析
- 用户提供的 PPTX 模板

### Key Rules Enforced

- 输出必须是真实可编辑 `.pptx`，不是 Markdown 大纲，也不是整页截图。
- 主流程是 `Source -> Outline -> Design Spec -> SVG -> DrawingML PPTX`。
- 不调用外部 technicalroute skill；研究路线图在 `CN_Spark_paper2ppt` 内部完成。
- 技术路线图默认生成两页：模板可编辑版和 AI 参考图版。
- 用户 PPTX 模板的设计优先级最高，包括标题位置、字体大小、加粗、颜色、placeholder 几何等。
- 用户 PPTX 模板模式下，页码优先跟随母版 / 版式页码占位符；无页码槽时才使用默认右下角。
- 除技术路线、总结页、规划启示页外，每页至少有一张图片、复杂表格截图、图表或数学公式。
- 中文 / 英文 / 数字混排需要分字体处理，引用页脚按中文学术报告习惯组织。
- 论文公式优先转写为 LaTeX，再渲染为透明 PNG 插入 PPT。

### Files

```text
CN_Academic_PPT_Spark_Skill/
|-- README-CN.md
|-- LICENSE
|-- .claude-plugin/
|   `-- marketplace.json
`-- skills/
    `-- CN_Spark_paper2ppt/
        |-- SKILL.md
        |-- requirements.txt
        |-- .env.example
        |-- conditional-workflows/
        |-- references/
        |   |-- academic/
        |   `-- technicalroute/
        |-- scripts/
        |   |-- source_to_md/
        |   |-- technicalroute/
        |   |-- template_import/
        |   |-- pptx_to_svg/
        |   `-- svg_to_pptx/
        `-- templates/
            |-- layouts/
            |-- charts/
            |-- icons/
            `-- technicalroute/
                |-- templates/
                `-- Custom_gallery/
```

### Example Workflow

1. 用户上传论文 PDF 和可选 PPTX 模板。
2. skill 将论文转换为 Markdown，抽取论文图片、复杂表格和公式线索。
3. 根据汇报类型选择 Route A / B / C / D，并判断论文类型。
4. 生成 `design_spec.md` 和 `spec_lock.md`，确定页数、章节、标题、引用、图片和模板策略。
5. 如果用户提供 PPTX 模板，导入模板并识别可编辑元素、主题色、标题位置、字体和身份标识。
6. 需要研究路线图时，内部 TechnicalRoute 生成模板可编辑 SVG 版和 AI 参考图版。
7. 逐页生成 SVG，执行质量检查，写入 speaker notes。
8. 将 SVG 转换为 DrawingML PPTX，输出最终 `.pptx` 和简要 QA 摘要。

## 开发状态

当前项目仍处于 v1 开发阶段，尚未作为稳定产品正式对外发布。README 只描述当前仓库的设计目标和使用方式；具体执行规则以 `skills/CN_Spark_paper2ppt/SKILL.md`、`references/`、`templates/` 和 `scripts/` 中的文件为准。

## 致谢

本项目参考了以下开源项目的思路与工程结构，并在此基础上面向中文学术 PPT 场景继续开发：

- nature-skills：https://github.com/Yuan1z0825/nature-skills
- ppt-master：https://github.com/hugohe3/ppt-master
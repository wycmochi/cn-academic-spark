# CN-Academic-Spark

CN-Academic-Spark 是一个面向中文学术汇报场景的 Codex skill 仓库。当前仓库的核心 skill 是 `cn-academic-spark-ppt-engine`，用于把论文、开题材料、课程报告、文献综述、政策报告等完整学术材料转换为中文学术 `.pptx`。

它不是单纯的“文字转 PPT”提示词，而是一套包含来源解析、论文图表公式处理、中文学术叙事、模板解析、演讲稿 DOCX生成和质量检查的工作流。

## 1 案例展示

![案例展示](example_asset/case-transportation-partc.png)

- [下载示例 PPTX](example_asset/example-transportation-partc.pptx)
- [查看论文原文 PDF](example_asset/main.pdf)

本案例基于交通领域论文 `High-speed rail impacts on intercity accessibility: A multi-modal, multi-scalar networking approach`，使用 `cn-academic-spark-ppt-engine` 生成中文学术汇报 PPT。示例用于展示论文解析、图表复用、方法框架组织和可编辑 PPTX 导出的效果。

---

## 2 产品构成

该项目构建 `Source → Outline → Design Spec → SVG → DrawingML PPTX` 的端到端生成流水线，支持论文答辩、组会汇报、课程报告、开题报告、文献综述等场景，最终输出带讲稿、带 GB/T 7714 引用、带技术路线图、可编辑的 .pptx 文件。

| 组件 | 位置 | 作用 |
|---|---|---|
| 核心 skill | `skills/CN_Spark_paper2ppt/` | 学术 PPT 生成主入口，包含 source 解析、路线选择、设计规范、SVG 页面、PPTX 导出和 QA 流程。 |
| 学术规则 | `skills/CN_Spark_paper2ppt/references/academic/` | 论文类型判断、中文学术标题、引用页脚、讲稿、公式、图表解释和不同汇报场景的结构规则。 |
| TechnicalRoute | `skills/CN_Spark_paper2ppt/references/technicalroute/`、`scripts/technicalroute/`、`templates/technicalroute/` | 内置技术路线图模块，生成可编辑模板版和 AI 参考图版。 |
| 模板与资源 | `skills/CN_Spark_paper2ppt/templates/` | 页面布局、图表、icons、PPT 模板解析结果、TechnicalRoute 模板和 Custom_gallery 参考仓库。 |
| 工具脚本 | `skills/CN_Spark_paper2ppt/scripts/` | PDF/Word/PPT/Excel 转换、模板导入、公式渲染、SVG 检查、SVG 转 PPTX、讲稿 DOCX 导出等。 |

## 3 产品亮点

| 功能 | 其他产品 | cn-academic-spark |
|---|---:|---:|
| 用户上传 PPT 模板解析 | 大多只复用主题颜色 | 模板结构及元素解析 |
| 多源论文文件 PDF/Word/Markdown 结构解析 | 部分 | √ |
| 输出真实可编辑 PPTX 对象 | 常为整页图片 | √ |
| 符合学术规范的文献引用 | 不稳定 | √ |
| 演讲稿 DOCX 输出 | 部分 | √ |
| 全文技术路线图ppt可编辑版本 | 部分 | √ |
| 支持自定义参考库，AI生成全文技术路线 | × | √ |
| 版式溢出、重叠、低分辨率等ppt输出质量检查 | 不稳定 | √ |

## 4 安装

### 4.1 安装 Python

建议使用 Python 3.10 或更高版本，优先推荐 Python 3.11。安装后确认命令可用：

```bash
python --version
```

运行 skill 时会按项目脚本自动处理所需依赖；用户不需要手动逐条安装 Python 包。若需要本地调试脚本，可以再查看 `skills/CN_Spark_paper2ppt/requirements.txt`。

### 4.2 克隆仓库

```bash
git clone <this-repository-url>
cd CN_Academic_PPT_Spark_Skill
```

### 4.3 安装到 Codex（推荐）

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills"
if (Test-Path "$HOME\.codex\skills\CN_Spark_paper2ppt") {
  Remove-Item -Recurse -Force "$HOME\.codex\skills\CN_Spark_paper2ppt"
}
Copy-Item -Recurse ".\skills\CN_Spark_paper2ppt" "$HOME\.codex\skills\"
```

macOS / Linux：

```bash
mkdir -p ~/.codex/skills
rm -rf ~/.codex/skills/CN_Spark_paper2ppt
cp -R skills/CN_Spark_paper2ppt ~/.codex/skills/
```

安装或更新后请重启 Codex 会话，避免继续使用旧 skill 副本。

### 4.4 安装到 Claude Code

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills"
if (Test-Path "$HOME\.claude\skills\CN_Spark_paper2ppt") {
  Remove-Item -Recurse -Force "$HOME\.claude\skills\CN_Spark_paper2ppt"
}
Copy-Item -Recurse ".\skills\CN_Spark_paper2ppt" "$HOME\.claude\skills\"
```

macOS / Linux：

```bash
mkdir -p ~/.claude/skills
rm -rf ~/.claude/skills/CN_Spark_paper2ppt
cp -R skills/CN_Spark_paper2ppt ~/.claude/skills/
```

## 5 推荐提问方式

为了让生成结果更稳定，建议在 prompt 中说明这些信息：

- 学科或方向：如交通运输、医学、计算机、管理学、遥感等。
- 汇报场景：组会、课程报告、开题、答辩、文献综述、项目汇报。
- 汇报人信息：姓名、学校、学院、课题组、导师。
- 期望页数和时长：例如 18-22 页、15 分钟。
- 语言与风格：中文学术汇报、偏正式、面向导师/组会/评审专家。
- 重点内容：必须保留哪些论文图、公式、结果表；是否需要绘制技术路线图或机制图。
- 模板要求：是否使用用户上传 PPT 模板、是否保留学校 logo、色彩偏好。

完整示例：

```text
请使用 CN-Academic-Spark，把我上传的交通运输方向论文做成中文组会汇报 PPT。
汇报人：张三，学校：某某大学，导师：李四教授。
汇报时长约 15 分钟，页数控制在 18-22 页。
请保留论文中的关键结果图和公式，并为每张图生成针对性说明；同时总结我使用模型的原理和全文技术路线，并将其可视化。
```

## 6 skill说明与自定义操作

### 6.1 这个 skill 是什么？

`cn-academic-spark-ppt-engine` 是一个中文学术 PPT 生成 skill。它把完整学术材料转成项目化产物：解析后的 Markdown、项目 `design_spec.md`、机器可读 `spec_lock.md`、逐页 SVG、演讲备注、图片 / 公式资源，以及最终 `.pptx`。

适用输入包括：

- 学术论文 PDF / Word / Markdown。
- 开题报告、研究计划、课题申请材料。
- 文献综述、journal club 材料。
- 课程报告、政策报告、案例分析。
- 用户提供的 PPTX 模板。

### 6.2 关键约束

- 输出必须是真实可编辑 `.pptx`，不是 Markdown 大纲，也不是整页截图。
- 主流程是 `Source -> Outline -> Design Spec -> SVG -> DrawingML PPTX`。
- 不调用外部 technicalroute skill；研究路线图在 `CN_Spark_paper2ppt` 内部完成。
- 技术路线图默认生成两页：模板可编辑版和 AI 参考图版。
- 用户 PPTX 模板的设计优先级最高，包括标题位置、字体大小、加粗、颜色、placeholder 几何等。
- 用户 PPTX 模板模式下，页码优先跟随母版 / 版式页码占位符；无页码槽时才使用默认右下角。
- 除技术路线、总结页、规划启示页外，每页至少有一张图片、复杂表格截图、图表或数学公式。
- 中文 / 英文 / 数字混排需要分字体处理，引用页脚按中文学术报告习惯组织。
- 论文公式优先转写为 LaTeX，再渲染为 PNG 插入 PPT。

### 6.3 Skill Files

```text
CN_Academic_PPT_Spark_Skill/
|-- README.md
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

### 6.4 workflow示例

1. 读取用户材料，将 PDF / Word / Markdown / PPTX / Excel 等来源转换为项目化 Markdown 和资源清单。
2. 判断汇报类型与论文类型，生成 `ppt_outline_cn.md`、`design_spec.md` 和 `spec_lock.md`。
3. 如用户提供 PPT 模板，先解析模板主题色、字体、标题槽、页码槽、icons 和受保护区域。
4. 提取论文内图片、表格、公式和关键图注，优先把机制图、原理图、结果图放入正文页并生成说明。
5. 生成 TechnicalRoute：可编辑模板版走 SVG；AI 生图版走独立图像生成链路，直接作为整页 PNG 插入 PPTX。
6. 逐页生成 SVG 页面，执行文本框、图形边界、字体大小、图片等比例缩放和页面边界检查。
7. 导出讲稿 DOCX，并将 SVG 转换为可编辑 DrawingML PPTX。
8. 执行最终 QA：PPTX 可打开性、direct image slide、AI route 参考源、图片分辨率、文本溢出等。

### 6.5 自定义技术路线图参考仓库

AI 技术路线图的兜底参考仓库位于：

```text
skills/CN_Spark_paper2ppt/templates/technicalroute/Custom_gallery/
```

它只用于 AI 技术路线图 Version B 的参考风格和结构，不提供论文语义内容。语义内容必须来自论文和 `content.yaml`；参考图只能来自两类来源：

1. `references/technicalroute/seed_sites.json` 指导的学术检索结果。
2. 学术检索无可用结果后，`Custom_gallery` 中对应学科的 raster 图片。

添加自己学科的参考方式：

1. 在 `Custom_gallery/` 下新建学科文件夹，例如 `medicine/`、`computer_science/`、`management/`。
2. 放入 PNG/JPG/JPEG/WEBP/BMP 格式的范图；不要放 SVG、PPT、PPTX、Keynote 或截图自可编辑 route 页的图片。
3. 在该学科文件夹内维护一个 manifest，例如 `medicine/medicine-manifest.json`，记录每张范图的论文来源、年份、作者、适用场景、`plotSummary` 和 `agentKeywords`。
4. 在 `Custom_gallery/gallery_index.json` 中新增学科条目：
   - `label_zh`：学科中文名。
   - `aliases`：中英文别名，便于自动匹配用户 prompt 和论文主题。
   - `default_archetype`：默认图类型，如 `workflow`、`method`、`thinking`。
   - `refs`：每张范图的索引，至少包含 `label`、`file`、`archetype`、`sub_variant`、`keywords`、`source_manifest`。
5. 当没有完全对应的参考图时，系统会在同一 Custom_gallery 范围内按学科、图类型、关键词和意图选择最接近的 raster 范图参考并生成AI技术路线图。

## 7 输出内容与目录结构

一次完整运行后，项目目录通常包含三类最终交付物：

- 质检 Markdown / 中文大纲：`ppt_outline_cn.md` 或 `outline/ppt_outline_cn.md`，记录页数、notes 覆盖、图片 / 公式对象、TechnicalRoute 位置和 QA 状态。
- 汇报 PPT：`exports/<project_name>_<timestamp>.pptx`，默认是 DrawingML 可编辑对象；AI 技术路线图 Version B 作为独立高清 PNG 页插入。
- 演讲稿 DOCX：`exports/<project_name>_speaker_notes.docx`，连续分段文稿，每段前带 `第 N 页：` 便于定位。

输出成果如下：

```text
projects/<project_name>/
├─ content.yaml                         # 论文解析、汇报元信息、图表公式索引
├─ outline/
│  ├─ ppt_outline_cn.md                  # 中文汇报大纲
│  └─ design_spec.md                     # 页面设计规格
├─ notes/
│  ├─ *.md                               # 每页讲稿来源
│  └─ formula_*.json                     # 公式块渲染输入
├─ images/
│  ├─ figures/                           # 论文图片、机制图、结果图
│  └─ formulas/
│     ├─ formula_block_*.png             # QA 通过的公式块图片
│     └─ formula_block_*.meta.json       # 公式渲染元数据与 mathtext 校验结果
├─ technicalroute/
│  ├─ search_refs/                       # 学术检索参考记录
│  ├─ gallery_refs/                      # Custom_gallery 兜底参考记录
│  ├─ route_ai_image.png                 # AI 生图结果
│  └─ _direct_image_slides.json          # 直接图片页插入清单
├─ svg_output/                           # 主 PPT 可编辑页 SVG
└─ exports/
   ├─ <project_name>_<timestamp>.pptx
   └─ <project_name>_speaker_notes.docx
```

## 8 致谢

本项目参考了以下开源项目的思路与工程结构，并在此基础上面向中文学术 PPT 场景继续开发：

- nature-skills: https://github.com/Yuan1z0825/nature-skills
- ppt-master: https://github.com/hugohe3/ppt-master

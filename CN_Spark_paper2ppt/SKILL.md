---
name: cn_spark_paper2ppt
description: >
  把一份完整的学术材料（论文、报告、开题书、读书笔记、综述提纲、PDF、Word、Markdown 或粘贴文本）
  转换为一整套**中文学术 .pptx**。覆盖四类汇报场景：学术论文讲解 / 课程报告 / 开题报告 / 文献综述。
  采用 ppt-master 的 **Source → Outline → SVG → DrawingML** 多阶段流水线：先识别大纲、生成可编辑 SVG，再
  转 PPTX，最终交付的是矢量可编辑的 `.pptx`，不是 Markdown 大纲。同时强制满足中文学术硬约束：
  GB/T 7714 引文页脚、备注区演讲词、底部横幅、四路线版式分流。
  当用户上传学术材料且要求做幻灯片 / 答辩 / 汇报 / 组会 / 开题 / 综述讲解时调用本技能。
---

# CN_Spark_paper2ppt · 中文学术 PPT 生成器

> **核心 pipeline**：`Source Document → Outline → Design Spec → [Image Acquisition] → SVG Pages → Quality Check → DrawingML (PPTX)`

本技能底层资产（templates / scripts / executor / strategist）参考自 ppt-master 并按中文学术场景做了必要扩展，保证：

1. 输出是**真正可编辑的 .pptx**：原生 DrawingML 矢量形状，PowerPoint / WPS 双击可改。
2. 整套 deck 走"先 SVG → 再 PPTX"两段式，避免文字与图形挤在一起、避免位图退化。
3. 强制满足中文学术硬约束（GB/T 7714 引文、混合字体、备注演讲词、底部横幅、四路线分流）。

> [!CAUTION]
> ## 🚨 全局执行纪律（与 ppt-master 一致）
>
> 1. **串行执行**：Step 1 → Step 7 严格按序，每步输出即下一步输入。
> 2. **BLOCKING = 硬停**：⛔ 标记的步骤必须等用户明确确认。
> 3. **不允许跨步打包**：Step 4 的"八项确认"必须一次性给出并等待回应。
> 4. **每页重读 `spec_lock.md`**：Executor 生成每张 SVG 前都重读，避免长 deck 主题色漂移。
> 5. **SVG 主代理产出**：SVG 生成必须由当前主代理顺序输出，禁止派给子代理批量生成。

> [!IMPORTANT]
> ## 🌐 语言与字体规则
>
> - **响应语言**：跟随用户输入与源材料；除非用户明确切换。
> - **正文字体**：中文用 *微软雅黑 / Source Han Sans*，英文 / 数字 / 拉丁字符用 *Times New Roman*（学术汇报场景的硬约束）。
> - **混合字体写法**：在 SVG 中用 `<tspan font-family="...">` 分段；具体见 [references/academic/citation-style.md](references/academic/citation-style.md)。
> - **`design_spec.md` 模板结构**保持英文骨架（与 ppt-master 一致），字段值可填中文。

---

## 主流水线脚本（继承自 ppt-master）

| 脚本 | 作用 |
|------|------|
| `scripts/source_to_md/pdf_to_md.py` | PDF → Markdown |
| `scripts/source_to_md/doc_to_md.py` | DOCX / EPUB / HTML 等 → Markdown |
| `scripts/source_to_md/excel_to_md.py` | Excel → Markdown |
| `scripts/source_to_md/ppt_to_md.py` | PPTX → Markdown |
| `scripts/source_to_md/web_to_md.py` | 网页 → Markdown |
| `scripts/project_manager.py` | 项目初始化 / 校验 / 资源导入 |
| `scripts/analyze_images.py` | 图片分析（生成图注 + 位置建议） |
| `scripts/image_gen.py` | 多后端 AI 生图（默认 Gemini 3 Pro Image） |
| `scripts/svg_quality_checker.py` | SVG 合规检查 |
| `scripts/total_md_split.py` | 演讲词按页拆分 |
| `scripts/finalize_svg.py` | SVG 后处理（图标内嵌 / 图片裁切 / tspan 拍平） |
| `scripts/svg_to_pptx.py` | **核心**：SVG → PPTX 转换（原生 DrawingML） |
| `scripts/update_spec.py` | 主题色 / 字体批量传播 |

完整脚本说明：[scripts/README.md](scripts/README.md)。

## 模板索引

| 索引 | 路径 | 用途 |
|------|------|------|
| 版式模板 | `templates/layouts/layouts_index.json` | 含 `academic_defense`（学位答辩）/ `medical_university`（医学院风）/ `government_blue`（开题答辩可用）等 |
| 可视化模板 | `templates/charts/charts_index.json` | 70+ 图表 / 信息图 / 框架（甘特图 / SWOT / 鱼骨 / 矩阵 / 概念图等） |
| 图标库 | `templates/icons/` | tabler / phosphor / simple-icons / chunk 四套 |

学术场景**强推**：
- `academic_defense` — 论文答辩 / 组会汇报（蓝白学院风、有 logo 位、有底部横幅位）
- `medical_university` — 医学 / 生命科学类
- `government_blue` — 开题报告（庄重深蓝、适合甘特图页）

## 学术专属参考（references/academic/）

| 文件 | 内容 | 何时读 |
|------|------|--------|
| [references/academic/route-academic-paper.md](references/academic/route-academic-paper.md) | Route A 学术论文路线（question-to-evidence 骨架） | Strategist 判定 Route A 时 |
| [references/academic/route-course-report.md](references/academic/route-course-report.md) | Route B 课程报告路线（背景-问题-分析-建议） | Strategist 判定 Route B 时 |
| [references/academic/route-proposal.md](references/academic/route-proposal.md) | Route C 开题报告路线（含甘特图） | Strategist 判定 Route C 时 |
| [references/academic/route-literature-review.md](references/academic/route-literature-review.md) | **Route D 文献综述路线（含概念框架可视化）** | Strategist 判定 Route D 时 |
| [references/academic/citation-style.md](references/academic/citation-style.md) | GB/T 7714 引文 + 中英文混合字体 SVG 写法 | **任何路线写引用时必读** |
| [references/academic/speaker-notes.md](references/academic/speaker-notes.md) | 演讲词撰写规范、衔接、口播 vs 书面 | Step 6 写 `notes/total.md` 时 |
| [references/academic/layout-library.md](references/academic/layout-library.md) | 中文学术各 `content_type` 的版式映射（含底部横幅） | Strategist 选版式时 |
| [references/academic/executor-academic.md](references/academic/executor-academic.md) | **学术专属执行器**：底部横幅 / 引文页脚 / 公式页 / 矩阵证据表的 SVG 写法 | **Step 6 执行器必读，替换 executor-{general,consultant}** |

---

## Workflow（7 步）

### Step 1 · 解析输入材料

🚧 **GATE**：用户已提供任意一种材料（PDF / DOCX / EPUB / URL / Markdown / 对话粘贴文本 / 已有论文笔记）。

> 仅有**主题词**而无材料时 → 先跑 [`workflows/topic-research.md`](workflows/topic-research.md)（带回研究文档 + 图片），再回到 Step 1。学术场景下 topic-research 必须只用**权威可引用源**（Wikipedia / 期刊官方 / 政府公开数据），避免引入未经发表的二手内容。

按下表转 Markdown：

| 用户输入 | 命令 |
|---|---|
| PDF（论文 / 报告） | `python3 scripts/source_to_md/pdf_to_md.py <file>` |
| DOCX / Word | `python3 scripts/source_to_md/doc_to_md.py <file>` |
| Excel 数据 | `python3 scripts/source_to_md/excel_to_md.py <file>` |
| 网页 / 期刊摘要 | `python3 scripts/source_to_md/web_to_md.py <URL>` |
| Markdown | 直接读 |

**✅ Checkpoint** — 源材料 Markdown 就绪，进入 Step 2。

---

### Step 2 · 项目初始化

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source_files...> --move
```

`<project_name>` 建议 `<场景>_<论文短名>`，例如 `defense_mobility_exposure`、`review_2sfca_dynamic`、`proposal_displacement_2026`。

`--move` 让原 PDF / Markdown 进入 `sources/` 而不是复制，节省空间。

**✅ Checkpoint** — `projects/<name>/` 已建好（含 `sources/` `templates/` `images/` `svg_output/` `notes/`），进入 Step 3。

---

### Step 3 · 模板选择

**默认 — 自由设计**：直接进入 Step 4。除非用户显式给出模板目录路径，否则不主动猜模板。

学术场景**显式触发**情况（用户给路径）：

| 用户输入 | 推荐模板路径 |
|---|---|
| 论文答辩 / 组会 | `templates/layouts/academic_defense/` |
| 开题答辩 | `templates/layouts/government_blue/` |
| 医学 / 生科 | `templates/layouts/medical_university/` |
| 文献综述 / journal club | `templates/layouts/academic_defense/`（可后续手动改色） |

触发后复制模板：

```bash
TEMPLATE_DIR=templates/layouts/academic_defense
cp $TEMPLATE_DIR/*.svg <project_path>/templates/
cp $TEMPLATE_DIR/design_spec.md <project_path>/templates/
cp $TEMPLATE_DIR/*.png <project_path>/images/ 2>/dev/null || true
```

详细规则与 mirror/fidelity/standard 三种复制模式见 ppt-master 主文档与 [workflows/create-template.md](workflows/create-template.md)。

**✅ Checkpoint** — 默认或模板已就位，进入 Step 4。

---

### Step 4 · Strategist 阶段（八项确认 + 路线分流 + 大纲）

🚧 **GATE**：Step 3 完成。

**必读**：
```
Read references/strategist.md          # ppt-master 通用 Strategist
Read references/academic/executor-academic.md   # 学术执行器（提前看，决定 §IV §V）
```

#### 4.1 路线分流（学术专属）

按下表判定，**只读对应那一份 academic route 文件**：

| 输入类型 | 路线 | 必读 |
|---|---|---|
| 学术论文（期刊 / 会议、单篇） | **Route A** | [references/academic/route-academic-paper.md](references/academic/route-academic-paper.md) |
| 课程报告（含时政 / 政策 / 案例） | **Route B** | [references/academic/route-course-report.md](references/academic/route-course-report.md) |
| 开题报告（含甘特图、研究计划） | **Route C** | [references/academic/route-proposal.md](references/academic/route-proposal.md) |
| 文献综述 / Review | **Route D** | [references/academic/route-literature-review.md](references/academic/route-literature-review.md) |

#### 4.2 八项确认（⛔ BLOCKING）

把八项配置作为**一次性**打包给用户：

1. 画布：`ppt169`（学术汇报默认）
2. 页数：依汇报时长（默认 1.5 分钟/页，综述 2 分钟/页）
3. 受众：答辩委员 / 组会同行 / 课程教师 / 综述听众
4. 风格目标：严谨 / 紧凑 / 留白学院风
5. 配色：深蓝经典（默认 `#1F3864`） / 墨绿学术 / 深灰简约 / 跟随学校色
6. 图标用法：tabler-outline（默认，学院风） / phosphor-duotone（信息密度高时）
7. 字体：中文微软雅黑 + 英数 Times New Roman（默认）；或 Source Han Sans + Inter
8. 图片：用户提供 / AI 生成 / Web 搜索 / 仅占位

> ⚠️ 默认配色与字体即满足"学术硬约束"。用户无特殊要求时直接采用默认。

#### 4.3 输出物

- `<project_path>/design_spec.md`（人读，含 §IX 每页内容简报）
- `<project_path>/spec_lock.md`（机器读，Executor 每页重读 — 见 ppt-master 主文档）

`design_spec.md §IX` 每页都要带：`page_rhythm` / `page_layouts` / `page_charts` / `bottom_banner_text` / `citations[]` 字段。其中 **`bottom_banner_text` 与 `citations[]` 是学术专属字段**，详见 [executor-academic.md](references/academic/executor-academic.md) §2。

**✅ Checkpoint** — Strategist 阶段完成，用户已确认大纲。

---

### Step 5 · 图片获取（条件触发）

🚧 **GATE**：Step 4 完成。

> **触发**：`design_spec.md §VIII 资源清单`中至少一行 `Acquire Via: ai` 或 `Acquire Via: web`。否则跳到 Step 6。

```
Read references/image-base.md           # 通用框架
Read references/image-generator.md      # 仅当有 ai 行
Read references/image-searcher.md       # 仅当有 web 行
```

**学术补充**：
- 论文里**已存在的图**（实验结果图、流程图截图） → 用 `analyze_images.py` 分析后**直接嵌入 SVG**（保留原图，标"图来源：[n]"）。
- 需要的**自绘图**（技术路线、研究框架、概念图） → 调 **`CN_Spark_technicalroute`** 子技能（参见仓库根 `SKILL.md` 联合调用约定），用 AI 生图后再嵌入 SVG，不要在本技能内强凑流程图节点。

**✅ Checkpoint** — 每一行资源都达到 `Generated` / `Sourced` / `Needs-Manual` 终态。

---

### Step 6 · Executor 阶段（SVG 生成 + 演讲词）

🚧 **GATE**：Step 4（及 Step 5 触发后）完成。

**必读**：
```
Read references/executor-base.md          # 通用执行规则（每页重读 spec_lock 等）
Read references/shared-standards.md       # SVG / PPT 兼容性硬约束
Read references/academic/executor-academic.md   # ⭐ 学术专属执行器（替代 executor-general / consultant）
```

> ⚠️ 学术场景**只读 executor-academic.md**，不读 executor-general / consultant / consultant-top。学术执行器在通用约束之上叠加：底部横幅、引文页脚、模块化公式页、矩阵证据表、混合字体 tspan 写法。

#### 6.1 设计参数确认

按 `executor-base.md §2` 输出画布、字号、配色、字体计划。

#### 6.2 批量预读

按 `executor-base.md §1.0` 一次性读完所有 `page_layouts` 与 `page_charts` 引用的模板 SVG。

#### 6.3 顺序生成 SVG

> ⚠️ **强制纪律**：必须**逐页串行**生成（不要 5 页一批）。每页生成前 `read_file <project_path>/spec_lock.md`。SVG 必须由当前主代理输出，不允许派子代理。

每页输出文件 `<project_path>/svg_output/<NN>_<page_name>.svg`。

**学术专属硬约束**（见 [executor-academic.md](references/academic/executor-academic.md)）：

1. 每张证据型 / 论点页底端必须有 **`bottom_banner`**（深蓝底白字一句话主旨，22mm 高，置于底部）；
2. 凡引用文献的页面，必须在 `bottom_banner` 上方 8pt 浅灰 `#888888` 列出 **GB/T 7714 完整条目**；
3. 引文条目里**中文-微软雅黑、数字 / 拉丁字符-Times New Roman**，分 `<tspan>` 写入；
4. 公式页默认 **"模块化步骤公式页"**，每个公式独占一个 panel；超过 3 个公式时切换"标题分段公式页"；
5. 自绘流程图 / 框架图禁止位图截图，必须用 SVG `<rect>` `<line>` `<path>` `<marker>` 写成可编辑形状。

#### 6.4 质量检查门

```bash
python3 scripts/svg_quality_checker.py <project_path>
```

任何 `error` 必须在本步修复并重出（**禁止**先跑 finalize_svg 再检查）。

#### 6.5 演讲词

写入 `<project_path>/notes/total.md`：每页 100–180 字，正式但自然，不照读 PPT。规范见 [references/academic/speaker-notes.md](references/academic/speaker-notes.md)。

**✅ Checkpoint** — 所有 SVG 生成完毕、checker 0 errors、`notes/total.md` 完成。

> **含数据图表的 deck**：在 Step 7 前先跑 [`workflows/verify-charts.md`](workflows/verify-charts.md) 校正坐标。AI 在映射数据→像素时常引入 10–50px 误差，verify-charts 把这一类错误清零。

---

### Step 7 · 后处理与导出

🚧 **GATE**：Step 6 完成；`svg_output/` 已就位、`notes/total.md` 已写。

> ⚠️ 三个子步必须**逐一**执行，不要合在一行。

**7.1 拆分演讲词**：
```bash
python3 scripts/total_md_split.py <project_path>
```

**7.2 SVG 后处理**（图标嵌入 / 图片裁切 / tspan 拍平 / 圆角矩形转 path）：
```bash
python3 scripts/finalize_svg.py <project_path>
```

**7.3 导出 PPTX**（嵌入演讲词、默认带入场动画）：
```bash
python3 scripts/svg_to_pptx.py <project_path>
# 输出：
#   exports/<project_name>_<timestamp>.pptx           ← 主交付物（原生 DrawingML，高保真）
#   backup/<timestamp>/<project_name>_svg.pptx        ← SVG 预览版（旧路径）
#   backup/<timestamp>/svg_output/                    ← SVG 源备份
```

**可选**：
- `-t fade|push|wipe|...` 切页转场
- `-a fade|mixed|none` 入场动画
- `--animation-trigger after-previous|on-click|with-previous` 触发方式
- 含数据图表 → 先跑 [`workflows/verify-charts.md`](workflows/verify-charts.md)
- 想录制旁白 → 跑 [`workflows/generate-audio.md`](workflows/generate-audio.md)
- 想可视化微调 → 跑 [`workflows/visual-edit.md`](workflows/visual-edit.md)

---

## 与 CN_Spark_technicalroute 的协作

当 `design_spec.md` 中**任一页**需要"技术路线图 / 研究框架图 / 概念框架图 / 思考脉络图"时：

1. 在 Step 5 不要把这张图作为普通 `Acquire Via: ai` 行处理；
2. 切换到 [CN_Spark_technicalroute/SKILL.md](../CN_Spark_technicalroute/SKILL.md)；
3. 把需求（archetype + 主题 + 节点要点 + 配色）传过去，让它走"文献样式检索 → image_gen.py 生图"流水线；
4. 拿回 PNG / SVG 后，在对应 SVG 页面用 `<image href="...">` 嵌入。

详细协作约定见仓库根 [SKILL.md](../SKILL.md)。

---

## 学术硬约束（无论走哪一路线都要满足）

1. **可编辑 .pptx**：所有正文、表格、流程图都是原生 DrawingML 矢量；禁止把流程图退化为整张截图。
2. **引文**：正文出现引用 → 必加 `[n]` 角标；该页底端 8pt 灰色完整 GB/T 7714 条目；混合字体分 tspan。
3. **底部横幅**：每张证据型页都要有一句话主旨（深蓝底白字、22mm 高）。
4. **演讲词**：每页 `notes/<NN>_*.md` 不允许空白。
5. **不编造**：不出现源材料中没有的数据 / 机构 / 文献 / 图细节。

---

## 输出物

```
projects/<project_name>/
├── sources/                              ← 原始材料
├── images/                               ← 用户图 + AI 生图 + 论文原图
├── templates/                            ← 选择的版式模板（如有）
├── design_spec.md                        ← 人读设计书
├── spec_lock.md                          ← 机器读执行锁
├── svg_output/                           ← Executor 输出的 SVG
│   ├── 01_cover.svg
│   ├── 02_toc.svg
│   ├── 03_introduction.svg
│   └── ...
├── svg_final/                            ← finalize_svg 后处理结果
├── notes/
│   ├── total.md                          ← 演讲词总文件
│   ├── 01_*.md / 02_*.md / ...           ← 按页拆分
├── exports/
│   └── <project_name>_<timestamp>.pptx   ← ⭐ 主交付物
└── backup/
    └── <timestamp>/...                   ← SVG 备份 + 旧版预览 pptx
```

---

## Fallback Rules

- **部分内容缺失**：仍尽量产出可用骨架；缺数据用占位符并在 `notes/` 注明；
- **python-pptx / lxml 不可用**：跳过 svg_to_pptx，导出 SVG 集合 + 一份说明；
- **没有 LibreOffice**：跳过 SVG 预览，直接走 finalize_svg → svg_to_pptx；
- **图片获取失败**：按 `image-base.md §5` 规则——重试一次 → 标 `Needs-Manual` → 不阻塞主流程。

---

## References Index

通用（继承自 ppt-master）：

| 文件 | 何时读 |
|---|---|
| [references/strategist.md](references/strategist.md) | Step 4 |
| [references/executor-base.md](references/executor-base.md) | Step 6 |
| [references/shared-standards.md](references/shared-standards.md) | Step 6 |
| [references/image-base.md](references/image-base.md) | Step 5 |
| [references/image-generator.md](references/image-generator.md) | Step 5 有 ai 行时 |
| [references/image-searcher.md](references/image-searcher.md) | Step 5 有 web 行时 |
| [references/template-designer.md](references/template-designer.md) | 仅在 [workflows/create-template.md](workflows/create-template.md) |
| [references/canvas-formats.md](references/canvas-formats.md) | 画布尺寸查 |
| [references/animations.md](references/animations.md) | Step 7 动画 |
| [references/svg-image-embedding.md](references/svg-image-embedding.md) | SVG 内嵌位图时 |
| [references/image-layout-spec.md](references/image-layout-spec.md) | 图片版式规范 |

学术专属：

| 文件 | 何时读 |
|---|---|
| [references/academic/executor-academic.md](references/academic/executor-academic.md) | **Step 6 必读** |
| [references/academic/citation-style.md](references/academic/citation-style.md) | 任何路线写引用时 |
| [references/academic/speaker-notes.md](references/academic/speaker-notes.md) | Step 6 写演讲词 |
| [references/academic/layout-library.md](references/academic/layout-library.md) | Step 4 选版式 |
| [references/academic/route-academic-paper.md](references/academic/route-academic-paper.md) | Route A |
| [references/academic/route-course-report.md](references/academic/route-course-report.md) | Route B |
| [references/academic/route-proposal.md](references/academic/route-proposal.md) | Route C |
| [references/academic/route-literature-review.md](references/academic/route-literature-review.md) | Route D |

## Notes

- 本地预览：`python3 -m http.server -d projects/<name>/svg_final 8000`
- 故障排除：[scripts/docs/troubleshooting.md](scripts/docs/troubleshooting.md)
- 公式页规则（模块化 / 标题分段）已内嵌到 [executor-academic.md](references/academic/executor-academic.md)，不用查别的文件。

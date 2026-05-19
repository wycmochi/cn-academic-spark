# `assets/templates/` · Editable SVG Templates (TR engine first choice)

> **位置定位**：当 TechnicalRoute engine 决定要画一张图时，它的第一选择**不是** AI 生图，而是从这里挑一个**结构匹配 + 可编辑**的 SVG 模板，再注入论文里的术语与数据。只有"任何模板都不合适"时才落到 `image_gen.py` 出栅格 PNG。这是本 skill"可编辑学术示意图"目标的实现底座。

## 选择流程（必读）

`generate_route_image.py` 与主代理共同执行：

1. **必读 `templates_index.json`** —— 这份 JSON 是模板**选择规则**（`summary = "Pick for X. Skip if Y."` 风格），不是文档说明。任何要走"模板装配"路径的任务**必须**先把整份 index 通读一遍。
2. **按 archetype 收口候选**——根据 `contract.md §2` 中决定的 `archetype` (`thinking` / `method` / `workflow`)，从 `archetypes.<name>.templates` 里取该 archetype 的全部模板。
3. **按 sub_variant + 内容形状打分**——结合 `contract.md §2.sub_variant`（quad / cascade / twin / mechanism-block / formula-grid / horizontal-pipeline / circular / vertical-stack …）与 `content.yaml` 的真实节点数、是否含公式、是否需要循环、轴是否分类型等，给每个候选模板按 summary 中的 "Pick / Skip" 条款打 0–3 分。
4. **用 `quickLookup` 二次校验**——例如 contract 提到 "2×2 quadrant" 而打分前 1 名不在 `quickLookup["2x2_quadrant"]` 里，说明判断可能跑偏，回到 step 3 重看 summary。
5. **没有 ≥ 2 分的候选 → 走 AI 生图后备**——只能先走 seed-sites 文献检索，若零可用结果再走 `gallery_only_fallback` / `image_gen.py` 链路，详见 [`../../references/handling-no-references.md`](../../references/handling-no-references.md)。
6. **命中模板后**——`Read` 该 SVG，**把占位文本替换为 `content.yaml` 中的具体术语**，颜色按 `contract.md §5 color_scheme` 改写。**严禁照搬模板里的示例文本**——文本必须来自当前论文 / 用户材料。

## 当前模板（18 张，按 archetype 分组）

`templates_index.json.archetypes` 是权威分组，下表是为人类查阅准备的速览。冲突时以 JSON 为准。

### `thinking` — 研究背景 / 问题 / 理论 / 意义

| 文件 | sub_variant_hint | 典型用途 |
|---|---|---|
| `ansoff_matrix.svg` | quad | 2×2 概念框架，两条正交轴的分类（"现有 vs 新"风格） |
| `bcg_matrix.svg` | quad | 2×2 portfolio quadrant（星 / 金牛 / 问号 / 狗 等命名格） |
| `feature_matrix_table.svg` | twin | 行×列方法对比，单元格放 ✓/✗/简短文字 |
| `icon_grid.svg` | quad | 4–9 个并列的概念，每条 icon + 短标签 + 一句支持 |
| `pyramid_chart.svg` | cascade | 层级递进（Maslow / DIKW / 微-中-宏观） |
| `venn_diagram.svg` | twin | 2–3 个集合交叠，强调贡献处于交集 |

### `method` — 模型结构 / 机制 / 公式 / 假设

| 文件 | sub_variant_hint | 典型用途 |
|---|---|---|
| `client_server_flow.svg` | mechanism-block | 两大主块跨边界交换（数据↔模型 / 传感器↔算法 / 用户端↔服务端） |
| `layered_architecture.svg` | vertical-stack | 3–6 层堆叠（数据层 / 特征层 / 模型层 / 输出层） |
| `method-formula-grid.svg` | formula-grid | 2–6 个命名公式拼成 grid，每格一式 + 一行含义 |
| `module_composition.svg` | mechanism-block | 3–6 个模块用箭头连成系统（encoder + attention + decoder 等） |
| `org_chart.svg` | vertical-stack | 显式层级 / 分类树（损失 = a + b + c，各项又有子项） |
| `vertical_list.svg` | vertical-stack | 3–6 步线性方法走读，每步一行无公式面板 |

### `workflow` — 全文 Data → Method → Result

| 文件 | sub_variant_hint | 典型用途 |
|---|---|---|
| `chevron_process.svg` | horizontal-pipeline | 3–6 阶段带强方向动量（chevron 箭头并入下一段） |
| `cycle_diagram.svg` | circular | 显式循环 / 反馈 / 迭代（PDCA、训练-验证回路） |
| `pipeline_with_stages.svg` | horizontal-pipeline | data → preprocess → model → result，全文思路默认 |
| `process_flow.svg` | horizontal-pipeline | 通用 3–8 阶段流程，转移箭头可带标签 |
| `progress_bar_chart.svg` | horizontal-pipeline | N 个任务各自的完成% (消融实验进度 / 标定阶段) |
| `project_schedule_table.svg` | horizontal-pipeline | Gantt-like 开题计划 / 研究进度 |

## SVG 内部约定

每个模板 SVG 都应当满足以下硬约束（与 paper2ppt 的 `templates/charts/CHART_STYLE_GUIDE.md` 同源，但范围更窄——只覆盖技术路线 / 框架图常用的 18 类）：

1. **画布**：`viewBox="0 0 1280 720"`，匹配 ppt169 默认页面；
2. **占位文本**：要被 `content.yaml` 替换的文字位置写成 `{{<path>}}`，例如 `{{title}}` / `{{P1.label}}` / `{{steps[0].formula_latex}}`；
3. **占位颜色**：使用 CSS variable，主代理在 prompt 合成阶段按 `contract.md §5.color_scheme` 替换为 HEX：
   - `var(--primary)` 主色
   - `var(--accent)` 强调色
   - `var(--muted)` 次要色 / 灰
   - `var(--surface)` 卡片底
4. **混合字体**：中文走 微软雅黑 / Source Han Sans，数字 / 拉丁字符走 Times New Roman / Inter——用 `<tspan font-family="...">` 分段，与 paper2ppt 的 GB/T 7714 引文约定一致；
5. **不允许的元素**：`<filter>`、3D 透视、emoji、栅格图片占位、水印——这些会让 svg_to_pptx 转换失败或破坏可编辑性；
6. **箭头**：直角 / 直线，不要 freestyle 曲线（`workflow.circular` 模板例外）。

## 如何新增一个模板

1. 决定新模板属于 `thinking` / `method` / `workflow` 哪一类（如都不属于，需要先在 [`../../references/archetype-*.md`](../../references/) 中扩 archetype）；
2. 用 `viewBox="0 0 1280 720"` 起手画 SVG，按上面 §SVG 内部约定 写占位符 + CSS var 颜色；
3. 文件命名 `<key>.svg`，`<key>` 用 snake_case 或与 paper2ppt 同名（如直接借用 `ansoff_matrix`、`pyramid_chart`）；
4. 在 [`templates_index.json`](templates_index.json) 三处添加：
   - `meta.total` 数字 +1；
   - `archetypes.<archetype>.templates` 列表加这个 key；
   - `templates.<key>` 加一个完整条目（`label` / `archetype` / `sub_variant_hint` / `summary` / `keywords`）；
   - 视情况在 `quickLookup` 加一个语义 tag → key 的映射；
5. 在本 README "当前模板" 表格里也加一行（仅作人类速览，权威以 JSON 为准）；
6. 跑一个 contract → prompt → render 的端到端 smoke test 验证新模板能被打分挑中。

## 与 paper2ppt 同名模板的关系

`ansoff_matrix.svg` / `bcg_matrix.svg` / `chevron_process.svg` / `client_server_flow.svg` / `cycle_diagram.svg` / `feature_matrix_table.svg` / `icon_grid.svg` / `layered_architecture.svg` / `module_composition.svg` / `org_chart.svg` / `pipeline_with_stages.svg` / `process_flow.svg` / `progress_bar_chart.svg` / `project_schedule_table.svg` / `pyramid_chart.svg` / `venn_diagram.svg` / `vertical_list.svg` 与 `../../../CN_Spark_paper2ppt/templates/charts/` 同名文件**视觉风格一致**，但本目录的版本是**为单图独立交付**裁的——viewBox 更宽、留白更多、字号更大，便于直接出图。两边各自维护，不要硬链接。

## 与 Custom_gallery 的差异

| 维度 | `templates/`（本目录） | `../Custom_gallery/` |
|---|---|---|
| 是什么 | 我们写的**抽象结构骨架**，可编辑 SVG | 用户 / 学科**真实学术图片**，PNG/JPG |
| 用途 | 装配 → 注入内容 → 出可编辑成品 | **结构参考**（panel 数 / 配色 / 流向）+ **风格 anchor**（喂给 image_gen.py） |
| 学术抄袭风险 | 无（骨架不带内容） | 高 — Gallery 里的文字 / 数据 / 节点**绝不能**复制到产物中，只能"看结构、抄风格" |
| 选择优先级 | 命中即用（**第一选择**） | 仅作风格参考，不作装配源 |

详细融合关系见 [`../README.md`](../README.md)（assets 总览）。

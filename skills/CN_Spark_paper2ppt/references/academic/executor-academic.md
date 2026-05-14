# Executor Academic · 中文学术执行器

> 通用规则在 [executor-base.md](../executor-base.md)，SVG/PPT 技术约束在 [shared-standards.md](../shared-standards.md)。本文件**仅**列出"中文学术汇报"相对通用执行器的增量。
>
> ⚠️ 学术场景**只读本文件**作为风格执行器，不读 `executor-general.md` / `executor-consultant.md` / `executor-consultant-top.md`。

---

## 1. 角色定义

中文学术汇报场景的 SVG 执行器：写论点页、证据页、流程图页、研究框架页、文献综述概念框架页、参考文献页。

适用：
- 学位答辩 / 组会汇报 / journal club
- 课程报告 / 开题报告
- 文献综述讲解
- 学术海报式总结页

风格目标：**克制、严谨、信息密度适中、可朗读**。每页都能用一句话讲清楚，不堆砌装饰。

---

## 2. 学术专属版面元素（每页都要确认四件事）

每一张证据型 / 论点页都按下面四件事检查。封面、目录、章节页、致谢页例外。

### 2.1 底部横幅 `bottom_banner`

中文学术 PPT 的标志性元素：页面**最底端**一条深色横幅，白字一句话，复述这页的论点 / 主旨。

**SVG 写法**（1280×720 画布）：

```svg
<g id="bottom_banner">
  <rect x="0" y="668" width="1280" height="52" fill="#1F3864"/>
  <text x="640" y="700" font-family="Microsoft YaHei,Source Han Sans SC,sans-serif"
        font-size="18" font-weight="bold" fill="#FFFFFF" text-anchor="middle">
    本页主张：人类流动性数据为暴露科学提供了高分辨率轨迹基线
  </text>
</g>
```

**硬约束**：
- 高度 52–72px（折合 22–30mm），不要更高，否则压缩正文；
- 颜色用 `spec_lock.colors.banner`（默认 = `primary` = `#1F3864`）；
- 字号 16–20px，**加粗**；
- 文本 ≤ 30 字（论点要短到能口头朗读）；
- 永远位于页面**最底层**，所有引文 / 页码 / 图都在其**上方**；
- 封面 / 目录 / 章节封面 / 致谢页**不要**底部横幅。

### 2.2 引文页脚 `citation_footer`

每张引用了文献的页都必须有。

**SVG 写法**：

```svg
<g id="citation_footer">
  <text x="60" y="650" font-size="11" fill="#888888">
    <tspan font-family="Microsoft YaHei,Source Han Sans SC,sans-serif">[1] 张三, 李四. 城市流动性与环境暴露的时空耦合分析</tspan><tspan font-family="Times New Roman,serif">[J]. </tspan><tspan font-family="Microsoft YaHei,sans-serif">地理学报</tspan><tspan font-family="Times New Roman,serif">, 2025, 80(3): 512-528.</tspan>
  </text>
  <text x="60" y="660" font-size="11" fill="#888888">
    <tspan font-family="Times New Roman,serif">[2] Smith J, Doe A. Mobility-based exposure assessment[J]. </tspan><tspan font-family="Times New Roman,serif" font-style="italic">Nature</tspan><tspan font-family="Times New Roman,serif">, 2024, 612(7940): 215-223.</tspan>
  </text>
</g>
```

**硬约束**：
- 引文字号 8–11px，颜色 `#888888`（浅灰，AA 对比度，不抢眼）；
- 紧贴 `bottom_banner` **上方**，行间距 1.0–1.2；
- 单页 ≤ 3 条；超过则前 3 条 + "等，详见参考文献页 P{n}"，完整列表挪到独立页；
- **混合字体**：中文 `<tspan font-family="Microsoft YaHei,..."`，数字 / 拉丁字符 `<tspan font-family="Times New Roman,...">`，必须**分 tspan**写入；
- 期刊名按学术惯例可加 `font-style="italic"`（仅英文期刊名，中文不斜）；
- 不要给引文条目加方框、底色、阴影。

引文写法的完整规范见 [citation-style.md](citation-style.md)。

### 2.3 中英文混排的 tspan 分段规则

**任意正文 / 标题 / 表格**只要同时含中文和"数字 / 英文 / 符号"，都必须分 tspan：

```svg
<text x="60" y="120" font-size="32" fill="#1F3864">
  <tspan font-family="Microsoft YaHei,sans-serif">研究背景：</tspan><tspan font-family="Times New Roman,serif">PM</tspan><tspan font-family="Times New Roman,serif" baseline-shift="sub" font-size="22">2.5</tspan><tspan font-family="Microsoft YaHei,sans-serif">的人群暴露估计</tspan>
</text>
```

切分规则（正则等价）：连续的中文汉字属于一段，连续的非中文（数字、字母、符号、空格）属于另一段。每段独立 `<tspan>` 设 `font-family`。

> 这一条是**学术汇报场景的硬约束**，比 ppt-master 默认更严格。`finalize_svg.py --flatten-tspan` 不会破坏此结构（它只拍平没有 font-family 切换的 tspan）。

### 2.4 页码 + Logo

- 页码：右下角，紧贴 `citation_footer` 与 `bottom_banner` 之间，9pt 灰；
- Logo：右上角占位 40×40px 方块，`<image href="logos/school_logo.png">`；
- 这两项都**不要**遮挡 `bottom_banner` / `citation_footer`。

---

## 3. 学术专属版式骨架

按 `design_spec.md §IX brief` 的 `content_type` 字段决定版式。所有版式都遵循 `executor-base.md §2.1` 的"每页重读 spec_lock"。

### 3.1 `text_flow` · 论点流页（Route A 引言、Route B 背景）

| 区域 | 位置（1280×720） |
|---|---|
| 标题（结论式标题） | x=60 y=80 w=1160 h=80，font-size=32，bold |
| 论点主体（≤ 3 段，每段一句一论点） | x=60 y=180 w=720 h=440 |
| 右侧配图（icon / 数据卡 / 简图） | x=820 y=180 w=400 h=440 |
| 引文页脚 | y=620–660 |
| 底部横幅 | y=668–720 |

### 3.2 `bullet_analysis` · 要点分析页（Route A 文献综述、Route B 政策分析）

| 区域 | 内容 |
|---|---|
| 标题 | 同 3.1 |
| 主体 | 3–5 条要点，每条左侧 16px 图标，主标题 18px，副解释 13px |
| 不要 | 超过 6 条；不要并列 bullet + 表格混排 |

### 3.3 `pipeline` · 技术路线 / 流程页（Route A P6、Route C P9）

**重要**：复杂技术路线**不要**在本技能内手画 SVG `<rect>` + `<line>`，调 [cn-academic-spark-technicalroute-engine](../../../CN_Spark_technicalroute/SKILL.md) 生图后嵌入。简单 3–5 步线性流程才本地画。

简单流程 SVG：

```svg
<g id="pipeline">
  <!-- 节点 -->
  <rect x="60"  y="240" width="180" height="80" rx="8" fill="#1F3864"/>
  <text x="150" y="285" fill="#FFF" text-anchor="middle" font-size="16">数据采集</text>
  <rect x="290" y="240" width="180" height="80" rx="8" fill="#4472C4"/>
  <!-- 箭头 -->
  <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 z" fill="#555555"/></marker></defs>
  <line x1="240" y1="280" x2="290" y2="280" stroke="#555555" stroke-width="2" marker-end="url(#arr)"/>
</g>
```

### 3.4 `matrix_framework` · 研究框架页（Route A P7、Route C P10）

三段式：**左维度 + 中模块 + 右产出**。

| 列 | 位置 |
|---|---|
| 左 | x=60 w=320 |
| 中 | x=420 w=440 |
| 右 | x=900 w=320 |

每列顶端 60px 高的列标题条（深蓝底白字），下方 3–5 张浅灰卡片（`fill="#F0F4FA"`），跨列关系用细灰直线（`stroke="#888"` `stroke-width="1"`，**不加箭头**）。

### 3.5 `results_chart` · 结果图表页

调 `templates/charts/<chart_name>.svg`（bar / line / radar / scatter 等），按 [executor-base.md §1.0](../executor-base.md) 批量预读后改字段。学术结果页**默认左图右文**（图占 60% 宽，右侧 3–5 条洞察）。

数据图坐标必须在 Step 7 前跑 [verify-charts](../../workflows/verify-charts.md) 校正。

### 3.6 `formula_step` · 模块化步骤公式页 · **学术默认公式版式**

适合：模型推导每一步独立、需要讲清"为什么这样写"。**默认走这种**。

```
┌─────────────────────────────────────┐
│  标题：Two-Step Floating Catchment   │
├─────────────────────────────────────┤
│ Step 1 设施端：计算供需比             │
│  ┌──────────┐  含义：…                │
│  │  公式 1   │  ─────────             │
│  └──────────┘                         │
├─────────────────────────────────────┤
│ Step 2 居民端：计算可达性             │
│  ┌──────────┐  含义：…                │
│  │  公式 2   │                        │
│  └──────────┘                         │
└─────────────────────────────────────┘
```

- 每个 panel 含：序号徽章 + 步骤名（深色背景白字） + 公式图（PNG / SVG `<image>`） + 含义注释（13px 灰）；
- 公式 PNG 用 matplotlib `\LaTeX` 渲染为透明背景嵌入；
- panel 间距 = 画布高 × 0.04，垂直堆叠。

### 3.7 `formula_paragraph` · 标题分段公式页 · **公式 ≥ 4 时切换**

当一页要塞 4 个以上公式或公式有大段中文推导时：

- 上半页：所有公式列表（小图 + 编号 [`(1)` `(2)` `(3)` `(4)`]）；
- 下半页：分段中文说明（"式(1)由 Frank (2025) 给出..."），每段贴一个公式编号。

### 3.8 `gantt` · 甘特图（Route C 专属）

调 `templates/charts/gantt_chart.svg` 模板。学术开题甘特图硬约束：
- 时间窗口 = 用户 Step 4.2 确认的开题周期（默认 18–24 月）；
- 任务分组：文献调研 / 数据采集 / 方法开发 / 验证 / 写作 / 答辩；
- 每个任务条颜色 = 阶段色（不要每条都用不同色）；
- 关键节点（开题、中期、答辩）用菱形标记。

### 3.9 `conceptual_framework` · 综述概念框架（Route D 专属）

三选一形态：
- **形态 A · 矩阵表**：行 = 主题、列 = 维度 / 时段，单元格 = 代表文献 + 关键观点。直接用 `templates/charts/consulting_table.svg`。
- **形态 B · 思维导图**：调 [cn-academic-spark-technicalroute-engine](../../../CN_Spark_technicalroute/SKILL.md) 的"思考路线类"。
- **形态 C · 演化时间轴**：调 [cn-academic-spark-technicalroute-engine](../../../CN_Spark_technicalroute/SKILL.md) 的"全文思路类"。

由 Strategist 在 Step 4 判定走哪一形态，并在 `design_spec.md §IX` 该页备注 `framework_variant: matrix|mindmap|timeline`。

### 3.10 `evidence_matrix` · 文献证据矩阵（Route D 必备）

原生 SVG 表格，列出每篇代表文献的：作者 / 年份 / 数据 / 方法 / 主结论。直接用 `templates/charts/comparison_table.svg`，**不要**用图片替代。表头深蓝底白字、表身浅灰斑马底（`#F0F4FA` / `#FFFFFF` 交替）、数字 / 年份走 Times New Roman、作者 / 主结论走中文混排（分 tspan）。

### 3.11 `references_page` · 独立参考文献页

Route C / D 必备，Route A / B 可选。

- 字号 10pt（比正文页脚的 8pt 大）；
- 一页 ≤ 18 条，超过则跨页（P{n} / P{n+1}）；
- 编号格式 `[n]`，与全文角标完全一致，不允许跳号 / 重号。

---

## 4. 学术色板与字号

如 `spec_lock.md` 未声明，按下表：

| 角色 | 颜色 | 用途 |
|---|---|---|
| `primary` | `#1F3864` | 标题、底部横幅、节点 |
| `secondary` | `#4472C4` | 副节点、强调链接 |
| `surface` | `#F0F4FA` | 卡片底色、表格斑马 |
| `accent` | `#C00000` | 关键风险 / 警告 / 显著结果（克制使用） |
| `muted` | `#888888` | 引文、说明、灰色辅助 |
| `text_main` | `#222222` | 正文 |

字号（基于 `typography.body = 16px`）：

| 角色 | 字号 | 比例 |
|---|---|---|
| 页面标题 | 32 | 2.0× body |
| 章节小标题 | 22 | 1.4× body |
| 正文 | 16 | body |
| 卡片副解释 | 13 | 0.8× body |
| 引文页脚 | 11 | 0.7× body |
| 角标 `[n]` / 页码 | 9 | 0.55× body |

---

## 5. 学术不允许做的事

1. ❌ 把流程图、研究框架退化为整张位图截图；
2. ❌ 引用了文献但没在页脚列条目；
3. ❌ 中英文混合走单一 font-family；
4. ❌ 引文条目里中文期刊名也用 Times New Roman；
5. ❌ 在普通幻灯片上塞超过 6 条 bullet；
6. ❌ 用渐变 / 阴影 / 3D 立体 / emoji 装饰节点；
7. ❌ 备注区留空白（每页 100–180 字）；
8. ❌ 标题用章节标签（"方法"），必须用**结论式标题**（"基于 HMM 的轨迹识别将精度从 78% 提升至 91%"）。

---

## 6. 与 strategist.md 的对接

Strategist 在 `design_spec.md §IX` 每页 brief 中**必须**额外填写下列学术字段（普通 ppt-master 字段之外）：

```yaml
P05:
  page_rhythm: dense
  content_type: matrix_framework
  page_layouts: 03_content                   # 模板继承
  page_charts: comparison_table              # 主图
  bottom_banner_text: "维度二是流动性研究区别于静态暴露评估的关键尺度"
  citations: ["[1]", "[3]"]                  # 该页角标列表
  framework_variant: null                    # 仅 Route D conceptual_framework 用
```

Strategist 没填这三个新字段时，Executor **必须**回查 `design_spec.md §IX prose`，从段落中提炼后**临时填入**生成（并在产出标注 "auto-filled bottom_banner"），不要静默跳过。

---

## 7. 自检（每页 SVG 完成后）

- [ ] 标题是结论式（说出主张），不是章节标签；
- [ ] `bottom_banner` 在最底层、≤ 30 字；
- [ ] 每个 `[n]` 都能在 `citation_footer` 或独立参考文献页找到；
- [ ] 中英文混排都分了 tspan；
- [ ] 数字 / 拉丁字符走 Times New Roman；
- [ ] 配色不超过 4 种主色 + muted 灰；
- [ ] 不要装饰素材（emoji / 立体 / 渐变）；
- [ ] 复杂流程图走 cn-academic-spark-technicalroute-engine，不本地手画。

跑过 `scripts/svg_quality_checker.py` 后再进入 Step 7。

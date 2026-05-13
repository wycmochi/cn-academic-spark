---
name: cn_spark_technicalroute
description: >
  中文学术技术路线图 / 研究框架图 / 思考脉络图 / 全文流程图的**AI 生图**子技能。
  采用 contract-first + abstract-archetype 工作流：先让用户写一份 Diagram Contract（论证 + panel 映射 + 术语保留），
  再按 archetype × sub_variant 选骨架，从公开学术文献（≥ 5 篇）检索同 archetype 的视觉参考（**没有文献的情况下走 atlas-only fallback**），
  抽风格特征后注入 generic placeholder prompt，调 `image_gen.py`（默认 Gemini 3 Pro Image / nano banana pro）生成。
  支持三大类拓扑：思考路线类（研究背景 / 问题 / 理论 / 意义）、技术方法类（模型思路 / 公式 / 步骤 / 假设）、
  全文思路类（数据 / 方法 / 过程 / 结果）。每类下有 3–4 个 sub_variant 形状骨架。
  可独立调用，也由 CN_Spark_paper2ppt 在某一页嵌图时调用。
---

# CN_Spark_technicalroute · 学术技术路线图（AI 生图，contract-first）

> **核心 pipeline**：`Diagram Contract → Content Schema → 文献样式检索 (or fallback) → 风格画像 → Prompt 合成 → image_gen.py → QA Audit → 嵌入 / 独立输出`

本技能在第二版做了两件大事，避免之前出现的"被例子误导"问题：

1. **archetype 全面抽象化**：references/archetype-*.md 不再写死任何具体学科 / 主题。每个 archetype 拆成 3–4 个 sub_variant 抽象形状骨架（quad / cascade / twin / core-steps / horizontal-pipeline / circular ...），由 `content.yaml` 字段实例化，不绑案例。
2. **三档参考模式 + atlas fallback**：文献检索不到合适机制图时不会卡死。`literature_search.py assess` 自动给出 `literature` / `offline` / `atlas_only` 三档建议，`atlas_only` 模式直接用 `assets/archetype-atlas/` 抽象骨架 SVG 作为风格 anchor。

---

## 三类拓扑（每类下多个 sub_variant）

| Archetype | 何时用 | sub_variant | 视觉档案 |
|---|---|---|---|
| **thinking** | 研究背景 / 问题 / 理论 / 意义（"为什么做"） | `quad` / `cascade` / `twin` | [references/archetype-thinking.md](references/archetype-thinking.md) |
| **method** | 单个模型 / 算法的思想 + 公式 + 步骤 + 假设 | `core-steps` / `vertical-stack` / `formula-grid` / `mechanism-block` | [references/archetype-method.md](references/archetype-method.md) |
| **workflow** | 整篇研究 Data→Methods→Results 链路 | `horizontal-pipeline` / `twin-track` / `funnel` / `circular` | [references/archetype-workflow.md](references/archetype-workflow.md) |

判别规则在每份 archetype 文件顶部。三类共用 [content-schema.md](references/content-schema.md)、[shape-recipes.md](references/shape-recipes.md)、[color-typography.md](references/color-typography.md)、[image-prompt-templates.md](references/image-prompt-templates.md)。

---

## Workflow（8 步，contract → audit）

### Step 1 · 写 Diagram Contract（⛔ BLOCKING）

🚧 **GATE**：用户提供了某种材料（研究描述 / 论文片段 / 主题 + outline）。

> **任何生图任务在出 prompt 之前都必须有 contract**。这是本技能的硬约束（参考 nature-figure 的 figure-contract）。

scaffold：

```bash
python3 scripts/generate_route_image.py contract \
    --out projects/<project_name>/contract.md \
    --project <project_name> \
    --archetype <thinking|method|workflow>
```

骨架已写好，agent 与用户**一起**填以下 8 节（详见 [references/diagram-contract.md](references/diagram-contract.md)）：

1. Core claim（一句话主张）
2. Archetype 与 sub_variant + 选这个的理由
3. Panel / Stage 映射（每条 panel 支撑 core claim 的什么）
4. **Discipline-specific 术语保留清单**（agent 与图像模型都不允许翻译 / 简写）
5. 视觉合同（canvas / color_scheme / density / typography / emphasis_usage）
6. Reference 模式（literature / offline / atlas_only）
7. Reviewer 风险 4 问
8. 验收门槛

⛔ **BLOCKING**：把 contract.md 给用户看，让用户回 "OK" / "改字段 X"。用户确认前不能进 Step 2。

---

### Step 2 · 写 content.yaml + 校验

按对应 archetype 的字段说明（[content-schema.md](references/content-schema.md)）抽 `<project>/content.yaml`。**字段必须完全派生自 contract.md §3**——出现 contract 之外的字段 → 补回 contract（再让用户确认）或从 yaml 删掉。

校验：

```bash
python3 scripts/content_schema.py validate projects/<project_name>/content.yaml
```

- `OK` → 进入 Step 3；
- `OK with N warnings` → 视情况修，或继续；
- `FAIL` → 必须修，不允许带错进 Step 3。

---

### Step 3 · 文献样式检索（不强求成功）

🚧 **GATE**：Step 2 完成 & contract §6 `mode: literature`。

```bash
python3 scripts/literature_search.py emit-plan \
    --topic "<contract §1 中的关键词>" \
    --archetype <thinking|method|workflow> \
    --max 8 \
    --out projects/<project_name>/style_refs/
```

主代理按生成的 `search_plan.json` 用当前 IDE 的 `WebSearch` + `WebFetch`（Claude Code）按优先级抓 figure，调 `record` 子命令写入 `manifest.json`。每张图保留时再跑 `filter --image ...` 复核质量。

详细规则与降级策略：[references/seed_urls.md](references/seed_urls.md)。

---

### Step 4 · 评估检索结果，决定模式

```bash
python3 scripts/literature_search.py assess --out projects/<project_name>/style_refs/
```

输出 `assess.json`：

| score 区间 | recommended_mode | 下一步 |
|---|---|---|
| ≥ 0.6 且 ≥ min_refs 张 | `literature` | Step 5 走文献样式 |
| 0.3–0.6 或 ≥ 3 张本地 | `offline` | 提示用户补 ≥ 3 张参考图（任意结构相似的图），再走 Step 5 |
| < 0.3 | `atlas_only` | 直接跳到 Step 5 用 atlas 模式 |

`atlas_only` 模式的所有规则在 [references/handling-no-references.md](references/handling-no-references.md)。

⛔ **BLOCKING**（建议）：把 assess 结果给用户看。用户可以接受推荐，也可以手动指定 mode（例如检索成功但用户希望走 atlas 风格）。最终 mode 回写到 `contract.md §6`。

---

### Step 5 · 风格特征抽取（可选）

仅当 mode ∈ {`literature`, `offline`} 时执行。主代理直接读 `style_refs/` 中的图（Claude / GPT-4V 多模态），提炼 7 字段到 `style_refs/style_profile.md`：

| 字段 | 候选值 |
|---|---|
| 主色 + 强调色 | 由 `color-typography.md` 命名色板挑 |
| panel 数 | 2 / 3 / 4 / 6 / 多 |
| panel 形态 | 圆角矩形带顶部彩条 / 卡片带左侧 icon / 全宽列 / 含编号徽章 |
| 图标密度 | 极简 / 中 / 高 |
| 字体感 | 中文等线 + 英文衬线 / 全 sans / ... |
| 信息密度 | 留白 / 紧凑 / 海报式 |
| 论证流向 | 横向左→右 / 双列对比 / 自上而下 / 中心辐射 / 环形 |

`atlas_only` 模式跳过这一步。

---

### Step 6 · Prompt 合成

```bash
python3 scripts/generate_route_image.py prompt \
    --archetype <thinking|method|workflow> \
    --content projects/<project_name>/content.yaml \
    --style projects/<project_name>/style_refs/style_profile.md \
    --out projects/<project_name>/prompt.md
```

内部：

1. 读 [references/image-prompt-templates.md](references/image-prompt-templates.md) 取对应 archetype × sub_variant 的英文骨架；
2. 读 [references/shape-recipes.md](references/shape-recipes.md) 注入 RECIPE 行；
3. 读 [references/color-typography.md](references/color-typography.md) 把 `color_scheme` 解析成 HEX 注入 `[COLOR DISCIPLINE]`；
4. 渲染 `[CHINESE CONTENT]` 块逐字列出 content.yaml 的所有中文 / 英文 string；
5. 渲染 `[GLOSSARY]` 块（来自 `content.yaml.glossary_preserve`） + `[NEGATIVE]`。

输出 `prompt.md`。**给用户预览**（contract §6 也建议在此再次让用户审阅最终 prompt）。

---

### Step 7 · 生图（≤ 3 轮重试）

```bash
python3 scripts/generate_route_image.py run \
    --prompt projects/<project_name>/prompt.md \
    --aspect_ratio 16:9 \
    --image_size 2K \
    --refs projects/<project_name>/style_refs/*.png \
    --out projects/<project_name>/output/
```

- 默认 backend = Gemini 3 Pro Image（`IMAGE_BACKEND=gemini`，nano banana pro）；
- 失败重试 1 次（去掉参考图重出）；
- 仍失败时主代理切 backend（如 `IMAGE_BACKEND=qwen` 重跑）；
- 三轮失败 → 走 [handling-no-references.md](references/handling-no-references.md) 档位 C（半成品交付）。

`atlas_only` 模式下 `--refs` 不传任何参考图，prompt 头部已自动加 `[ATLAS-ONLY MODE]` clause。

---

### Step 8 · QA Audit（⛔ BLOCKING）

```bash
python3 scripts/generate_route_image.py audit \
    --image projects/<project_name>/output/route_xxx.png \
    --content projects/<project_name>/content.yaml \
    --contract projects/<project_name>/contract.md \
    --out projects/<project_name>/audit_report.md
```

`audit` 自动跑 hard checks（画布比例、像素宽度、文件大小、无水印 / URL / emoji）。soft checks（panel 数、配色、glossary 逐字保留、流向）由主代理用多模态读图判断，[references/qa-checklist.md](references/qa-checklist.md) 给完整清单。

audit_report 三种结论：

- **PASS** → 进入嵌入或直接交付；
- **CONDITIONAL PASS** → 用 `run --refine "<修正指令>"` 微调一次再重审；
- **FAIL** → 回 Step 6 改 prompt 或 Step 1 改 contract。

---

### Step 9（可选）· 嵌入 paper2ppt

仅当 paper2ppt 在某一页需要这张图时：

```bash
python3 scripts/generate_route_image.py embed \
    --image projects/<project_name>/output/route_xxx.png \
    --target projects/<paper2ppt_project>/svg_output/<NN>_<page>.svg \
    --bbox "60,120,1160,500" \
    --caption "图 N · <caption>"
```

嵌入后再由 paper2ppt 的 finalize_svg → svg_to_pptx 导出 PPTX。

---

## 输出物

```
projects/<project_name>/
├── contract.md                  ← ⛔ 必填（Step 1）
├── content.yaml                 ← Step 2
├── style_refs/
│   ├── ref_001.png … ref_00N.png    ← 文献检索 / 用户上传（Step 3）
│   ├── manifest.json
│   ├── search_plan.json
│   ├── assess.json              ← Step 4
│   └── style_profile.md         ← Step 5（仅 literature / offline 模式）
├── prompt.md                    ← Step 6
├── output/
│   ├── route_<archetype>_<ts>.png   ← ⭐ 主交付物
│   └── route_<archetype>_<ts>_prompt.txt
└── audit_report.md              ← Step 8
```

---

## 与 paper2ppt 的协作

被 paper2ppt 调用时通过 dict 传入：

```yaml
caller: paper2ppt
target_svg: projects/defense_demo/svg_output/06_research_framework.svg
target_bbox: "60,120,1160,500"
target_caption: "图 1 · 研究框架"
archetype: thinking|method|workflow
sub_variant: <optional, 推断>
content_inline: { ... }       # 同 content.yaml 的 dict
glossary_preserve: ["<术语1>", "<术语2>"]
contract_inline: { ... }      # 至少 §1 §3 §4 §5 §6
```

返回：

```yaml
image_path: projects/.../output/route_thinking_20260513.png
audit_passed: true
manifest_json: projects/.../style_refs/manifest.json
contract_path: projects/.../contract.md
```

paper2ppt 拿到 image_path 后用 `<image>` 嵌入对应 SVG 页。

---

## Style Rules · 学术示意图风格硬约束（最终 prompt 都强制）

❌ Negative：

- 3D / 立体 / 阴影 / 渐变 / emoji
- stock photo 风格人物头像
- 水印 / 网址 / 社交 logo
- contract §3 / `content.yaml` 之外的节点 / 编号
- 弯曲 freestyle 箭头（archetype=workflow circular 例外）
- 翻译 / 简写 / 美化 `glossary_preserve` 中任意术语

✅ 强制正向：

- 白底或极浅灰底
- 主色 ≤ 1 + 强调色 ≤ 1 + muted 灰；强调色面积 ≤ 5%
- 中文清晰、可识别、无错位 / 截断 / 乱码
- panel 之间清晰边界
- 整图有论证起点 + 论证终点

---

## References Index

| 文件 | 内容 | 何时读 |
|---|---|---|
| [references/diagram-contract.md](references/diagram-contract.md) | **contract.md** 模板 + 字段定义 | Step 1（必读） |
| [references/content-schema.md](references/content-schema.md) | content.yaml 字段类型与约束 | Step 2 |
| [references/archetype-thinking.md](references/archetype-thinking.md) | thinking 3 个 sub_variant 抽象骨架 | archetype = thinking 时 |
| [references/archetype-method.md](references/archetype-method.md) | method 4 个 sub_variant 抽象骨架 | archetype = method 时 |
| [references/archetype-workflow.md](references/archetype-workflow.md) | workflow 4 个 sub_variant 抽象骨架 | archetype = workflow 时 |
| [references/shape-recipes.md](references/shape-recipes.md) | R1–R10 视觉原子积木（panel / badge / arrow / banner / formula_box / cylinder / tree / mini_chart / symbol_strip / assumption_card） | Step 6 拼 prompt 时 |
| [references/color-typography.md](references/color-typography.md) | 8 套命名色板 + 4 套字体方案 | Step 6 |
| [references/image-prompt-templates.md](references/image-prompt-templates.md) | 三 archetype × 多 sub_variant 的英文骨架 + 中文 CONTENT block + GLOSSARY + NEGATIVE | Step 6 |
| [references/handling-no-references.md](references/handling-no-references.md) | **没文献时**的三档 fallback | Step 4 `mode = atlas_only` 时 |
| [references/qa-checklist.md](references/qa-checklist.md) | hard / soft / reviewer-risk 三段清单 | Step 8 |
| [references/seed_sites.json](references/seed_sites.json) | 学术站点检索 URL 模板 | Step 3 |
| [references/seed_urls.md](references/seed_urls.md) | 站点适配 + 三档降级说明 | Step 3 |

## Assets

| 路径 | 用途 |
|---|---|
| [assets/archetype-atlas/](assets/archetype-atlas/) | **每个 archetype × sub_variant 的抽象骨架 SVG**（atlas_only 模式必备） |
| [assets/gallery/](assets/gallery/) | **用户 / 学科自补**的真实风格参考（按学科 × archetype × sub_variant 分桶；默认空） |

## Scripts

| 脚本 | 子命令 |
|---|---|
| `scripts/literature_search.py` | `emit-plan` / `record` / `offline` / `filter` / `assess` |
| `scripts/generate_route_image.py` | `contract` / `prompt` / `run` / `audit` / `embed` |
| `scripts/content_schema.py` | `validate` |

---

## Fallback Summary

| 情境 | 解决方案 |
|---|---|
| 检索到 ≥ 5 张高质量参考图 | mode=literature，常规走 Step 5–7 |
| 检索到 3–4 张 / 部分缺 DOI | mode=offline，用户补图后继续 |
| 检索 0 张 / 学科冷门 / IDE 无 web 工具 | mode=atlas_only，用 `assets/archetype-atlas/` 兜底 |
| Gemini 失败 | 切 Qwen Image 2.0 重出 |
| 三轮重试仍失败 | 半成品交付：prompt + atlas SVG + contract.md → 用户去网页版生图 |
| panel 太复杂模型理解不准 | 拆成两张子图分别生成，paper2ppt 在同页放两张 |
| 中文渲染错位 | 切 Qwen（中文渲染最稳）或 `--refine "<指令>"` 微调 |

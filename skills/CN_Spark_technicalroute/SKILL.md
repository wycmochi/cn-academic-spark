---
name: cn-academic-spark-technicalroute-engine
description: >
  中文学术技术路线图 / 研究框架图 / 思考脉络图 / 全文流程图的**单图生成**子技能
  （属于 cn-academic-spark bundle 的 TechnicalRoute engine）。
  采用 contract-first + abstract-archetype 工作流：先写 Diagram Contract（论证 + panel 映射 + 术语保留），
  再按 archetype × sub_variant 选骨架，从公开学术文献（≥ 5 篇）+ Custom_gallery 同学科示意图检索视觉参考
  （**没有文献时走 atlas-only fallback**），抽风格特征后注入 generic placeholder prompt，
  优先尝试 `assets/templates/` 矢量模板装配可编辑 SVG，无合适模板时调 `image_gen.py`
  （默认 Gemini 3 Pro Image / nano banana pro）生成 PNG。
  支持三大类拓扑：思考路线类（研究背景 / 问题 / 理论 / 意义）、技术方法类（模型思路 / 公式 / 步骤 / 假设）、
  全文思路类（数据 / 方法 / 过程 / 结果）。每类下有 3–4 个 sub_variant 形状骨架。
  可独立调用（仅生成单张图），也作为 **cn-academic-spark-ppt-engine** Step 5.5 的子流程被串入。
  当用户说"技术路线""研究框架""思考脉络""示意图""概念框架图""全文思路图"时调用本技能；
  组装整套 PPT 的需求请改调 cn-academic-spark-ppt-engine。
---

# cn-academic-spark-technicalroute-engine · 学术技术路线图（AI 生图 + 矢量模板装配，contract-first）

> **安装方式（捆绑 vs 单独）**
>
> - **捆绑安装**（推荐，整个仓库一起装）：本 skill 与 ppt-engine 作为同级目录位于 `skills/` 下。`scripts/generate_route_image.py` 会自动找到同级 `../CN_Spark_paper2ppt/scripts/image_gen.py` 作为生图后端。
> - **单独安装**（只把本目录复制到某个 `~/.claude/skills/` 下时）：请通过环境变量 `IMAGE_GEN_PATH=/abs/path/to/image_gen.py` 显式指向某个能调起 Gemini / Qwen / OpenAI 的生图脚本；或安装 ppt-engine 到任意位置后用 `PAPER2PPT_ROOT=/abs/path/to/CN_Spark_paper2ppt` 覆盖默认查找。两个变量都未设置且找不到同级 paper2ppt 时，`generate_route_image.py run` 会直接报错并打印这两个变量的提示。

> **核心 pipeline**：`Diagram Contract → Content Schema → 文献样式检索 (or fallback) → 风格画像 → Prompt 合成 → image_gen.py → QA Audit → 嵌入 / 独立输出`

本技能在第二版做了两件大事，避免之前出现的"被例子误导"问题：

1. **archetype 全面抽象化**：references/archetype-*.md 不再写死任何具体学科 / 主题。每个 archetype 拆成 3–4 个 sub_variant 抽象形状骨架（quad / cascade / twin / core-steps / horizontal-pipeline / circular ...），由 `content.yaml` 字段实例化，不绑案例。
2. **三档参考模式 + atlas fallback**：文献检索不到合适机制图时不会卡死。`literature_search.py assess` 自动给出 `literature` / `offline` / `atlas_only` 三档建议，`atlas_only` 模式直接用 `assets/templates/` 中匹配 archetype × sub_variant_hint 的可编辑 SVG 作为风格 anchor。

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

### Step 4.5 · Gallery anchor + Template 匹配（⛔ MUST 读 templates_index.json）

> **本步骤决定本图走 Tier 2（可编辑 SVG）还是 Tier 3（PNG）。** 这是从 1.1.0 起 contract → render 链路里**最关键的一步**——之前版本因为没读 `templates_index.json`，导致技术路线图都被默认丢给 image_gen.py 出 PNG，结果普遍过于简单。

#### 4.5.1 选 gallery anchor（always；first read）

读 `assets/Custom_gallery/<discipline>/trans-manifest.json`（13 个学科文件夹中 transportation 已有；其余等用户补图）。按论文 / 用户材料的学科匹配文件夹名，再按 `agentKeywords` 命中筛 1–3 张作为**结构 / 风格 anchor**。

学科文件夹没有 manifest 时直接跳过——**不要编造一个 anchor**。

#### 4.5.2 选可编辑模板（首选交付路径）

```
Read assets/templates/templates_index.json
```

读完按 `contract.md §2 archetype` 收口候选，按打分规则（见 `assets/templates/README.md §选择流程`）打分。Gallery anchor 的结构（panel 数 / 流向 / 双轨 / 环形…）必须和候选模板的 `sub_variant_hint` 一致。

| 命中情况 | 下一步 |
|---|---|
| 至少一个模板得分 ≥ 2 且 `sub_variant_hint` 与 anchor 匹配 | → 在 `spec_lock.md §source_choice` 写 `template_key: <key>`，本图走 **Tier 2（assemble）** |
| 没有模板得分 ≥ 2，或 anchor 结构无对应模板 | → `template_key: none`，本图走 **Tier 3（image_gen）**；gallery anchor 仍作 `--refs` 喂进去 |

#### 4.5.3 写 `design_spec.md` + `spec_lock.md`

用 [`assets/design_spec_reference.md`](assets/design_spec_reference.md) 和 [`assets/spec_lock_reference.md`](assets/spec_lock_reference.md) 骨架填出本项目的两份文件：

- `design_spec.md §IV.1` = Step 4.5.1 选的 gallery anchor 列表 + 提取的结构信号；
- `design_spec.md §IV.2` = Step 4.5.2 选的 `template_key`（或 `none` + 兜底原因）；
- `spec_lock.md §source_choice` = 同上但机器可读；
- `spec_lock.md §slot_map` = 把所选模板 SVG 里的每个 `{{path}}` 占位符映射到 `content.yaml` 的具体路径（**Tier 2 必填，Tier 3 省略**）；
- `spec_lock.md §color_var_map` + `§colors` = 把模板里的 `var(--*)` token 映射到具体 HEX。

**✅ Checkpoint** — `design_spec.md` 与 `spec_lock.md` 已写入；Tier 决定（Tier 2 或 Tier 3）已记录到 `spec_lock.md §source_choice.template_key`。进入 Step 5。

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

### Step 7 · 出图（Tier 2 装配 or Tier 3 生图）

按 Step 4.5.2 的决定分叉：

#### Tier 2 · 装配可编辑 SVG（首选）

当 `spec_lock.md §source_choice.template_key` ≠ `none` 时：

```bash
python3 scripts/generate_route_image.py assemble \
    --spec-lock projects/<project_name>/spec_lock.md \
    --content   projects/<project_name>/content.yaml \
    --out       projects/<project_name>/output/route_<archetype>_<ts>.svg
```

`assemble` 内部：

1. 读 `spec_lock.md`，从 `§source_choice` 取 `template_key`；
2. 读 `assets/templates/<template_key>.svg`；
3. 按 `§slot_map` 把每个 `{{path}}` 替换成 `content.yaml` 对应路径的值（任一占位符未在 slot_map 中映射 → 直接报错，不静默输出）；
4. 按 `§color_var_map` + `§colors` 把 `var(--*)` 替换成具体 HEX；
5. 输出**可编辑 SVG**。

随后可选用 `finalize_svg.py` 同款的 SVG 后处理把它栅格化成 2K PNG，写到同目录 `.png`——这一份用于 audit 与可选嵌入 PPT engine。

#### Tier 3 · AI 生图兜底（PNG）

当 `spec_lock.md §source_choice.template_key = none` 时（即 `templates_index.json` 没有合适模板）：

```bash
python3 scripts/generate_route_image.py run \
    --prompt projects/<project_name>/prompt.md \
    --aspect_ratio 16:9 \
    --image_size 2K \
    --refs <gallery anchors> <style_refs/*.png> \
    --out projects/<project_name>/output/
```

`--refs` 顺序：**Custom_gallery anchor 在前、literature style_refs 在后**——gallery 通常同主题、anchor 价值更高。

- 默认 backend = Gemini 3 Pro Image（`IMAGE_BACKEND=gemini`，nano banana pro）——任务 8 的默认兜底；
- 备选 backend = Qwen Image 2.0（`IMAGE_BACKEND=qwen`，image2）——CJK 渲染最稳；
- 失败重试 1 次（去掉参考图重出）；
- 仍失败时主代理切 backend（gemini → qwen）；
- 三轮失败 → 走 [handling-no-references.md](references/handling-no-references.md) 档位 C（半成品交付）。

`atlas_only` 模式下 `--refs` 不传任何参考图，prompt 头部已自动加 `[ATLAS-ONLY MODE]` clause。

#### Tier 2 失败 → 退化到 Tier 3

`assemble` 报错（如占位符未映射、模板文件丢失、color_var 不全）→ 不强行修，**直接把 `template_key` 改成 `none` 走 Tier 3**。这是任务 8 的"找不到合适模板就出 PNG"的具体落地——不要为了一定出 SVG 而硬塞错模板。

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

**学术抄袭红线核验（每次必跑，无论 Tier 2 还是 Tier 3）**：

主代理用多模态对比 `output/` 里的图 与 `spec_lock.md §source_choice.gallery_refs` 中列出的每张 gallery anchor，确认：

- [ ] 图中出现的**节点文字**全部能在 `content.yaml` / 用户原始材料反查到来源，**未出现仅在 gallery 图里有的文字**；
- [ ] 图中出现的**数据 / 地名 / 模型名 / 作者名**全部来自用户材料，未直接搬运 gallery 图里的实例；
- [ ] gallery anchor 提供的是**结构骨架 + 配色风格**，没有被原样复制（构图相似度 ≤ 70%）。

任一项疑似命中 → audit 直接判 **FAIL**，回 Step 4.5 重选 anchor（同学科换张图）或 Step 1 改 contract §4 glossary 让模型重渲。

audit_report 三种结论：

- **PASS** → 进入嵌入或直接交付；
- **CONDITIONAL PASS** → 用 `run --refine "<修正指令>"` 微调一次再重审；
- **FAIL** → 回 Step 6 改 prompt 或 Step 1 改 contract；学术抄袭红线触发的 FAIL 必须回 Step 4.5。

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
| [assets/templates/](assets/templates/) | **18 张可编辑 SVG 模板**（Tier 2 装配源 / atlas-only fallback 共用） + `templates_index.json` 选择规则 |
| [assets/Custom_gallery/](assets/Custom_gallery/) | **各学科真实学术图**（PNG/JPG，每学科一个 `trans-manifest.json`）作为**结构 / 风格 anchor**（Tier 1，always first read） |
| [assets/design_spec_reference.md](assets/design_spec_reference.md) | 单图级 Design Spec 骨架（重写每个项目的 `design_spec.md` 用） |
| [assets/spec_lock_reference.md](assets/spec_lock_reference.md) | 单图级 Execution Lock 骨架（重写每个项目的 `spec_lock.md` 用） |
| [assets/README.md](assets/README.md) | 四块资产的角色 + 工作流图 + 学术性硬规则 |

## Scripts

| 脚本 | 子命令 |
|---|---|
| `scripts/literature_search.py` | `emit-plan` / `record` / `offline` / `filter` / `assess` |
| `scripts/generate_route_image.py` | `contract` / `prompt` / `assemble` / `run` / `audit` / `embed` |
| `scripts/content_schema.py` | `validate` |

`assemble` 是 1.1.0 新增的 **Tier 2 装配路径**：读 `spec_lock.md` 中选定的 `template_key`，按 `slot_map` 把 `content.yaml` 注入模板 SVG，按 `color_var_map` 替换 `var(--*)`，输出**可编辑 SVG**。

---

## Fallback Summary

| 情境 | 解决方案 |
|---|---|
| `templates_index.json` 有得分 ≥ 2 的模板匹配 archetype + sub_variant | **Tier 2 装配可编辑 SVG**（首选） |
| `templates_index.json` 无合适模板 | **Tier 3 出 PNG**：`image_gen.py`（nano banana pro 默认，image2 备选），把 Custom_gallery + style_refs 作 `--refs` 喂进去 |
| Custom_gallery 同学科空 + 文献检索 < 3 张 | mode=atlas_only，用 `assets/templates/` 中匹配 archetype 的 SVG 注入 prompt（不传 `--refs`） |
| Gemini（nano banana pro）失败 | 切 Qwen Image 2.0（image2）重出 |
| 三轮重试仍失败 | 半成品交付：prompt + 选中模板 SVG + contract.md → 用户去网页版生图 |
| panel 太复杂模型理解不准 | 拆成两张子图分别生成，paper2ppt 在同页放两张 |
| 中文渲染错位 | 切 Qwen（中文渲染最稳）或 `--refine "<指令>"` 微调 |
| Tier 2 装配报错（slot_map 不全 / 模板丢失） | 直接降到 Tier 3 出 PNG，不要硬塞错模板 |

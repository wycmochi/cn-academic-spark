# Diagram Contract · 出图前的"契约"（每张图必填）

> 灵感来自 nature-figure 的 figure-contract。**任何生图任务，agent 必须在生成 prompt / 调 image_gen 之前把这份 contract 写出来**（写到 `<project>/contract.md`），由用户在 ⛔ BLOCKING 节点确认后再继续。
>
> 不写 contract 直接出图是本技能的硬违规。

---

## 为什么需要 contract

技术路线 / 框架 / 思路图不是装饰，而是**一个论证**。先把论证拆清楚，再让图像模型画 — 否则会出现：

- 节点凭空多 / 关键节点漏；
- panel 数过多导致信息密度爆炸；
- 配色和论证不挂钩（红 = 强调？还是仅装饰？没说清楚就用了）；
- 用户拿到图后才发现"这不是我想表达的"。

contract 把这些问题在出图前一次性解决。

---

## Contract 模板（写到 `<project>/contract.md`）

```text
# Diagram Contract — <project_name>

## 1. Core claim（一句话）
<这张图必须捍卫的一句话主张。动词必须有：例如 "本研究通过 A 与 B 的耦合，从 C 维度回答 D 问题"，
而不是 "本研究方法"。>

## 2. Archetype 与 sub-variant
archetype: thinking | method | workflow
sub_variant: <对应的 sub-variant 名，见 archetype-*.md>
reason: <为什么选这个 — 一句话>

## 3. Panel / Stage 映射
（按 archetype 填）

对 thinking：
  - P1: <label> — 支撑 core claim 的什么？(动词+原因)
  - P2: <label> — ...
  - P3: <label> — ...
  - P4: <label> — ...
  - bottom_anchor: <kind + text>，或 "无"

对 method：
  - core_idea: <text>
  - S1: <label> — <做什么>
  - S2: <label> — <做什么>
  - ...
  - assumptions: [list]，或 "无"
  - symbols: [list]，或 "无"

对 workflow：
  - Col 1 / Track A / Input 集合: <label + 包含项>
  - Col 2 / 中间 / Core: <label + 包含项>
  - Col N / 汇合 / Output: <label + 包含项>
  - 列间标签: ["weighted", "extracted", ...]

## 4. Discipline-specific 术语保留清单
（用户希望**逐字保留**的中英文术语；agent 与图像模型都不允许翻译 / 简写 / 美化）

  - <术语 1>
  - <术语 2>
  - ...

## 5. 视觉合同
canvas: 16:9 | 4:3 | square | long
color_scheme: <从 color-typography.md 中选一个命名色板，或 "discipline_default">
density: airy | balanced | dense
icon_density: low | medium | high
typography: cn_yahei_en_times (default) | cn_songti_en_inter | other
emphasis_usage: <核心问题 / 主张 / 警示，会用强调色一次的地方，或 "无">

## 6. Reference 模式
mode: literature | offline_user_uploads | atlas_only
expected_refs_count: <≥5 (literature) / ≥3 (offline) / 0 (atlas_only)>
note: <若 atlas_only，写明 fallback 原因 — 例如 "学科冷门，文献检索 0 命中"，会触发 handling-no-references.md>

## 7. Reviewer 风险（出图前回答）
Q1. 这张图最可能被听众挑战的一个点是什么？
A1.
Q2. 如果 panel 数减半，论证还成立吗？哪些可以合并 / 删除？
A2.
Q3. 任意一个被引用的"他人方法 / 数据 / 概念"是否在 PPT 页脚有 GB/T 7714 引用？
A3.
Q4. 颜色编码（主色 / 强调 / 灰）是否承担信息含义？还是只是装饰？
A4.

## 8. 验收门槛（生图后逐条核对）
- [ ] 每一个可见文本都对应 contract §3 中的某条
- [ ] 没有 contract 之外的节点 / 编号 / 引用
- [ ] §4 术语清单中的每一项都**逐字出现**
- [ ] 配色和 §5 一致
- [ ] §7 中识别的风险点已经在图中被回应
```

---

## ⛔ BLOCKING GATE

在 SKILL.md Step 4（prompt 合成）之前，**必须**：

1. 把 contract.md 写完；
2. 把它给用户看，让用户回答"OK / 修改字段 X"；
3. 用户确认后才能调 `generate_route_image.py prompt`。

跳过 contract 直接生 prompt 是硬违规。

---

## Contract 与 content.yaml 的关系

| 文件 | 谁写 | 用途 |
|---|---|---|
| `contract.md` | agent 起草 → 用户确认 | 论证 + 验收标准；人读 |
| `content.yaml` | agent 从 contract + 用户原材料抽 | 结构化字段，喂给 prompt 合成；机器读 |

`content.yaml` 字段必须**完全派生自** `contract.md`，不能多 / 不能少。如果 yaml 出现了 contract 没有的字段，要么补到 contract（用户再确认一次），要么从 yaml 删掉。

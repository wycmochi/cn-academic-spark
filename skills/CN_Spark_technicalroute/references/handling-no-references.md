# Handling No-References · 文献检索 + Custom_gallery 都没合适图时的 fallback

> 学科冷门 / 关键词受限 / 站点不可访问 / IDE 无 web 工具时，文献样式检索可能**返回 0 张可用图**；同时 `assets/Custom_gallery/<discipline>/` 也可能因为该学科尚未补图而为空。本文件规定此时的 fallback 路径，保证 pipeline 不会卡死。
>
> **位置**：本文件描述的是 Step 7 Tier 3（AI 生 PNG）路径中的**参考图来源兜底**——当 Custom_gallery + literature 检索两路都拿不到 anchor 时如何继续出 PNG。它**不影响** Step 7 Tier 2（模板装配）的判定；Tier 2 只看 `templates_index.json` 是否打分命中，与本文件无关。

---

## 触发条件（任一即触发）

1. `literature_search.py assess <out_dir>` 返回 `score < 0.5`（即可用参考图 < 3 张）；
2. `manifest.json` 中 `refs` 数量 < `min_refs`（默认 5）；
3. 用户主动在 contract.md 中标记 `reference_mode: atlas_only`；
4. IDE 没有 `WebSearch` / `WebFetch` 且用户也未上传参考图；
5. **Custom_gallery 同学科文件夹为空或无 `trans-manifest.json`**——即"既无文献参考、也无 gallery 参考"的双重缺失情景。

---

## Fallback 三档（按可用资源逐档降级）

### 档位 A · 用户能补 ≥ 3 张参考图

最优 fallback：让用户上传任意 3 张**结构相似**的图（不必同主题、不必同学科），跳到 offline 模式：

```bash
python3 scripts/literature_search.py offline \
    --hints <user_uploaded_dir> \
    --out <project>/style_refs/
```

> "结构相似"指：archetype 一致（同是 thinking / method / workflow），sub_variant 接近（同是 quad / core-steps / horizontal-pipeline 等）。学科 / 主题 / 文字内容可以完全不同，因为风格参考只取**视觉骨架**。

### 档位 B · 用 `assets/templates/` 中匹配 archetype 的 SVG 作风格 anchor

用户没上传图，但接受标准学术 infographic 风格：用 `assets/templates/` 中对应 archetype + sub_variant_hint 的可编辑 SVG 作为风格 anchor（即使本图整体走 Tier 3 出 PNG）：

```bash
python3 scripts/generate_route_image.py prompt \
    --content <project>/content.yaml \
    --reference-mode atlas_only \
    --out <project>/prompt.md
```

`prompt` 子命令在 `atlas_only` 模式下：

1. 读取对应 archetype 的 atlas SVG 中的形状描述（不读用户的检索结果）；
2. prompt 的 `[STYLE PROFILE]` 字段直接来自 atlas SVG 的注释段；
3. **不**给图像模型传 reference image — 走纯文本到图模式；
4. 在 prompt 头部插入：

```
[ATLAS-ONLY MODE]
No literature reference images available. Render using ONLY the shape recipes
specified in [STRUCTURE] and the discipline-default color discipline from
[COLOR DISCIPLINE]. Default to a clean, restrained, academic-poster look with
generous white space, thin strokes, flat fills, and no decorative flourishes.
Treat the [STRUCTURE] block as the single source of layout truth.
```

### 档位 C · 模型生不出可用图

档位 B 仍失败 → 触发"半成品交付"：

1. 把当前 prompt + atlas SVG + content.yaml + contract.md 一并打包；
2. 输出指引让用户去 ChatGPT / Gemini / Midjourney 网页版手动生成；
3. 由 SKILL.md Step 6 验收清单确认。

---

## 文献缺失对 contract 的影响（重写流程）

如果 `assess` 失败，**回到 contract.md** 重新填一行：

```text
## 6. Reference 模式
mode: atlas_only           # 从 literature 降级
expected_refs_count: 0
note: <为什么没找到 — 例如 "学科为某新兴交叉领域，Google Scholar 与 Semantic Scholar 均 < 3 命中"; 或 "用户上传的 PDF 引用文献未提供 figure URL，且关键词 X 在中文数据库未命中">
```

降级后再让用户**再次确认 contract**，避免出现"用户以为我们用了文献参考但其实没有"的误差。

---

## 与 `assets/templates/` 的关系

`assets/templates/` 提供 18 张可编辑 SVG 模板（详见 `assets/templates/templates_index.json` + `assets/templates/README.md`）。这些 SVG 在本 skill 中担**两个角色**：

1. **Tier 2 装配源**——主流路径下，`generate_route_image.py assemble` 直接把 content.yaml 注入这些 SVG，产出可编辑成品；
2. **atlas-only fallback**（本文件场景）——当文献检索 + Custom_gallery 双双拿不到 anchor 时，`prompt --reference-mode atlas_only` 把对应模板的几何骨架 / 占位符布局 / 命名色板抽出来注入 prompt（不传 `--reference` 图），让模型按"标准学术 infographic"风格出 PNG。

两个角色用同一批 SVG 文件，只是消费方式不同。Tier 2 是"装"（替换占位符）；atlas-only fallback 是"看"（提取结构特征）。

---

## 何时**不要**触发 fallback

- 已经有 ≥ 5 张参考图，质量评分 ≥ 0.5 — 此时按正常 SKILL.md Step 2 流程；
- 用户上传了已有论文 figure 想"重绘 / 风格化" — 走档位 A 的 offline 模式即可，不算 fallback；
- 文献中有合适的 figure 但**用户主动要求不参考**（如担心版权 / 风格冲突） — 写到 contract `reference_mode: atlas_only` 并照档位 B 走。

---

## 校验

`generate_route_image.py audit` 在 PNG 出图后会复核：

- atlas_only 模式下生成的图是否仍然符合 archetype 视觉约束（panel 数 / 流向 / 配色）；
- atlas_only 模式下 reviewer-risk Q4（"配色是否承担信息含义"）是否在图中体现；

不符合则触发 SKILL.md Step 6 的 `--refine` 重出循环。

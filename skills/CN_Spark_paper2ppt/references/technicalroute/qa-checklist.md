# QA Checklist · 出图后交付前的验收

> 灵感来自 nature-figure 的 qa-contract。**任何 PNG 在交付给用户 / 嵌入到 paper2ppt SVG 之前，必须通过这份 checklist**。由 `scripts/generate_route_image.py audit` 半自动执行 + 主代理 / 用户人工补完。

---

## 三段验收（按严格度递增）

### 1) Hard checks（机器可判，audit 子命令自动跑）

- [ ] **画布比例** — 与 `contract.md §5 canvas` 一致（误差 ≤ 2%）
- [ ] **像素宽度** — ≥ 1600 px（嵌入 PPT 不糊）
- [ ] **文件大小** — ≥ 200 KB（< 200KB 通常意味着画面过空 / 退化）
- [ ] **无水印 / 网址 / 社交 logo** — OCR 抽出全部文本后 grep `http` / `©` / `watermark` / 已知 stock 服务商名 → 0 命中
- [ ] **无 emoji** — OCR 抽出文本中无 Unicode emoji 块（U+1F300–U+1FAFF）

### 2) Soft checks（视觉判，主代理多模态读图判断）

- [ ] **每一个可见文本**都对应 `contract.md §3 panel/stage 映射` 中的某一条
- [ ] **没有 contract 外的节点 / 编号 / 引用**
- [ ] **`contract.md §4 术语保留清单`中的每一项都逐字出现**（中英文混合时分别检查）
- [ ] **配色不超过 4 种**主色（primary / secondary / accent / muted），白底深字保留
- [ ] **强调色（accent）使用面积 ≤ 5%**，且承载语义（核心问题 / 主张 / 警示），不只是装饰
- [ ] **panel 数与 contract §3 一致**
- [ ] **论证流向**（自上而下 / 左→右 / 环形 / 双轨汇合）与 archetype × sub_variant 一致
- [ ] **公式区底色为浅灰 / 白**（不是饱和色块）— 仅 archetype=method 时检查
- [ ] **列间过渡箭头**带 italic muted 标签 — 仅 archetype=workflow horizontal-pipeline 时检查
- [ ] **底部强调横幅**只有 0 或 1 条 — 不允许多条互相竞争注意力
- [ ] **中文文字无错位 / 无截断 / 无乱码 CJK**
- [ ] **中英文混排**：英 / 数字 / 拉丁字符可肉眼判出 serif（如 Times）；中文为 sans-serif（如 Yahei）

### 3) Reviewer-risk checks（高严格度，对应 contract §7）

- [ ] §7 Q1 识别的"最可能挑战点"在图中已被回应（例如 contract 提到"听众会问 panel 4 是不是和 panel 2 重复"→ 图中应有视觉区分让 P2 / P4 看上去不同）
- [ ] §7 Q2 panel 减半后论证不成立（即每个 panel 都是必要的）
- [ ] §7 Q3 引用的"他人方法 / 数据 / 概念"在 PPT 页脚已有 GB/T 7714 完整条目（这步在 paper2ppt 嵌入完成后做）
- [ ] §7 Q4 颜色编码承担信息含义，不只是装饰

---

## audit 子命令的输出

```bash
python3 scripts/generate_route_image.py audit \
    --image <project>/output/route_xxx.png \
    --contract <project>/contract.md \
    --content <project>/content.yaml \
    --out <project>/audit_report.md
```

输出形如：

```markdown
# Audit Report — route_thinking_20260513.png

## Hard checks (5/5 passed)
- canvas: 16:9 ✓
- width: 1920 px ✓
- size: 384 KB ✓
- no watermark / URL ✓
- no emoji ✓

## Soft checks (manual review required for 4 items)
- contract §3 panels all visible: AUTO-CHECK skipped, please review
- glossary preserve: AUTO-CHECK matched 4/5; "[术语 X]" missing or misrendered — needs manual confirm
- color palette ≤ 4 hues: AUTO-CHECK passed (dominant colors: #1F4E79 #2E7D32 #C00000 #888888)
- accent area ≤ 5%: AUTO-CHECK passed (estimate 3.2%)
- ...

## Decision
- [ ] PASS — ready for embed
- [x] CONDITIONAL PASS — fix missing glossary term then PASS
- [ ] FAIL — regenerate

## Recommended `--refine` instruction
"在底部红色横幅中把 '<term-replaced-by-model>' 改回 '<term-from-glossary>'，其他不变。"
```

主代理把 audit_report 给用户看：

- PASS → 直接进入 SKILL.md Step 6.2 嵌入；
- CONDITIONAL PASS → 让用户决定接受还是用 `--refine` 微调；
- FAIL → 回到 Step 5 重出，或回到 Step 4 改 prompt。

---

## 多次重出后仍不过的处理

最多重出 **3 轮**。每轮失败后：

- 第 1 次失败 → `--refine` 加 negative，原 prompt 不变；
- 第 2 次失败 → 切换 backend（gemini → qwen），原 prompt 不变；
- 第 3 次失败 → 触发 [handling-no-references.md](handling-no-references.md) 档位 C（半成品交付，用户去网页版手动生成）。

每一轮都把失败信息追加到 `audit_report.md`，便于复盘。

---

## QA 时的隐私规则（继承自 nature-figure）

- audit_report 中**不要**暴露用户私有路径、模板内部名、prompt 完整内容；
- 提到失败项时用"图中第 N 个 panel"或"右下角"等位置描述，不引用模型 ID / API key / 内部 reference 文件名。

# `assets/` · TechnicalRoute engine resource pack

> **本目录是 TR engine 的"装配源"。** `references/` 告诉 agent 怎么思考、怎么写 contract、怎么打分；`scripts/` 告诉机器怎么跑；本目录则提供**可直接拼装/参考的素材**：模板 SVG、学科示意图、单图级 design_spec / spec_lock 骨架。

## 目录速览

```
assets/
├── README.md                    ← 本文件
├── design_spec_reference.md     ← 单图级 Design Spec 骨架（人读，重写每个项目的 design_spec.md 用）
├── spec_lock_reference.md       ← 单图级 Execution Lock 骨架（机器读，renderer / template-assembler 必读）
├── templates/                   ← 可编辑 SVG 模板（首选装配源）
│   ├── README.md
│   ├── templates_index.json     ← ⭐ 选择规则（Pick for X / Skip if Y）
│   └── <18 个学术示意图模板 SVG>
└── Custom_gallery/              ← 各学科真实学术图（结构 / 风格参考，禁止内容抄袭）
    ├── README.md
    └── <discipline>/            ← agronomy / biology / chemical / computer-science /
        ├── trans-manifest.json  ←  economics / environmental-science / geography /
        └── *.png / *.jpg        ←  humanities-socialsciences / management /
                                  ←  materials-science / mathematics / medicine /
                                  ←  physics / transportation
```

## 四块各自的角色

| 资产 | 是什么 | 谁读 | 何时读 |
|---|---|---|---|
| `templates/` | 我们手写的**抽象结构骨架**（可编辑 SVG，含占位符） | 主代理 + `generate_route_image.py` | Step 4 评估 / Step 6 prompt 合成 / Step 7 渲染——**所有走"装配"路径的任务都必读 `templates_index.json`** |
| `Custom_gallery/` | 用户 / 学科收藏的**真实学术图**（PNG/JPG，可能受版权保护） | 主代理（多模态读图） | Step 3 文献样式检索找不到够多 ≥ 5 张参考时，从同学科文件夹里取 1–3 张作风格 anchor |
| `design_spec_reference.md` | **单图级**视觉设计书骨架（重写每个项目的 design_spec.md 用） | 主代理 | Step 5 风格抽取完成、要写当前项目 `design_spec.md` 时 |
| `spec_lock_reference.md` | **单图级**渲染执行锁骨架（重写每个项目的 spec_lock.md 用） | 主代理 + renderer | 写完 `design_spec.md` 后立即生成；Step 6 prompt 合成与 Step 7 渲染都必读 |

## 工作流（contract → audit，asset 层视角）

下面只画 asset 怎么被消费——完整 8 步在 [`../SKILL.md`](../SKILL.md)。

```
contract.md          → 写 §2 archetype × sub_variant、§5 视觉合同
   │
   ├──→ content.yaml         (typed content；字段必须派生自 contract §3)
   │
   ├──→ Step 3-4 文献检索 + assess  (literature / offline / atlas_only)
   │       └──→ 同学科 Custom_gallery/<discipline>/trans-manifest.json
   │            匹配触发词 → 取 1–3 张作风格 anchor
   │
   ├──→ design_spec.md       (本目录 design_spec_reference.md 骨架填出)
   │     §III archetype × sub_variant   (← 来自 contract.md §2)
   │     §IV.1 template_key             (← 来自 templates_index.json 打分)
   │     §IV.2 gallery_refs             (← 来自 Custom_gallery 匹配)
   │     §V colors / §VI typography     (← 来自 contract.md §5 或上游 PPT engine deck)
   │
   ├──→ spec_lock.md         (本目录 spec_lock_reference.md 骨架填出)
   │     # canvas / archetype / colors / typography / slot_map / color_var_map / glossary_preserve …
   │
   ├──→ prompt.md            (Step 6；从 spec_lock.md 拉值)
   │
   ├──→ 渲染分叉：
   │     ├─ template_key 命中 → renderer 读 templates/<key>.svg 做 slot 替换 → 输出 .svg + .png
   │     └─ template_key=none → image_gen.py 调 backend，参考图 = Custom_gallery + style_refs/
   │
   └──→ audit_report.md      (Step 8；按 spec_lock.md 校 colors / glossary_preserve / 比例)
```

## 优先级硬规则（**学术性保护**）

1. **装配 > 生图**：`templates_index.json` 里能匹配到 ≥ 2 分的模板，必须走装配路径（编辑 SVG，矢量可编辑）。只有都打不上分时才落到 AI 生图（输出 PNG）。
2. **Custom_gallery 仅作参考**：里面图片的**结构 / 配色 / 流向**可以学，**节点文字 / 数据 / 地名 / 模型名**绝对不能抄。所有出现在最终图里的文字必须能在 `content.yaml` / 用户原始材料里反查到来源。这条约束由 `contract.md §4 glossary_preserve` 与 `spec_lock.md §forbidden` 双重保护。
3. **配色 / 字体跟 caller**：当 caller = `cn-academic-spark-ppt-engine` 时，本图必须用 PPT engine deck 级 `design_spec.md` 的配色 / 字体——TR engine 的 `design_spec.md §V §VI` 直接复制过来，不能自创一套与 deck 漂移。
4. **glossary_preserve 字节级保留**：`contract.md §4` 列出的术语，在最终图里**逐字保留**——不翻译、不缩写、不大小写折叠。renderer 与 audit 双重校验。

## 怎么扩展

| 想加什么 | 改哪 |
|---|---|
| 新的可编辑 SVG 模板 | `templates/<key>.svg` + 更新 `templates/templates_index.json` 三处（`meta.total` / `archetypes.<X>.templates` / `templates.<key>`） |
| 新学科的参考图 | 在 `Custom_gallery/<discipline>/` 放图（PNG/JPG）+ 同目录写 `trans-manifest.json`（参考 `transportation/trans-manifest.json` 格式） |
| 新的 archetype | 先在 `../references/archetype-*.md` 加 sub_variant 骨架；再回来在 `templates_index.json.archetypes` 加一个分组；最后视情况加新模板 |
| 单图设计骨架的字段 | 改 `design_spec_reference.md`（人读骨架）+ 对应改 `spec_lock_reference.md`（机器锁），两边必须同步 |

## 与 PPT engine 同名资产的关系

| 资产 | 本目录（TR engine） | `../../CN_Spark_paper2ppt/templates/` |
|---|---|---|
| `templates/` | 18 张为**单图独立交付**优化的 SVG（viewBox 更宽、留白更多、字号更大） | 70+ 张 deck 级图表 / 信息图模板，跨多页风格统一 |
| `<archetype>_*` 同名文件 | 视觉风格一致，但参数偏单图 | 视觉风格一致，参数偏 deck |
| `templates_index.json` | 按 TR engine 三类 archetype 分组（thinking / method / workflow） | 按 paper2ppt 9 类分组（comparison / trend / composition / metrics / analysis / process / strategy / architecture / infographic / table） |

两边各自维护，**不要硬链接 / 互相 import**——结构分歧是有意的。

---

详细消费方式见 [`../SKILL.md`](../SKILL.md) Step 1–8 与 [`templates/README.md`](templates/README.md) / [`Custom_gallery/README.md`](Custom_gallery/README.md)。

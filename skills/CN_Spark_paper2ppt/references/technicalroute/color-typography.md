# Color & Typography · 命名色板与字体规则

> 本文件给所有 archetype 共享的命名色板与字体规则。`content.yaml.color_scheme` 必须从这里选一个名字，**不允许**在 yaml 里直接写 HEX。HEX 由本文件统一维护，方便日后切换 / 跟随学校色 / 跟随期刊色。

## 命名色板（直接在 `content.yaml.color_scheme` 中使用其名）

| 名称 | primary | secondary | accent | muted | 适用学科示意 |
|---|---|---|---|---|---|
| `academic_blue_green` | `#1F4E79` | `#2E7D32` | `#C00000` | `#888888` | 地理 / 城市 / 公共卫生 / 社会科学 |
| `academic_blue_teal` | `#005B8C` | `#00897B` | `#FFB300` | `#888888` | 经济 / 管理 / 教育 / 综合 |
| `academic_purple_green` | `#7E57C2` | `#43A047` | `#EF5350` | `#757575` | 机器学习 / 计算 / 数据科学 |
| `academic_navy_amber` | `#1A237E` | `#FF8F00` | `#D32F2F` | `#888888` | 工程 / 材料 / 物理 |
| `academic_indigo_lime` | `#283593` | `#9E9D24` | `#C62828` | `#888888` | 生物 / 化学 / 农学 |
| `academic_blue_pink` | `#1565C0` | `#C2185B` | `#FBC02D` | `#888888` | 医学 / 临床 / 公共健康 |
| `academic_grey_red` | `#37474F` | `#C62828` | `#FFB300` | `#90A4AE` | 法律 / 政策 / 风险 |
| `academic_neutral_blue` | `#1F4E79` | `#90A4AE` | `#C00000` | `#888888` | 极简学院风（综述讲解） |

每条色板都满足：

- primary 与 secondary 的色相相距足够远，便于辨识；
- accent 只在"核心问题 / 主张 / 警示"位置用，且整图占比 ≤ 5%；
- muted 用于引文 / 说明 / 弱信息，在白底上有 ≥ 4.5:1 对比度（AA 级）。

## `discipline_default` 别名

`content.yaml.color_scheme: discipline_default` 时按学科自动落到上面某条：

| 学科关键词（出现在 title / subtitle） | 落到 |
|---|---|
| 城市 / 地理 / 公共卫生 / 暴露 / GIS / 流动性 | `academic_blue_green` |
| 机器学习 / 深度学习 / 神经网络 / 计算 / 算法 | `academic_purple_green` |
| 医学 / 临床 / 病人 / 疾病 / 影像 | `academic_blue_pink` |
| 政策 / 法规 / 风险 / 评估 / 治理 | `academic_grey_red` |
| 经济 / 管理 / 教育 / 经营 | `academic_blue_teal` |
| 工程 / 材料 / 物理 / 力学 | `academic_navy_amber` |
| 生物 / 化学 / 农学 / 生态 | `academic_indigo_lime` |
| 其他 / 无法判定 | `academic_neutral_blue` |

判定关键词不在标题里时，本字段保留为 `discipline_default` 并在 prompt 中标注让图像模型走"中性学院蓝"。

## 角色 → HEX 在 prompt 中的注入

`generate_route_image.py prompt` 把 `color_scheme` 解析后注入：

```
[COLOR DISCIPLINE]
primary  = #1F4E79  (用于 panel 主色、step 标题条、核心节点)
secondary = #2E7D32 (用于次要 panel、辅助节点、过渡)
accent   = #C00000  (仅用于核心问题 / 主张横幅，整图占比 ≤ 5%)
muted    = #888888  (引文 / 说明 / 弱信息)

Do NOT introduce hues outside this 4-color budget except for:
  - pure white (#FFFFFF) backgrounds
  - dark text (#1A1A1A or muted) for body copy
  - alpha-modulated tints of the above 4 (e.g., primary @ 20% for surface fills)
```

## 字体规则

### 默认（学术汇报 95% 场景适用）

| 用途 | 字体族 |
|---|---|
| 中文（标题 / bullet / 标签） | `Microsoft YaHei` / `Source Han Sans SC` |
| 英文 + 数字 + 拉丁字符 | `Times New Roman` |
| 公式 LaTeX | `Computer Modern` / `STIX Two Math` 风格的衬线（图像模型按 "LaTeX style" 渲染即可） |
| 代码 / 模型名 | `Inter Mono` / `Roboto Mono` |

### 切换条件

| `content.yaml.typography` | 用途 |
|---|---|
| `cn_yahei_en_times` (default) | 答辩 / 综述 / 大多数学术场景 |
| `cn_songti_en_inter` | 论文风、严肃文献综述 |
| `cn_yahei_en_inter` | 计算 / 工程 / 互联网氛围 |
| `cn_pingfang_en_helvetica` | 极简学院 / 设计学院 / 建筑 |

## 字号（基于 1080×1920 输出，**不是** SVG 1280×720）

| 角色 | 字号 |
|---|---|
| 主标题 | 36–44 |
| 段标题（panel label） | 22–28 |
| Bullet 主文 | 16–20 |
| Bullet 副解释 / 含义 | 13–15 |
| 公式 LaTeX | 24–30（变量与数字） |
| 角标 / 引用 / 时间戳 | 10–12 |

## 不要做的事

- ❌ 在一张图里出现 ≥ 5 种饱和色相；
- ❌ 红色 / 强调色用在装饰位置（必须承载语义）；
- ❌ 中英文走同一种字体（中英混排必须分 family）；
- ❌ 公式区用饱和底色（必须浅灰 `#F5F8FB` 或白）；
- ❌ 在 yaml 里直接写 HEX（必须用本文件的命名色板）。

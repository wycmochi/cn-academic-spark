# Academic Formula Rendering

这是学术 PPT 中公式页的强制流程。目的：把“公式标题 + 完整公式 + 变量解释”渲染成一个透明 PNG，再作为单个图片对象插入 PPT，避免公式和解释被拆成多个互相重叠的文本框。

## 触发条件

出现以下任一情况必须使用本流程：
- 论文包含方法、指标、模型、损失函数、估计策略或解释变量的关键公式；
- `design_spec.md` 声明 `visual_requirement: formula_png` 或 `formula_block_png`；
- 页面内容类型是 `formula_step` 或 `formula_paragraph`；
- 幻灯片需要解释公式变量。

## 公式选择规则

先分析用户提供的论文或文本，再提取主方法、主模型、核心指标下的公式。优先保留：
1. 定义方法、模型、目标函数、估计量、评价指标或推断规则的公式；
2. 后文结果或解释反复引用的公式；
3. 引入高频变量的公式；
4. 口头汇报中理解研究逻辑所必需的推导式。

不要只展示一个公式而遗漏同一主步骤下的关键公式。单页最多放 5 个公式块，超出后分页。

## 必需 JSON

每个重要公式都先写一个公式块 JSON，再渲染 PNG。所有解释文字必须使用中文；`formula_role` 必须是中文公式标题，`definition_label` 固定为 `式中：`。

```json
{
  "formula_id": "formula_01",
  "source_location": "第3节 / 式(1) / 第5页",
  "formula_role": "客流恢复力指标",
  "latex": "<忠实转写的 LaTeX>",
  "definition_label": "式中：",
  "variables": [
    {"symbol": "C_{r,i}", "meaning": "站点 i 的客流恢复力，数值越大表示累计损失越小"},
    {"symbol": "P_i(o)", "meaning": "站点 i 在正常状态下第 o 天的客流量"}
  ],
  "png_path": "images/formulas/formula_block_01.png",
  "status": "rendered"
}
```

占位参考见 `templates/formula/formula_block_schema.json`。渲染前替换所有 `{{...}}`，不要把 `Variables`、`Where` 或 `???` 写入最终 JSON。

## 渲染命令

首选命令：

```bash
python3 scripts/latex_formula_to_png.py --block-json <project_path>/notes/formula_01.json --out <project_path>/images/formulas/formula_block_01.png --font-size 30 --dpi 260 --color "#111111"
```

单公式渲染只用于诊断；最终 PPT 中解释型公式必须使用公式块 PNG：

```bash
python3 scripts/latex_formula_to_png.py --latex "<latex>" --out <project_path>/images/formulas/formula_01.png --font-size 30 --dpi 260 --color "#111111"
```

## 插入方式

先读取 `templates/formula/formula_templates_index.json`，选择 `formula_explanation_block`。SVG 模板只是图片壳，公式内容必须作为一个 PNG 插入：

```svg
<g id="formula_block_01" data-content-type="formula_block" data-formula-id="formula_01">
  <image id="formula_block_01_png" data-formula-png="true" data-formula-block-png="true" href="images/formulas/formula_block_01.png" x="32" y="130" width="1216" height="120" preserveAspectRatio="xMidYMid meet"/>
</g>
```

规则：
- 一个被解释的公式对应一个公式块 PNG。
- PNG 内部包含中文公式标题、公式、`式中：` 和中文变量解释。
- 插入 SVG 时保留 `data-formula-png="true"` 和 `data-formula-block-png="true"`。
- 多个公式块之间使用灰色 1.5pt 虚线分隔。
- 公式 PNG、文本框、分隔线不得重叠。
- 公式块 PNG 放在 `<project_path>/images/formulas/`。
- 在 `design_spec.md` Image Resource List 和 `spec_lock.md images` 中记录 `usage: formula_block_png`。

## QA

导出前检查：
- 每个公式页至少有一个 `<image ... data-formula-block-png="true">` 或 `images/formulas/formula_block_*.png`；
- 单页公式块不超过 5 个；
- 公式角色、变量解释、`式中：` 没有被拆成 SVG 文本框；
- 公式块 PNG 文件在 `finalize_svg.py` 前已经存在；
- 公式解释文字为中文；
- 相邻公式块和分隔线没有重叠。

若 mathtext 无法解析某个 LaTeX 命令，先简化为 matplotlib 支持的写法；只有记录限制后才使用透明截图兜底。

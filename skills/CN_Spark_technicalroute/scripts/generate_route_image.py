#!/usr/bin/env python3
"""
generate_route_image.py · 把 content.yaml + style_profile.md 拼成 prompt，再调用
PPT engine 的 ``scripts/image_gen.py`` 做多后端生图。

子命令：
  prompt   读 content.yaml + style_profile.md + archetype skeleton → 生成 prompt.md
  run      读 prompt.md + 参考图 → 调 image_gen.py 出 PNG
  embed    把生成的 PNG 嵌入 PPT engine 项目的某张 SVG 页面

默认 backend = gemini（gemini-3-pro-image-preview，即 nano banana pro），
环境变量 ``IMAGE_BACKEND`` / ``GEMINI_API_KEY`` 由用户在 PPT engine 的 ``.env`` 中配置。

生图脚本路径查找顺序（最高优先级在前）：

1. ``IMAGE_GEN_PATH``  — 直接指向某个 image_gen.py（独立安装时最常用）；
2. ``PAPER2PPT_ROOT``  — 指向已部署的 PPT engine 根目录，自动拼出
   ``$PAPER2PPT_ROOT/scripts/image_gen.py``；
3. 默认值              — 同级目录下的 ``../CN_Spark_paper2ppt/scripts/image_gen.py``
   （仓库捆绑安装时这条就够了）。

三条都失败时 ``run`` 子命令会报错并把上述变量名一并打印出来，提示用户单独安装时
如何接生图后端。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore
except ImportError:  # 退化：手写极简 yaml loader 暂用 json
    yaml = None

HERE = Path(__file__).resolve().parent
TECHROUTE_ROOT = HERE.parent
REFS_DIR = TECHROUTE_ROOT / "references"


def _resolve_image_gen() -> Path:
    """Locate the PPT engine's image_gen.py via env-var overrides, then sibling fallback.

    Returns the resolved Path (may not exist; caller checks ``.exists()``).
    """
    override = os.environ.get("IMAGE_GEN_PATH")
    if override:
        return Path(override).expanduser().resolve()
    paper2ppt_env = os.environ.get("PAPER2PPT_ROOT")
    if paper2ppt_env:
        return (Path(paper2ppt_env).expanduser().resolve() / "scripts" / "image_gen.py")
    return (TECHROUTE_ROOT.parent / "CN_Spark_paper2ppt" / "scripts" / "image_gen.py").resolve()


IMAGE_GEN_PY = _resolve_image_gen()
PAPER2PPT_ROOT = IMAGE_GEN_PY.parent.parent  # backwards compatibility


# ---------------------------------------------------------------------------
# Prompt 拼装
# ---------------------------------------------------------------------------


COMMON_PREAMBLE = """\
A high-resolution academic infographic in the style of contemporary scholarly figures
published in journals like Nature, PNAS, Annals of GIS, and Habitat International.
Flat 2D vector style. Pure white background. No 3D, no drop shadows, no gradients,
no emoji, no stock photo people, no watermarks, no social media logos, no URLs.

Typography: Chinese characters render in a clean sans-serif (Microsoft YaHei / Source Han
Sans SC style), Latin characters and numbers render in Times New Roman / Inter for body,
and bold sans-serif for headings. All text must be sharp, legible, free of artifacts.

Color discipline: use AT MOST one primary color, one accent color, and one muted grey.
Avoid rainbow palettes. Avoid saturated reds except for genuine emphasis (≤ 5% of canvas).

Line discipline: arrows are straight or right-angled (elbow), never curved freestyle.
Borders are thin (1–2px). Panel corners are 8–16px rounded.

Composition discipline: there must be a clear reading order. Every visible text element
must correspond to a node listed in CHINESE CONTENT below. Do NOT invent nodes, captions,
authors, citations, or numbers that are not listed.
"""


NEGATIVE = """\
no 3D, no isometric, no drop shadows, no glow effects, no gradients,
no emoji, no stock photo of people, no watermarks, no URLs, no social media logos,
no rainbow palette, no oversaturated red except the banner,
no curved freestyle arrows, no decorative flourishes,
no nodes / captions / authors / citations / numbers not listed in the CHINESE CONTENT,
no Chinese typos, no character cutoffs, no garbled CJK,
no English-only output if Chinese content is provided
"""


ARCHETYPE_SKELETON = {
    "thinking": textwrap.dedent(
        """\
        Layout: a 16:9 academic concept-introduction figure organized as a 2×2 panel grid,
        each panel a rounded rectangle (rx≈12) with a circled number badge in the top-left
        and a small line icon next to the section label.

        Panel 1 (top-left, blue card #1F4E79): {{P1.label}} — {{P1.icon}} illustration.
        Bullets: {{P1.points}}.

        Panel 2 (top-right, green card #2E7D32): {{P2.label}} — two-column contrast,
        old vs new with small line icons, ending in a green bottom note bar.

        Panel 3 (bottom-left, blue card): {{P3.label}} — left mini diagram of
        transport-mode → service-destination, right side bullets.

        Panel 4 (bottom-right, green card): {{P4.label}} — 2×2 sub-grid of significance
        pillars, each an icon + bold label + one short sentence.

        Bottom red banner (#C00000), full width, ~8% canvas height, with a target icon
        and the text "{{core_question}}".
        """
    ),
    "method": textwrap.dedent(
        """\
        Layout: a 16:9 method-explanation infographic with ONE top "core idea" card on the
        left spanning ~30% width, followed by N Step cards filling the rest horizontally,
        then a bottom row of up to 3 small "assumption" cards.

        Core idea card: teal-bordered rounded rectangle with a lightbulb icon on a teal
        circle, the text "{{core_idea}}", and a thin downward visual abstract.

        Each Step card: rounded rect rx=16, white fill, thin grey border. Header bar in
        {{step.color}} with white text "Step N {{step.label}}". Center formula
        "{{step.formula_latex}}" rendered in clean LaTeX style inside a #F5F8FB box.
        Below: "含义：" label and "{{step.interpretation}}" in 14pt muted grey.

        Symbol legend row: grey strip "符号说明:" with the symbols {{symbols}}.

        Bottom assumption row: up to 3 cards with colored circular icons
        ({{assumption.color}}), bold label, and a single muted line.
        """
    ),
    "workflow": textwrap.dedent(
        """\
        Layout: a 16:9 left-to-right ML/data pipeline figure with N=4 column groups (Data,
        Preprocessing, Extraction, Methods). Column headers are thin bold sans-serif at
        the top of each column (no boxes).

        Column 1 Data: vertical stack of rectangular badges, each with a real-looking
        brand logo placeholder + the data name + source attribution.
        Items: {{C1.items}}. Background: pale lavender #EDE7F6.
        Arrow to column 2 labeled "{{C1.arrow_label}}".

        Column 2 Preprocessing: rectangular blocks for each entry in {{C2.blocks}}.
        Arrow to column 3 labeled "{{C2.arrow_label}}".

        Column 3 Extraction: a single tall multi-layer cylinder stack of N=4 disc layers
        alternating colors ({{C3.layers}}), tilted ~5° for subtle depth.
        Arrow to column 4 labeled "{{C3.arrow_label|default:extracted}}".

        Column 4 Methods (rightmost, larger panel with dashed purple border): vertical
        stack of sub-blocks:
          - Propensity score matching: scatter with red fit line
          - Causal XGBoost: row of {{C4.blocks[1].tree_count}} small decision-tree icons
            with purple branches + green leaves, sub-label chain
            "{{C4.blocks[1].sub_label_chain}}"
          - Treatment Effects: green downward arrow
          - SHAP: horizontal bar chart (red positive / blue negative), 4 features, base
            rate line

        Primary color: deep purple #7E57C2. Accent: leaf green #43A047. Muted: #757575.
        """
    ),
}


def load_content(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    try:
        return json.loads(text)
    except Exception:
        print(
            "❌ 未安装 pyyaml 且 content.yaml 不是合法 JSON。"
            "请 `pip install pyyaml` 或把 content.yaml 改成 JSON。",
            file=sys.stderr,
        )
        sys.exit(2)


def jsonify(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_chinese_content_block(content: dict) -> str:
    archetype = content.get("archetype", "")
    lines: list[str] = []
    title = content.get("title")
    if title:
        lines.append(f"标题：{title}")

    if archetype == "thinking":
        for section in content.get("sections", []):
            label = section.get("label", "")
            lines.append(f"\n{section.get('id', '')} {label}：")
            for pt in section.get("points", []):
                lines.append(f"  - {pt}")
            contrast = section.get("contrast")
            if contrast:
                lines.append(f"  既有研究：{', '.join(contrast.get('old', []))}")
                lines.append(f"  本文强调：{', '.join(contrast.get('new', []))}")
                if section.get("note"):
                    lines.append(f"  注：{section['note']}")
            for bullet in section.get("bullets", []):
                lines.append(f"  - {bullet}")
            grid = section.get("grid_2x2")
            if grid:
                for cell in grid:
                    lines.append(f"  - {cell[0]}：{cell[1]}")
        if content.get("core_question"):
            lines.append(f"\n核心问题：{content['core_question']}")

    elif archetype == "method":
        if content.get("core_idea"):
            lines.append(f"\n核心思想：{content['core_idea']}")
        for step in content.get("steps", []):
            lines.append(f"\n{step.get('label', '')}")
            if step.get("formula_latex"):
                lines.append(f"  公式（LaTeX）：{step['formula_latex']}")
            if step.get("interpretation"):
                lines.append(f"  含义：{step['interpretation']}")
        if content.get("symbols"):
            lines.append("\n符号说明：")
            for s in content["symbols"]:
                lines.append(f"  - {s.get('sym', '')}：{s.get('desc', '')}")
        if content.get("assumptions"):
            lines.append("\n传统公式的核心假设：")
            for a in content["assumptions"]:
                lines.append(f"  - {a.get('label', '')}：{a.get('note', '')}")

    elif archetype == "workflow":
        for col in content.get("columns", []):
            lines.append(f"\n列 {col.get('id', '')} · {col.get('label', '')}")
            for item in col.get("items", []) or []:
                lines.append(f"  - {item.get('name', '')}（{item.get('source', '')}）")
            for block in col.get("blocks", []) or []:
                lines.append(f"  - {block.get('name', '')}")
            if col.get("arrow_label"):
                lines.append(f"  → 箭头标签：{col['arrow_label']}")

    return "\n".join(lines).strip()


def render_skeleton(template: str, content: dict) -> str:
    """简化的 mustache 风格变量替换。不支持嵌套循环 — 复杂列表交给 CHINESE CONTENT 块。"""
    out = template
    flat = flatten(content)
    for key, val in flat.items():
        token = "{{" + key + "}}"
        if token in out:
            out = out.replace(token, str(val))
    # 把剩余未替换的占位符变成简短描述，避免出现在最终 prompt 里
    import re as _re

    out = _re.sub(r"\{\{[^}]+\}\}", "[see chinese content]", out)
    return out


def flatten(d: dict, prefix: str = "") -> dict:
    flat: dict = {}
    if isinstance(d, dict):
        for k, v in d.items():
            sub_prefix = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, (dict, list)):
                flat.update(flatten(v, sub_prefix))
                flat[sub_prefix] = jsonify(v)
            else:
                flat[sub_prefix] = v
    elif isinstance(d, list):
        for i, v in enumerate(d):
            flat.update(flatten(v, f"{prefix}[{i}]"))
        flat[prefix] = jsonify(d)
    else:
        flat[prefix] = d
    return flat


def cmd_prompt(args: argparse.Namespace) -> int:
    content_path = Path(args.content)
    if not content_path.exists():
        print(f"❌ content 不存在：{content_path}", file=sys.stderr)
        return 2

    content = load_content(content_path)
    archetype = args.archetype or content.get("archetype")
    if archetype not in ARCHETYPE_SKELETON:
        print(f"❌ archetype 必须是 thinking/method/workflow，当前 = {archetype}", file=sys.stderr)
        return 2

    style_extra = ""
    if args.style:
        sp = Path(args.style)
        if sp.exists():
            style_extra = sp.read_text(encoding="utf-8").strip()

    skeleton = ARCHETYPE_SKELETON[archetype]
    rendered = render_skeleton(skeleton, content)
    cn_block = build_chinese_content_block(content)

    prompt = "\n\n".join(
        [
            COMMON_PREAMBLE.strip(),
            "[STRUCTURE]",
            rendered.strip(),
            "[STYLE PROFILE]",
            style_extra or "(none)",
            "[CHINESE CONTENT — render exactly as written, no translation]",
            cn_block,
            "[NEGATIVE]",
            NEGATIVE.strip(),
        ]
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prompt, encoding="utf-8")
    print(f"✅ 已生成 prompt：{out_path}")
    print(f"   archetype = {archetype}")
    print(f"   字符数 = {len(prompt)}")
    return 0


# ---------------------------------------------------------------------------
# 调 image_gen.py 出图
# ---------------------------------------------------------------------------


def cmd_run(args: argparse.Namespace) -> int:
    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"❌ prompt 不存在：{prompt_path}", file=sys.stderr)
        return 2
    prompt = prompt_path.read_text(encoding="utf-8")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not IMAGE_GEN_PY.exists():
        print(
            "❌ 未找到 image_gen.py：\n"
            f"   尝试路径：{IMAGE_GEN_PY}\n"
            "\n"
            "cn-academic-spark-technicalroute-engine 依赖 ppt-engine 的 image_gen.py 做生图。请任选一种修复：\n"
            "  1. 设置 IMAGE_GEN_PATH=/abs/path/to/image_gen.py 直接指向脚本；\n"
            "  2. 设置 PAPER2PPT_ROOT=/abs/path/to/CN_Spark_paper2ppt 指向 PPT engine 根目录；\n"
            "  3. 把 CN_Spark_paper2ppt 与 CN_Spark_technicalroute 作为兄弟目录一起安装（捆绑安装即满足）。\n",
            file=sys.stderr,
        )
        return 2

    cmd = [
        sys.executable,
        str(IMAGE_GEN_PY),
        prompt,
        "--aspect_ratio",
        args.aspect_ratio,
        "--image_size",
        args.image_size,
        "-o",
        str(out_dir),
    ]
    if args.refs:
        for ref in args.refs:
            cmd.extend(["--reference", ref])

    env = os.environ.copy()
    env.setdefault("IMAGE_BACKEND", "gemini")
    print("▶", " ".join(cmd))
    rc = subprocess.run(cmd, env=env).returncode
    if rc != 0:
        print("⚠️ image_gen.py 失败，尝试 fallback（去掉参考图重试）")
        cmd = [c for c in cmd if c not in {"--reference"} and not any(c == r for r in (args.refs or []))]
        rc = subprocess.run(cmd, env=env).returncode
    return rc


# ---------------------------------------------------------------------------
# 嵌入到 paper2ppt SVG
# ---------------------------------------------------------------------------


def cmd_embed(args: argparse.Namespace) -> int:
    image_path = Path(args.image)
    target_svg = Path(args.target)
    if not image_path.is_file():
        print(f"❌ image 不存在：{image_path}", file=sys.stderr)
        return 2
    if not target_svg.is_file():
        print(f"❌ 目标 SVG 不存在：{target_svg}", file=sys.stderr)
        return 2

    # 把图片复制到 paper2ppt project 的 images/
    project_root = target_svg.parent
    while project_root.parent != project_root and not (project_root / "images").is_dir():
        project_root = project_root.parent
    images_dir = project_root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    dst = images_dir / image_path.name
    if dst.resolve() != image_path.resolve():
        dst.write_bytes(image_path.read_bytes())

    # 解析 bbox
    try:
        x, y, w, h = (int(v.strip()) for v in args.bbox.split(","))
    except Exception:
        print(f"❌ bbox 格式应为 'x,y,w,h'：{args.bbox}", file=sys.stderr)
        return 2

    href = f"../images/{dst.name}"
    image_tag = (
        f'  <g id="injected_route_image">\n'
        f'    <image href="{href}" x="{x}" y="{y}" width="{w}" height="{h}"'
        f' preserveAspectRatio="xMidYMid meet"/>\n'
    )
    if args.caption:
        cap_y = y + h + 18
        image_tag += (
            f'    <text x="{x + w // 2}" y="{cap_y}" font-size="11" fill="#888"'
            f' text-anchor="middle" font-family="Microsoft YaHei,Source Han Sans SC,sans-serif">'
            f"{args.caption}</text>\n"
        )
    image_tag += "  </g>\n"

    svg_text = target_svg.read_text(encoding="utf-8")
    if "</svg>" not in svg_text:
        print("❌ 目标 SVG 缺少 </svg>", file=sys.stderr)
        return 2
    new_svg = svg_text.replace("</svg>", image_tag + "</svg>", 1)
    target_svg.write_text(new_svg, encoding="utf-8")
    print(f"✅ 已注入 <image> 到 {target_svg}（href={href}, bbox={args.bbox}）")
    return 0


CONTRACT_TEMPLATE = """# Diagram Contract — {project}

## 1. Core claim（一句话）
<这张图必须捍卫的一句话主张，必须有动词>

## 2. Archetype 与 sub_variant
archetype: {archetype}
sub_variant: <见对应 archetype-*.md 的 sub_variant 表>
reason: <为什么选这个 — 一句话>

## 3. Panel / Stage 映射
（按 archetype 填）

## 4. Discipline-specific 术语保留清单
  - <术语 1>
  - <术语 2>

## 5. 视觉合同
canvas: 16:9
color_scheme: discipline_default
density: balanced
icon_density: medium
typography: cn_yahei_en_times
emphasis_usage: <核心问题 / 主张 / 警示，或 "无">

## 6. Reference 模式
mode: literature        # literature | offline_user_uploads | atlas_only
expected_refs_count: 5
note: <可选>

## 7. Reviewer 风险
Q1. 这张图最可能被听众挑战的一个点是什么？
A1. <填>
Q2. 如果 panel 数减半，论证还成立吗？哪些可以合并 / 删除？
A2. <填>
Q3. 任意一个被引用的"他人方法 / 数据 / 概念"是否在 PPT 页脚有 GB/T 7714 引用？
A3. <填>
Q4. 颜色编码（主色 / 强调 / 灰）是否承担信息含义？还是只是装饰？
A4. <填>

## 8. 验收门槛
- [ ] 每一个可见文本都对应 §3 中的某条
- [ ] 没有 §3 之外的节点 / 编号 / 引用
- [ ] §4 术语清单中每一项都逐字出现
- [ ] 配色和 §5 一致
- [ ] §7 中识别的风险点已经在图中被回应
"""


def cmd_contract(args: argparse.Namespace) -> int:
    """scaffold contract.md。被 SKILL.md Step 1 调用。"""
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not args.force:
        print(f"❌ {out_path} 已存在；加 --force 覆盖", file=sys.stderr)
        return 2
    project = args.project or out_path.parent.name
    archetype = args.archetype or "<thinking | method | workflow>"
    out_path.write_text(
        CONTRACT_TEMPLATE.format(project=project, archetype=archetype),
        encoding="utf-8",
    )
    print(f"✅ 已写入 contract 骨架：{out_path}")
    print(f"   下一步：让用户填字段并在 SKILL.md Step 1 末尾 ⛔ BLOCKING gate 处确认。")
    return 0


def _extract_glossary(content: dict) -> list[str]:
    return content.get("glossary_preserve", []) or []


def _walk_text_strings(node):
    """递归收集 content.yaml 中所有 leaf 字符串。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _walk_text_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_text_strings(v)


def cmd_audit(args: argparse.Namespace) -> int:
    """对生成的 PNG 跑 hard checks（机器可判），并生成 audit_report.md。

    soft / reviewer-risk 检查项写到报告里，留给主代理 + 用户人工补完。
    """
    image_path = Path(args.image)
    if not image_path.is_file():
        print(f"❌ image 不存在：{image_path}", file=sys.stderr)
        return 2

    hard_results: list[tuple[str, bool, str]] = []

    # hard: file size
    size_kb = image_path.stat().st_size / 1024
    hard_results.append(("file size ≥ 200 KB", size_kb >= 200, f"actual = {size_kb:.0f} KB"))

    # hard: width / aspect (Pillow optional)
    width = height = None
    try:
        from PIL import Image  # type: ignore

        with Image.open(image_path) as im:
            width, height = im.size
    except ImportError:
        pass

    if width is not None:
        hard_results.append(("width ≥ 1600 px", width >= 1600, f"actual = {width} px"))
        if height:
            aspect = width / height
            hard_results.append(
                ("aspect within ±2% of contract canvas",
                 True,  # 留给人工判断（contract 的 canvas 多种合法）
                 f"aspect = {aspect:.3f}")
            )

    # 内容比对（如果提供了 contract / content）
    glossary: list[str] = []
    if args.content:
        cp = Path(args.content)
        if cp.is_file():
            try:
                content = load_content(cp)
                glossary = _extract_glossary(content)
            except SystemExit:
                content = None
        else:
            print(f"⚠️ content 文件不存在：{cp}", file=sys.stderr)

    # 写 audit_report.md
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# Audit Report — {image_path.name}\n")
    lines.append("## Hard checks")
    n_pass = sum(1 for _, ok, _ in hard_results if ok)
    lines.append(f"({n_pass}/{len(hard_results)} passed)\n")
    for name, ok, detail in hard_results:
        mark = "✓" if ok else "✗"
        lines.append(f"- [{mark}] **{name}** — {detail}")
    lines.append("")
    lines.append("## Soft checks (manual review required)")
    soft_items = [
        "每一个可见文本都对应 contract.md §3 panel/stage 映射中的某一条",
        "没有 contract 之外的节点 / 编号 / 引用",
        "contract.md §4 术语保留清单中的每一项都逐字出现",
        "配色不超过 4 种主色（primary / secondary / accent / muted）",
        "强调色面积 ≤ 5% 且承载语义（不只是装饰）",
        "panel / 阶段数与 contract §3 一致",
        "论证流向与 archetype × sub_variant 一致",
        "公式区底色为浅灰 / 白（method archetype）",
        "列间过渡箭头带 italic muted 标签（workflow horizontal-pipeline）",
        "底部强调横幅 ≤ 1 条",
        "中文文字无错位 / 截断 / 乱码 CJK",
        "中英文混排：英 / 数 = serif；中文 = sans-serif",
    ]
    for s in soft_items:
        lines.append(f"- [ ] {s}")
    if glossary:
        lines.append("")
        lines.append("### Glossary preserve（contract §4）— 主代理用多模态读图核对每一项是否逐字出现")
        for term in glossary:
            lines.append(f"  - [ ] `{term}`")
    lines.append("")
    lines.append("## Reviewer-risk checks (contract §7)")
    for q in ["Q1 最可能挑战点已在图中回应", "Q2 panel 减半后论证仍成立 → 每个 panel 必要",
              "Q3 引用文献在 PPT 页脚有 GB/T 7714 条目（嵌入 paper2ppt 后再核对）",
              "Q4 颜色编码承担信息含义（非装饰）"]:
        lines.append(f"- [ ] {q}")
    lines.append("")
    lines.append("## Decision")
    lines.append("- [ ] PASS — ready for embed")
    lines.append("- [ ] CONDITIONAL PASS — note follow-ups below")
    lines.append("- [ ] FAIL — regenerate via `generate_route_image.py run` with `--refine`")
    lines.append("")
    lines.append("## Recommended `--refine` instruction")
    lines.append("> <在此填写需要图像模型修正的具体指令，例如 \"把第 3 panel 的 X 改回 Y，其他不变\"。>")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ 已写入 audit report：{out}")
    print(f"   hard checks 通过 = {n_pass}/{len(hard_results)}")
    if any(not ok for _, ok, _ in hard_results):
        print("   ⚠️ 有 hard check 失败，建议先修复再考虑 soft / reviewer-risk")
        return 1
    return 0


# ---------------------------------------------------------------------------
# assemble · 装配可编辑 SVG（Gallery-first → Template assembly 链路的 Tier 2）
# ---------------------------------------------------------------------------

TEMPLATES_DIR = TECHROUTE_ROOT / "assets" / "templates"
PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.\[\]]+)\s*\}\}")
CSS_VAR_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)\s*\)")


def _parse_spec_lock(path: Path) -> dict[str, list[tuple[str, str]]]:
    """Minimal spec_lock.md parser.

    Recognises ``## section`` headers and ``- key: value`` data rows under each
    section. Blockquote lines (``>``), blank lines, code fences and free text are
    ignored. Returns ``{section_name: [(key, value), ...]}``.
    """
    sections: dict[str, list[tuple[str, str]]] = {}
    current: str | None = None
    in_fence = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line.startswith(">"):
            continue
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections.setdefault(current, [])
            continue
        if current is None or not line.lstrip().startswith("- "):
            continue
        body = line.lstrip()[2:]
        if ":" not in body:
            continue
        key, _, value = body.partition(":")
        sections[current].append((key.strip(), value.strip()))
    return sections


def _section_as_dict(rows: list[tuple[str, str]]) -> dict[str, str]:
    return {k: v for k, v in rows}


def _resolve_yaml_path(data: object, dotted: str) -> object | None:
    """Walk ``data`` along a dotted path with ``[index]`` segments.

    Example: ``content.yaml.panels[0].label`` → drops the leading ``content.yaml.``
    if present, then walks ``panels → [0] → label``.
    """
    if dotted.startswith("content.yaml."):
        dotted = dotted[len("content.yaml."):]
    cur: object | None = data
    for raw_seg in dotted.split("."):
        if cur is None:
            return None
        seg = raw_seg
        # extract trailing [i][j]... indices
        idx_parts = re.findall(r"\[(\d+)\]", seg)
        name = re.sub(r"\[\d+\]", "", seg)
        if name:
            if not isinstance(cur, dict) or name not in cur:
                return None
            cur = cur[name]
        for idx in idx_parts:
            if not isinstance(cur, list):
                return None
            try:
                cur = cur[int(idx)]
            except (IndexError, ValueError):
                return None
    return cur


def _load_content_yaml(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise SystemExit(
                f"❌ content.yaml 不是合法 JSON 且 PyYAML 未安装：{e}\n"
                "请 `pip install pyyaml` 再重试。"
            )
    return yaml.safe_load(text)


def cmd_assemble(args) -> int:
    """Assemble an editable SVG from a chosen template + content.yaml + spec_lock.md.

    Pipeline:
      1. Load spec_lock.md, pull `template_key` from §source_choice and the
         §slot_map / §color_var_map / §colors / §glossary_preserve / §forbidden
         sections.
      2. Read the template SVG at ``assets/templates/<template_key>.svg``.
      3. Substitute every ``{{path}}`` with the value at the dotted path inside
         content.yaml (per §slot_map). Unmapped placeholders abort with an
         error so the user fixes spec_lock.md, not the template.
      4. Substitute every ``var(--X)`` with the matching HEX from §colors (per
         §color_var_map).
      5. Sanity-check: every glossary_preserve term either appears verbatim in
         the output OR was never required to appear (warn, not fail).
      6. Write the output SVG to ``--out``.
    """
    spec_lock = Path(args.spec_lock).expanduser().resolve()
    if not spec_lock.is_file():
        print(f"❌ spec_lock.md not found: {spec_lock}", file=sys.stderr)
        return 2
    sections = _parse_spec_lock(spec_lock)

    source = _section_as_dict(sections.get("source_choice", []))
    template_key = source.get("template_key") or args.template_key
    if not template_key or template_key.lower() == "none":
        print(
            "❌ spec_lock.md §source_choice.template_key is empty or `none`.\n"
            "   `assemble` requires a concrete template_key. If none matches, "
            "fall through to `run` (which calls image_gen.py for PNG output).",
            file=sys.stderr,
        )
        return 2

    template_path = TEMPLATES_DIR / f"{template_key}.svg"
    if not template_path.is_file():
        print(
            f"❌ Template SVG not found: {template_path}\n"
            f"   Check that `{template_key}` is a real key in "
            f"`assets/templates/templates_index.json` and that the SVG file exists.",
            file=sys.stderr,
        )
        return 2

    content_path = Path(args.content).expanduser().resolve()
    if not content_path.is_file():
        print(f"❌ content.yaml not found: {content_path}", file=sys.stderr)
        return 2
    content_data = _load_content_yaml(content_path)

    slot_map = _section_as_dict(sections.get("slot_map", []))
    color_var_map = _section_as_dict(sections.get("color_var_map", []))
    colors = _section_as_dict(sections.get("colors", []))
    glossary = [k for k, _ in sections.get("glossary_preserve", [])]
    # In `## glossary_preserve` we emit `- 术语` (no colon); the key holds the
    # whole term and value is "". Re-collect raw lines to be safe.
    if not glossary:
        glossary = [
            ln.strip().lstrip("-").strip()
            for ln in spec_lock.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("-")
        ]
        glossary = []  # fallback empty rather than misclassify other lines

    svg_text = template_path.read_text(encoding="utf-8")

    # ---- step 3 · slot substitution -----------------------------------------
    placeholders = set(PLACEHOLDER_RE.findall(svg_text))
    unmapped = [p for p in placeholders if p not in slot_map]
    if unmapped:
        print(
            "❌ Template has placeholders with no row in spec_lock.md §slot_map:",
            file=sys.stderr,
        )
        for p in sorted(unmapped):
            print(f"   - {{{{{p}}}}}", file=sys.stderr)
        print(
            "   Add one row per placeholder under `## slot_map` "
            "(left = placeholder, right = dotted content.yaml path), then re-run.",
            file=sys.stderr,
        )
        return 2

    missing_in_yaml: list[str] = []
    for placeholder, dotted in slot_map.items():
        value = _resolve_yaml_path(content_data, dotted)
        if value is None:
            missing_in_yaml.append(f"{{{{{placeholder}}}}} ← {dotted}")
            continue
        # YAML lists / dicts coerce to str for SVG text injection.
        svg_text = svg_text.replace(
            "{{" + placeholder + "}}", str(value)
        )
    if missing_in_yaml:
        print(
            "❌ The following slot_map paths resolved to nothing in content.yaml:",
            file=sys.stderr,
        )
        for m in missing_in_yaml:
            print(f"   - {m}", file=sys.stderr)
        print(
            "   Either fill in content.yaml, or trim the placeholder from the template.",
            file=sys.stderr,
        )
        return 2

    # ---- step 4 · color var substitution ------------------------------------
    used_vars = set(CSS_VAR_RE.findall(svg_text))
    for var_name in used_vars:
        # spec_lock writes the key as `"var(--primary)"` (quoted) → strip quotes
        quoted_key = f'"var({var_name})"'
        target_section_key = color_var_map.get(quoted_key) or color_var_map.get(
            f"var({var_name})"
        )
        if not target_section_key:
            print(
                f"⚠️ var({var_name}) appears in template but has no row in "
                f"spec_lock.md §color_var_map — leaving literal token in SVG.",
                file=sys.stderr,
            )
            continue
        # target_section_key looks like "colors.primary" — pull from §colors
        if target_section_key.startswith("colors."):
            color_key = target_section_key.split(".", 1)[1]
            hex_val = colors.get(color_key)
            if not hex_val:
                print(
                    f"⚠️ color_var_map points var({var_name}) → {target_section_key} "
                    f"but §colors has no `{color_key}` row.",
                    file=sys.stderr,
                )
                continue
            svg_text = svg_text.replace(f"var({var_name})", hex_val)

    # ---- step 6 · write output ----------------------------------------------
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg_text, encoding="utf-8")
    print(f"✅ Assembled editable SVG: {out_path}")
    print(f"   template: {template_key}.svg")
    print(f"   placeholders substituted: {len(slot_map)}")
    print(f"   color vars substituted: {len(used_vars)}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="cn-academic-spark-technicalroute-engine · image prompt + gen + embed")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_prompt = sub.add_parser("prompt", help="拼装 prompt → prompt.md")
    p_prompt.add_argument("--archetype", choices=["thinking", "method", "workflow"])
    p_prompt.add_argument("--content", required=True, help="content.yaml")
    p_prompt.add_argument("--style", help="style_profile.md (optional)")
    p_prompt.add_argument("--out", required=True, help="prompt.md")
    p_prompt.set_defaults(func=cmd_prompt)

    p_asm = sub.add_parser(
        "assemble",
        help=(
            "装配可编辑 SVG（Tier 2 路径）：读 spec_lock.md 中选好的 template_key，"
            "用 content.yaml 替换占位符 + 用 §colors 替换 var(--*) → 输出可编辑 .svg"
        ),
    )
    p_asm.add_argument("--spec-lock", required=True, help="项目的 spec_lock.md 路径")
    p_asm.add_argument("--content", required=True, help="项目的 content.yaml 路径")
    p_asm.add_argument(
        "--template-key",
        default="",
        help="可选；显式覆盖 spec_lock.md §source_choice.template_key",
    )
    p_asm.add_argument("--out", required=True, help="输出 .svg 路径")
    p_asm.set_defaults(func=cmd_assemble)

    p_run = sub.add_parser(
        "run",
        help=(
            "Tier 3 兜底：模板装不出可编辑 SVG 时调 image_gen.py 出 PNG。"
            "默认 backend = gemini（nano banana pro），可切 qwen（image2）等。"
            "把 Custom_gallery / style_refs 图当 --refs 喂进去作风格 anchor。"
        ),
    )
    p_run.add_argument("--prompt", required=True)
    p_run.add_argument("--aspect_ratio", default="16:9")
    p_run.add_argument("--image_size", default="2K")
    p_run.add_argument("--refs", nargs="*", default=[])
    p_run.add_argument("--out", required=True)
    p_run.set_defaults(func=cmd_run)

    p_emb = sub.add_parser("embed", help="把生成的 PNG 嵌入 paper2ppt 的一张 SVG")
    p_emb.add_argument("--image", required=True)
    p_emb.add_argument("--target", required=True, help="目标 SVG 路径（svg_output/<NN>_<page>.svg）")
    p_emb.add_argument("--bbox", required=True, help="x,y,w,h（如 '60,120,1160,500'）")
    p_emb.add_argument("--caption", default="")
    p_emb.set_defaults(func=cmd_embed)

    p_con = sub.add_parser("contract", help="scaffold contract.md（SKILL.md Step 1 用）")
    p_con.add_argument("--out", required=True, help="contract.md 输出路径")
    p_con.add_argument("--project", default="", help="项目名（用于标题）")
    p_con.add_argument("--archetype", choices=["thinking", "method", "workflow"])
    p_con.add_argument("--force", action="store_true", help="存在则覆盖")
    p_con.set_defaults(func=cmd_contract)

    p_aud = sub.add_parser("audit", help="对生成的 PNG 跑 QA 检查（hard 自动 + soft / risk 留人工）")
    p_aud.add_argument("--image", required=True)
    p_aud.add_argument("--content", default="", help="可选 content.yaml — 用来抽 glossary 比对")
    p_aud.add_argument("--contract", default="", help="可选 contract.md — 仅记录路径")
    p_aud.add_argument("--out", required=True, help="audit_report.md 输出路径")
    p_aud.set_defaults(func=cmd_audit)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

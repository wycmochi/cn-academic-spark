#!/usr/bin/env python3
"""
generate_route_image.py · 把 content.yaml + style_profile.md 拼成 prompt，再调用
PPT engine 的 ``scripts/image_gen.py`` 做多后端生图。

子命令：
  contract       写 Diagram Contract 骨架
  prompt         读 content.yaml + style_profile.md + archetype skeleton → 生成 prompt_ai.md
  assemble       依据 technicalroute templates 装配 A 版可编辑 SVG
  run-ai-variant 读 prompt_ai.md + 参考图 → 调 image_gen.py 生成 B 版 AI PNG
  run            run-ai-variant 的兼容别名
  embed          把生成的 PNG 嵌入 PPT engine 项目的某张 SVG 页面

默认 backend = gemini（gemini-3-pro-image-preview，即 nano banana pro），
环境变量 ``IMAGE_BACKEND`` / ``GEMINI_API_KEY`` 由用户在 PPT engine 的 ``.env`` 中配置。

生图脚本路径查找顺序（最高优先级在前）：

1. ``IMAGE_GEN_PATH``  — 直接指向某个 image_gen.py（独立安装时最常用）；
2. ``PAPER2PPT_ROOT``  — 指向已部署的 PPT engine 根目录，自动拼出
   ``$PAPER2PPT_ROOT/scripts/image_gen.py``；
3. 默认值              — 当前 paper2ppt skill 内置的 ``scripts/image_gen.py``。

三条都失败时 ``run`` 子命令会报错并把上述变量名一并打印出来，提示用户单独安装时
如何接生图后端。
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import textwrap
from html import escape as xml_escape
from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore
except ImportError:  # 退化：手写极简 yaml loader 暂用 json
    yaml = None

HERE = Path(__file__).resolve().parent
PAPER2PPT_ROOT = HERE.parent.parent
TECHROUTE_ROOT = PAPER2PPT_ROOT
REFS_DIR = PAPER2PPT_ROOT / "references" / "technicalroute"


def _resolve_image_gen() -> Path:
    """Locate the PPT engine's image_gen.py via env-var overrides, then sibling default.

    Returns the resolved Path (may not exist; caller checks ``.exists()``).
    """
    override = os.environ.get("IMAGE_GEN_PATH")
    if override:
        return Path(override).expanduser().resolve()
    paper2ppt_env = os.environ.get("PAPER2PPT_ROOT")
    if paper2ppt_env:
        return (Path(paper2ppt_env).expanduser().resolve() / "scripts" / "image_gen.py")
    return (PAPER2PPT_ROOT / "scripts" / "image_gen.py").resolve()


IMAGE_GEN_PY = _resolve_image_gen()


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
Borders are thin (1–2px). Panel corners are 6–8px rounded by default.

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
        each panel a rounded rectangle (rx≈8) with a circled number badge in the top-left
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

        Each Step card: rounded rect rx=8, white fill, thin grey border. Header bar in
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

    reference_mode = getattr(args, "reference_mode", "literature")
    ref_clause = ""
    if reference_mode == "atlas_only":
        ref_clause = "\n\n".join([
            "[ATLAS-ONLY MODE]",
            "No literature or Custom_gallery reference images are available. Render using ONLY",
            "[STRUCTURE], [SHAPE RECIPES], [COLOR DISCIPLINE], and the article-derived",
            "[CHINESE CONTENT] as layout truth. Default to a clean, restrained, academic-poster",
            "look with generous white space, thin strokes, flat fills, and no decorative flourishes.",
        ])

    prompt_parts = [
        COMMON_PREAMBLE.strip(),
        "[STRUCTURE]",
        rendered.strip(),
        "[STYLE PROFILE]",
        style_extra or "(none)",
        "[CHINESE CONTENT — render exactly as written, no translation]",
        cn_block,
    ]
    if ref_clause:
        prompt_parts.append(ref_clause)
    prompt_parts.extend([
        "[NEGATIVE]",
        NEGATIVE.strip(),
    ])
    prompt = "\n\n".join(prompt_parts)

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


def _find_generated_image(out_dir: Path, filename: str, before: set[Path] | None = None) -> Path | None:
    """Find the image created by image_gen.py for a stable route filename."""
    image_exts = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]
    if filename:
        stem = Path(filename).stem
        candidates: list[Path] = []
        candidates.extend(out_dir / f"{stem}{ext}" for ext in image_exts)
        candidates.extend(sorted(out_dir.glob(f"{stem}.*")))
        for candidate in candidates:
            if candidate.is_file() and candidate.suffix.lower() in image_exts:
                return candidate.resolve()
        return None

    before = before or set()
    candidates = [
        candidate for candidate in out_dir.iterdir()
        if candidate.is_file()
        and candidate.suffix.lower() in image_exts
        and candidate.resolve() not in before
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates[0].resolve()


def _fallback_output_path(out_dir: Path, filename: str) -> Path:
    stem = Path(filename).stem if filename else "route_ai_local_fallback"
    if not stem:
        stem = "route_ai_local_fallback"
    return (out_dir / f"{stem}.png").resolve()


def _load_route_font(size: int, *, bold: bool = False):
    from PIL import ImageFont

    candidates = []
    if bold:
        candidates.extend([r"C:/Windows/Fonts/msyhbd.ttc", r"C:/Windows/Fonts/simhei.ttf"])
    candidates.extend([
        r"C:/Windows/Fonts/msyh.ttc",
        r"C:/Windows/Fonts/simhei.ttf",
        r"C:/Windows/Fonts/simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ])
    for candidate in candidates:
        try:
            path = Path(candidate)
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _pil_text_width(draw, text: str, font) -> int:
    if not text:
        return 0
    bbox = draw.textbbox((0, 0), text, font=font)
    return int(bbox[2] - bbox[0])


def _pil_wrap(draw, text: str, font, max_width: int, *, max_lines: int = 3) -> list[str]:
    text = re.sub(r"\s+", " ", str(text or "").strip())
    if not text:
        return []
    tokens = list(text) if re.search(r"[\u4e00-\u9fff]", text) else text.split(" ")
    sep = "" if re.search(r"[\u4e00-\u9fff]", text) else " "
    lines: list[str] = []
    current = ""
    for token in tokens:
        candidate = token if not current else current + sep + token
        if _pil_text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = token
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if len(lines) == max_lines and _pil_text_width(draw, lines[-1], font) > max_width:
        while lines[-1] and _pil_text_width(draw, lines[-1] + "…", font) > max_width:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines


def _prompt_snippets(prompt: str, count: int = 5) -> list[str]:
    snippets: list[str] = []
    seen: set[str] = set()
    skip_prefixes = (
        "A high-resolution", "Flat 2D", "Typography:", "Canvas:", "No ",
        "[", "NEGATIVE", "Use ", "Do not", "Render ",
    )
    for raw in prompt.splitlines():
        line = raw.strip(" \t-•*#0123456789.、:：")
        if not line or len(line) < 6:
            continue
        if any(line.startswith(prefix) for prefix in skip_prefixes):
            continue
        if not re.search(r"[\u4e00-\u9fffA-Za-z]", line):
            continue
        line = re.sub(r"\s+", " ", line)
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        snippets.append(line[:90])
        if len(snippets) >= count:
            break
    defaults = [
        "问题提出与研究对象界定",
        "指标构建、数据整理与变量识别",
        "模型解释、机制检验与稳健性分析",
        "结果归纳、异质性比较与规划启示",
        "形成可汇报的全文技术路线图",
    ]
    while len(snippets) < count:
        snippets.append(defaults[len(snippets)])
    return snippets[:count]


def _render_local_route_fallback(prompt: str, out_dir: Path, filename: str, reason: str) -> Path:
    try:
        from PIL import Image, ImageDraw
    except Exception as exc:
        raise RuntimeError("Local route fallback requires Pillow when image generation backend is unavailable.") from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = _fallback_output_path(out_dir, filename)
    width, height = 1280, 720
    image = Image.new("RGBA", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    font_title = _load_route_font(34, bold=True)
    font_subtitle = _load_route_font(17)
    font_stage = _load_route_font(18, bold=True)
    font_body = _load_route_font(14)
    font_badge = _load_route_font(12)

    draw.rectangle((0, 0, width, 92), fill="#0B3A66")
    draw.rectangle((0, 0, 12, 92), fill="#D00000")
    draw.text((34, 28), "AI全文技术路线图", fill="#FFFFFF", font=font_title)
    subtitle = "本地兜底生成：根据 prompt_ai.md 摘取全文研究链路，确保 Version B 页面不断链"
    draw.text((34, 102), subtitle, fill="#334155", font=font_subtitle)
    draw.rounded_rectangle((965, 28, 1220, 62), radius=10, fill="#E8F1FA", outline="#B9D1EA", width=1)
    draw.text((982, 38), f"fallback: {reason[:25]}", fill="#24527A", font=font_badge)

    snippets = _prompt_snippets(prompt, 5)
    labels = ["问题提出", "指标与数据", "模型解释", "结果验证", "规划启示"]
    colors = ["#2563EB", "#0EA5E9", "#10B981", "#F59E0B", "#D00000"]
    card_w, card_h = 204, 310
    gap = 28
    start_x = 62
    y = 220
    for idx, (label, snippet, color) in enumerate(zip(labels, snippets, colors), start=1):
        x = start_x + (idx - 1) * (card_w + gap)
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=16, fill="#FFFFFF", outline="#CBD5E1", width=2)
        draw.rounded_rectangle((x, y, x + card_w, y + 58), radius=16, fill=color)
        draw.rectangle((x, y + 42, x + card_w, y + 58), fill=color)
        draw.ellipse((x + 16, y + 16, x + 46, y + 46), fill="#FFFFFF")
        draw.text((x + 24, y + 20), str(idx), fill=color, font=font_stage)
        draw.text((x + 58, y + 19), label, fill="#FFFFFF", font=font_stage)
        lines = _pil_wrap(draw, snippet, font_body, card_w - 32, max_lines=6)
        ty = y + 90
        for line in lines:
            draw.text((x + 16, ty), line, fill="#334155", font=font_body)
            ty += 24
        draw.rounded_rectangle((x + 18, y + card_h - 74, x + card_w - 18, y + card_h - 26), radius=10, fill="#F8FAFC", outline="#E2E8F0")
        draw.text((x + 32, y + card_h - 58), "论文内容驱动", fill=color, font=font_body)
        if idx < 5:
            ax1 = x + card_w + 6
            ay = y + card_h / 2
            ax2 = ax1 + gap - 12
            draw.line((ax1, ay, ax2, ay), fill="#94A3B8", width=3)
            draw.polygon([(ax2, ay), (ax2 - 10, ay - 7), (ax2 - 10, ay + 7)], fill="#94A3B8")

    draw.text((64, 666), "说明：图像后端或参考图链路不可用时生成此兜底 PNG；真实 AI 后端可用时会自动替换为模型生成图。", fill="#64748B", font=font_badge)
    image.save(out_path, format="PNG")
    return out_path


def _create_ai_slide_if_requested(args: argparse.Namespace, image_path: Path) -> int:
    out_svg = getattr(args, "out_svg", "") or ""
    if not out_svg:
        return 0
    ns = argparse.Namespace(
        image=str(image_path),
        out_svg=out_svg,
        title=getattr(args, "title", "") or "Research Route: AI Reference Version",
        subtitle=getattr(args, "subtitle", "") or "Generated from article content plus available route anchors",
        caption=getattr(args, "caption", "") or "AI reference route diagram; semantic content follows the source material",
        footer=getattr(args, "footer", "") or "",
        page_number=getattr(args, "page_number", "") or "",
        format=getattr(args, "format", "ppt169") or "ppt169",
        bbox=getattr(args, "bbox", "") or "",
    )
    return cmd_create_ai_slide(ns)


def _finish_local_route_fallback(args: argparse.Namespace, prompt: str, out_dir: Path, reason: str) -> int:
    if getattr(args, "no_local_fallback", False):
        print(f"Error: {reason}; local fallback is disabled by --no-local-fallback.", file=sys.stderr)
        return 2
    try:
        generated = _render_local_route_fallback(prompt, out_dir, getattr(args, "filename", ""), reason)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(f"Warning: {reason}. Created a deterministic local route PNG so Version B is not missing.", file=sys.stderr)
    print(f"OK: route_ai_image_path = {generated}")
    slide_rc = _create_ai_slide_if_requested(args, generated)
    return slide_rc


def _load_refs_plan(args: argparse.Namespace) -> None:
    plan_path_raw = getattr(args, "refs_plan", "") or ""
    if not plan_path_raw:
        return
    plan_path = Path(plan_path_raw).expanduser().resolve()
    if not plan_path.is_file():
        raise FileNotFoundError(f"refs plan not found: {plan_path}")
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    plan_refs = [str(Path(item).expanduser().resolve()) for item in data.get("refs") or []]
    forbidden = {".svg", ".pptx", ".ppt", ".odp", ".key"}
    bad = [ref for ref in plan_refs if Path(ref).suffix.lower() in forbidden]
    if bad:
        raise ValueError("refs plan contains forbidden AI reference file(s): " + ", ".join(bad))
    args.refs = list(dict.fromkeys((args.refs or []) + plan_refs))
    if not getattr(args, "refs_manifest", "") and data.get("refs_manifest"):
        args.refs_manifest = str(Path(data["refs_manifest"]).expanduser().resolve())
    if data.get("gallery_only"):
        args.gallery_only = True
    args._refs_plan_mode = data.get("mode", "")


def _manifest_reference_paths(manifest_path: Path) -> set[Path]:
    """Load allowed academic-search refs collected from the seed_sites.json workflow."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"style refs manifest not found: {manifest_path}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"style refs manifest is not valid JSON: {manifest_path}: {exc}") from exc
    refs = data.get("refs") or []
    if not isinstance(refs, list):
        raise ValueError(f"style refs manifest has invalid refs list: {manifest_path}")

    allowed: set[Path] = set()
    base = manifest_path.parent
    for item in refs:
        if not isinstance(item, dict):
            continue
        local_file = str(item.get("local_file") or item.get("downloaded") or "").strip()
        if not local_file:
            continue
        candidate = Path(local_file)
        if not candidate.is_absolute():
            candidate = base / candidate
        if candidate.is_file():
            allowed.add(candidate.resolve())
    return allowed


def _classify_ai_reference(
    ref_path: Path,
    *,
    custom_gallery_root: Path,
    manifest_allowed: set[Path],
) -> str | None:
    try:
        ref_path.relative_to(custom_gallery_root)
        return "gallery"
    except ValueError:
        pass
    if ref_path in manifest_allowed:
        return "literature_manifest"
    return None


def cmd_run(args: argparse.Namespace) -> int:
    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"Error: prompt not found: {prompt_path}", file=sys.stderr)
        return 2
    prompt = prompt_path.read_text(encoding="utf-8")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        _load_refs_plan(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: invalid --refs-plan: {exc}", file=sys.stderr)
        return 2

    if not IMAGE_GEN_PY.exists():
        return _finish_local_route_fallback(
            args,
            prompt,
            out_dir,
            f"image_gen.py was not found at {IMAGE_GEN_PY}",
        )

    refs: list[str] = []
    ref_sources: list[str] = []
    raster_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    custom_gallery_root = (PAPER2PPT_ROOT / "templates" / "technicalroute" / "Custom_gallery").resolve()
    manifest_allowed: set[Path] = set()
    if getattr(args, "refs_manifest", ""):
        try:
            manifest_allowed = _manifest_reference_paths(Path(args.refs_manifest).expanduser().resolve())
        except (OSError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
    for ref in args.refs or []:
        ref_path = Path(ref).expanduser()
        if not ref_path.is_file():
            print(f"Error: reference image not found: {ref}", file=sys.stderr)
            return 2
        ref_resolved = ref_path.resolve()
        if ref_resolved.suffix.lower() == ".svg":
            print(
                f"Error: SVG references are forbidden for AI image generation: {ref_resolved}\n"
                "Use article-derived content.yaml for semantics and Custom_gallery raster images "
                "(.png/.jpg/.webp/.bmp) for style anchors.",
                file=sys.stderr,
            )
            return 2
        if ref_resolved.suffix.lower() not in raster_suffixes:
            print(f"Error: unsupported reference image type for AI generation: {ref_resolved}", file=sys.stderr)
            return 2
        ref_source = _classify_ai_reference(
            ref_resolved,
            custom_gallery_root=custom_gallery_root,
            manifest_allowed=manifest_allowed,
        )
        if ref_source is None:
            manifest_hint = (
                f" or listed in {Path(args.refs_manifest).expanduser().resolve()}"
                if getattr(args, "refs_manifest", "") else ""
            )
            print(
                "Error: AI route references must come from exactly two sources: "
                f"templates/technicalroute/Custom_gallery/{manifest_hint}. "
                f"Rejected: {ref_resolved}",
                file=sys.stderr,
            )
            return 2
        if getattr(args, "gallery_only", False):
            try:
                ref_resolved.relative_to(custom_gallery_root)
            except ValueError:
                print(
                    f"Error: --gallery-only allows refs only under {custom_gallery_root}; got {ref_resolved}",
                    file=sys.stderr,
                )
                return 2
        refs.append(str(ref_resolved))
        ref_sources.append(ref_source)

    if not refs:
        if getattr(args, "allow_no_ref_fallback", False):
            print(
                "Warning: no route reference images were provided; proceeding without refs "
                "because --allow-no-ref-fallback was explicitly set.",
                file=sys.stderr,
            )
        else:
            return _finish_local_route_fallback(
                args,
                prompt,
                out_dir,
                "no Custom_gallery/style_refs raster references were provided",
            )
    if refs and not any(source == "gallery" for source in ref_sources):
        print(
            "Error: Version B AI route generation requires at least one discipline "
            "Custom_gallery raster anchor.",
            file=sys.stderr,
        )
        return 2
    if refs and not getattr(args, "gallery_only", False):
        if not getattr(args, "refs_manifest", ""):
            print(
                "Error: Version B AI route generation requires --refs-manifest "
                "pointing to the research-search style_refs/manifest.json generated "
                "from references/technicalroute/seed_sites.json. Use --gallery-only "
                "only when academic search produced no usable "
                "route/framework/workflow figure references.",
                file=sys.stderr,
            )
            return 2
        if not any(source == "literature_manifest" for source in ref_sources):
            print(
                "Error: Version B AI route generation requires at least one "
                "academic-search route/framework/workflow raster reference listed "
                "in style_refs/manifest.json from the seed_sites.json workflow.",
                file=sys.stderr,
            )
            return 2

    backend_name = (getattr(args, "backend", "") or os.environ.get("IMAGE_BACKEND") or "openai").strip()
    model_name = (getattr(args, "model", "") or "").strip()
    if not model_name and backend_name == "openai":
        model_name = os.environ.get("OPENAI_MODEL") or "gpt-image-2"

    before = {item.resolve() for item in out_dir.iterdir() if item.is_file()}
    cmd = [
        sys.executable,
        str(IMAGE_GEN_PY),
        "--prompt-file",
        str(prompt_path),
        "--aspect_ratio",
        args.aspect_ratio,
        "--image_size",
        args.image_size,
        "-o",
        str(out_dir),
    ]
    if backend_name:
        cmd.extend(["--backend", backend_name])
    if model_name:
        cmd.extend(["--model", model_name])
    if args.filename:
        cmd.extend(["--filename", args.filename])
    if refs:
        for ref in refs:
            cmd.extend(["--reference", ref])

    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    display_cmd = cmd.copy()
    print(">> " + " ".join(display_cmd))
    rc = subprocess.run(cmd, env=env).returncode

    if rc != 0:
        if refs and getattr(args, "allow_no_ref_fallback", False):
            print(
                "Warning: image generation with references failed; retrying without references "
                "because --allow-no-ref-fallback was explicitly set.",
                file=sys.stderr,
            )
            cmd_no_refs = [
                sys.executable,
                str(IMAGE_GEN_PY),
                "--prompt-file",
                str(prompt_path),
                "--aspect_ratio",
                args.aspect_ratio,
                "--image_size",
                args.image_size,
                "-o",
                str(out_dir),
            ]
            if backend_name:
                cmd_no_refs.extend(["--backend", backend_name])
            if model_name:
                cmd_no_refs.extend(["--model", model_name])
            if args.filename:
                cmd_no_refs.extend(["--filename", args.filename])
            rc = subprocess.run(cmd_no_refs, env=env).returncode
        else:
            if refs:
                print(
                    "Warning: image_gen.py failed while reference images were enabled. "
                    "The references were not dropped silently; falling back to a deterministic "
                    "local PNG so the Version B slide remains present.",
                    file=sys.stderr,
                )
            return _finish_local_route_fallback(
                args,
                prompt,
                out_dir,
                f"image_gen.py failed with exit code {rc}",
            )

    generated = _find_generated_image(out_dir, args.filename, before)
    if generated is None:
        expected = f"{Path(args.filename).stem}.[png|jpg|jpeg|webp|bmp|gif]" if args.filename else "a new image file"
        return _finish_local_route_fallback(
            args,
            prompt,
            out_dir,
            f"image_gen.py exited successfully but {expected} was not found in {out_dir}",
        )

    print(f"OK: route_ai_image_path = {generated}")
    return _create_ai_slide_if_requested(args, generated)


# ---------------------------------------------------------------------------
# ??? paper2ppt SVG
# ---------------------------------------------------------------------------


def cmd_embed(args: argparse.Namespace) -> int:
    """Inject a generated route image into an existing SVG as embedded PNG bytes.

    This legacy command is kept for compatibility, but it must never write a
    path-only href for TechnicalRoute AI images. The exported PPTX must contain
    a real embedded PNG media part.
    """
    image_path = Path(args.image).expanduser().resolve()
    target_svg = Path(args.target).expanduser().resolve()
    if not image_path.is_file():
        print(f"Error: image not found: {image_path}", file=sys.stderr)
        return 2
    if not target_svg.is_file():
        print(f"Error: target SVG not found: {target_svg}", file=sys.stderr)
        return 2

    try:
        x, y, w, h = (int(v.strip()) for v in args.bbox.split(","))
    except Exception:
        print(f"Error: bbox must be 'x,y,w,h': {args.bbox}", file=sys.stderr)
        return 2

    try:
        href = _png_data_uri(image_path)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    href_escaped = xml_escape(href, quote=True)
    source_name = xml_escape(image_path.name, quote=True)
    caption = xml_escape(args.caption or "")
    image_tag = (
        f'  <g id="injected_route_image" data-route-source="embedded-png">\n'
        f'    <image id="technicalroute-ai-reference-image" href="{href_escaped}" '
        f'data-ai-image-source="{source_name}" '
        f'x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>\n'
    )
    if caption:
        cap_y = y + h + 18
        image_tag += (
            f'    <text x="{x + w // 2}" y="{cap_y}" font-size="11" fill="#888" '
            f'text-anchor="middle" font-family="Microsoft YaHei,Source Han Sans SC,sans-serif">'
            f"{caption}</text>\n"
        )
    image_tag += "  </g>\n"

    svg_text = target_svg.read_text(encoding="utf-8")
    if "</svg>" not in svg_text:
        print("Error: target SVG is missing </svg>", file=sys.stderr)
        return 2
    new_svg = svg_text.replace("</svg>", image_tag + "</svg>", 1)
    target_svg.write_text(new_svg, encoding="utf-8")
    print(f"OK: embedded PNG data URI into {target_svg} (bbox={args.bbox})")
    return 0


def _copy_image_for_svg(image_path: Path, target_svg: Path) -> str:
    # Copy a route image into project images/ and return an href relative to target SVG.
    if target_svg.parent.name in {"svg_output", "svg_final"}:
        project_root = target_svg.parent.parent
    else:
        project_root = target_svg.parent
        while project_root.parent != project_root:
            if (project_root / "images").is_dir() or (project_root / "spec_lock.md").is_file():
                break
            project_root = project_root.parent
    images_dir = project_root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    dst = images_dir / image_path.name
    if dst.resolve() != image_path.resolve():
        dst.write_bytes(image_path.read_bytes())
    return os.path.relpath(dst, target_svg.parent).replace(os.sep, "/")


def _png_data_uri(image_path: Path) -> str:
    """Return a data:image/png URI so PPTX export embeds bytes, not an external link."""
    data = image_path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        png_bytes = data
    else:
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Version B AI route images must be embedded as PNG. "
                f"The source file is not PNG ({image_path.name}); install Pillow or make image_gen.py output PNG."
            ) from exc
        with Image.open(image_path) as img:
            converted = img.convert("RGBA")
            buffer = io.BytesIO()
            converted.save(buffer, format="PNG")
            png_bytes = buffer.getvalue()
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")


def _parse_bbox_arg(raw: str) -> tuple[int, int, int, int]:
    try:
        x, y, w, h = (int(float(v.strip())) for v in raw.split(","))
    except Exception as exc:
        raise ValueError(f"bbox must be 'x,y,w,h', got: {raw}") from exc
    if w <= 0 or h <= 0:
        raise ValueError(f"bbox width and height must be positive, got: {raw}")
    return x, y, w, h


def cmd_create_ai_slide(args: argparse.Namespace) -> int:
    # Create a standalone SVG slide that embeds the Version B AI route image.
    image_path = Path(args.image).expanduser().resolve()
    if not image_path.is_file():
        print(f"Error: image not found: {image_path}", file=sys.stderr)
        return 2

    out_svg = Path(args.out_svg).expanduser().resolve()
    out_svg.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "ppt43":
        width, height = 1024, 768
        default_bbox = "64,126,896,520"
    else:
        width, height = 1280, 720
        default_bbox = "70,116,1140,520"

    try:
        x, y, w, h = _parse_bbox_arg(args.bbox or default_bbox)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    try:
        href = _png_data_uri(image_path)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    title = xml_escape(args.title or "Research Route: AI Reference Version")
    subtitle = xml_escape(args.subtitle or "")
    caption = xml_escape(args.caption or "AI-generated reference route diagram; semantic content is source-grounded.")
    footer = xml_escape(args.footer or "")
    page_number = xml_escape(args.page_number or "")
    href_escaped = xml_escape(href, quote=True)
    source_name = xml_escape(image_path.name, quote=True)

    subtitle_svg = ""
    if subtitle:
        subtitle_svg = (
            f'  <text id="slide-subtitle" x="64" y="86" font-size="15" fill="#595959" '
            f'font-family="Microsoft YaHei, Arial, sans-serif">{subtitle}</text>\n'
        )
    caption_y = min(height - 58, y + h + 22)
    footer_svg = ""
    if footer:
        footer_svg = (
            f'  <text id="citation-footer" x="64" y="{height - 28}" font-size="10" fill="#777777" '
            f'font-family="Microsoft YaHei, Arial, sans-serif">{footer}</text>\n'
        )
    page_svg = ""
    if page_number:
        page_svg = (
            f'  <text id="page-number" x="{width - 42}" y="{height - 26}" font-size="12" fill="#777777" '
            f'text-anchor="end" font-family="Arial, sans-serif">{page_number}</text>\n'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect id="slide-bg" x="0" y="0" width="{width}" height="{height}" fill="#FFFFFF"/>
  <text id="slide-title" x="64" y="58" font-size="30" font-weight="700" fill="#1F1F1F" font-family="Microsoft YaHei, Arial, sans-serif">{title}</text>
{subtitle_svg}  <g id="technicalroute-ai-reference" data-route-version="B" data-route-source="ai-reference">
    <image id="technicalroute-ai-reference-image" data-ai-image-source="{source_name}" href="{href_escaped}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>
    <text id="technicalroute-ai-reference-caption" x="{x + w // 2}" y="{caption_y}" font-size="11" fill="#777777" text-anchor="middle" font-family="Microsoft YaHei, Arial, sans-serif">{caption}</text>
  </g>
{footer_svg}{page_svg}</svg>
'''
    out_svg.write_text(svg, encoding="utf-8")
    print(f"OK: created AI reference slide SVG: {out_svg}")
    print("    image embedded: data:image/png;base64,<...>")
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
# assemble · 装配 A 版可编辑 SVG（Template SVG variant）
# ---------------------------------------------------------------------------

TEMPLATES_DIR = PAPER2PPT_ROOT / "templates" / "technicalroute" / "templates"
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
      2. Read the template SVG at ``templates/technicalroute/templates/<template_key>.svg``.
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
    legacy_template = _section_as_dict(sections.get("template_version", []))
    template_key = (
        args.template_key
        or source.get("template_key")
        or legacy_template.get("template_key")
        or "pipeline_with_stages"
    )
    if not template_key or template_key.lower() == "none":
        template_key = "pipeline_with_stages"


    template_path = TEMPLATES_DIR / f"{template_key}.svg"
    if not template_path.is_file():
        print(
            f"❌ Template SVG not found: {template_path}\n"
            f"   Check that `{template_key}` is a real key in "
            f"`templates/technicalroute/templates/templates_index.json` and that the SVG file exists.",
            file=sys.stderr,
        )
        return 2

    content_path = Path(args.content).expanduser().resolve()
    if not content_path.is_file():
        print(f"❌ content.yaml not found: {content_path}", file=sys.stderr)
        return 2
    content_data = _load_content_yaml(content_path)

    slot_map = _section_as_dict(sections.get("slot_map", []))
    preset_slot_map_path = TEMPLATES_DIR / f"{template_key}.slot_map.json"
    if preset_slot_map_path.is_file():
        try:
            preset_data = json.loads(preset_slot_map_path.read_text(encoding="utf-8"))
            for key, value in (preset_data.get("slot_map") or {}).items():
                slot_map.setdefault(key, value)
        except json.JSONDecodeError as exc:
            print(f"鉂?Invalid slot-map preset JSON: {preset_slot_map_path}: {exc}", file=sys.stderr)
            return 2
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
        ) or color_var_map.get(
            var_name
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
    parser = argparse.ArgumentParser(description="paper2ppt built-in TechnicalRoute · image prompt + gen + embed")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_prompt = sub.add_parser("prompt", help="拼装 prompt → prompt_ai.md")
    p_prompt.add_argument("--archetype", choices=["thinking", "method", "workflow"])
    p_prompt.add_argument("--content", required=True, help="content.yaml")
    p_prompt.add_argument("--style", help="style_profile.md (optional)")
    p_prompt.add_argument("--reference-mode", choices=["literature", "atlas_only"], default="literature", help="参考模式；atlas_only 时在 prompt 中写入无参考图引导")
    p_prompt.add_argument("--out", required=True, help="prompt_ai.md")
    p_prompt.set_defaults(func=cmd_prompt)

    p_asm = sub.add_parser(
        "assemble",
        help=(
            "装配 A 版可编辑 SVG：读 spec_lock.md 中选好的 template_key，"
            "用 content.yaml 替换占位符 + 用 §colors 替换 var(--*) → 输出 route_template_*.svg"
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

    def add_run_args(p):
        p.add_argument("--prompt", required=True)
        p.add_argument("--aspect_ratio", default="16:9")
        p.add_argument("--image_size", default="2K")
        p.add_argument(
            "--backend",
            default="",
            help="Image backend passed to image_gen.py. Defaults to IMAGE_BACKEND, or openai when unset.",
        )
        p.add_argument(
            "--model",
            default="",
            help="Image model passed to image_gen.py. For default openai backend this resolves to OPENAI_MODEL or gpt-image-2.",
        )
        p.add_argument("--refs", nargs="*", default=[])
        p.add_argument(
            "--refs-manifest",
            default="",
            help="style_refs/manifest.json from the seed_sites.json-driven literature_search.py workflow; only refs listed here may be used as academic-search references.",
        )
        p.add_argument(
            "--refs-plan",
            default="",
            help="route_ai_refs.json from literature_search.py prepare-ai-refs; expands refs and refs-manifest.",
        )
        p.add_argument(
            "--gallery-only",
            action="store_true",
            help="Require all --refs to be raster images under templates/technicalroute/Custom_gallery.",
        )
        p.add_argument("--filename", default="", help="输出文件名（不含扩展名），用于稳定命名 route_ai_<id>")
        p.add_argument("--out", required=True)
        p.add_argument("--out-svg", default="", help="Optional svg_output/<NN>_route_ai.svg path; when set, run-ai-variant also creates the embedded Version B slide.")
        p.add_argument("--title", default="Research Route: AI Reference Version")
        p.add_argument("--subtitle", default="")
        p.add_argument("--caption", default="")
        p.add_argument("--footer", default="")
        p.add_argument("--page-number", default="")
        p.add_argument("--format", choices=["ppt169", "ppt43"], default="ppt169")
        p.add_argument("--bbox", default="", help="Optional x,y,w,h image box for --out-svg.")
        p.add_argument(
            "--allow-no-ref-fallback",
            action="store_true",
            help="Explicitly allow a retry without reference images when ref-based generation fails.",
        )
        p.add_argument(
            "--no-local-fallback",
            action="store_true",
            help="Fail instead of creating a deterministic local PNG when image generation cannot complete.",
        )
        p.set_defaults(func=cmd_run)

    p_run = sub.add_parser(
        "run",
        help=(
            "兼容别名：生成 B 版 AI参考 PNG。建议新流程使用 run-ai-variant。"
            "默认 backend = gemini（nano banana pro），可切 qwen（image2）等。"
        ),
    )
    add_run_args(p_run)

    p_run_ai = sub.add_parser(
        "run-ai-variant",
        help=(
            "生成 B 版 AI参考 PNG：把 Custom_gallery / style_refs 图当 --refs 喂进去作风格 anchor。"
            "这是与 assemble 并列的必跑产物，不是模板失败后的补救路径。"
        ),
    )
    add_run_args(p_run_ai)

    p_emb = sub.add_parser("embed", help="Compatibility: inject a generated route PNG into an existing SVG as embedded PNG bytes")
    p_emb.add_argument("--image", required=True)
    p_emb.add_argument("--target", required=True, help="Target SVG path (svg_output/<NN>_<page>.svg)")
    p_emb.add_argument("--bbox", required=True, help="x,y,w,h, for example 60,120,1160,500")
    p_emb.add_argument("--caption", default="")
    p_emb.set_defaults(func=cmd_embed)

    p_ai_slide = sub.add_parser(
        "create-ai-slide",
        help="Create a standalone SVG page for the Version B AI reference image.",
    )
    p_ai_slide.add_argument("--image", required=True, help="Generated route_ai image path")
    p_ai_slide.add_argument("--out-svg", required=True, help="Target svg_output/<NN>_route_ai.svg path")
    p_ai_slide.add_argument("--title", required=True)
    p_ai_slide.add_argument("--subtitle", default="")
    p_ai_slide.add_argument("--caption", default="")
    p_ai_slide.add_argument("--footer", default="")
    p_ai_slide.add_argument("--page-number", default="")
    p_ai_slide.add_argument("--format", choices=["ppt169", "ppt43"], default="ppt169")
    p_ai_slide.add_argument("--bbox", default="", help="Optional x,y,w,h image box; defaults by format")
    p_ai_slide.set_defaults(func=cmd_create_ai_slide)

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

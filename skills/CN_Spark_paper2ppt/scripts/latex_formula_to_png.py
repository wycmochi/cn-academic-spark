#!/usr/bin/env python3
"""Render LaTeX-style formulas to transparent PNG assets for PPT slides.

The script is intentionally deterministic and local-first. It uses
matplotlib's mathtext renderer, which does not require a system LaTeX install.

Examples:
    python scripts/latex_formula_to_png.py --latex "E=mc^2" --out images/formulas/formula_01.png
    python scripts/latex_formula_to_png.py --formula "E=mc^2" --out-dir images/formulas
    python scripts/latex_formula_to_png.py --input formulas.txt --out-dir images/formulas --manifest images/formulas/manifest.json
    python scripts/latex_formula_to_png.py --block-json formula_01.json --out images/formulas/formula_block_01.png
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
DEFAULT_CJK_FONTS = [
    r"C:/Windows/Fonts/msyh.ttc",
    r"C:/Windows/Fonts/msyhbd.ttc",
    r"C:/Windows/Fonts/simhei.ttf",
    r"C:/Windows/Fonts/simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


@dataclass
class RenderedFormula:
    index: int
    latex: str
    output: str
    width_px: int
    height_px: int


def _load_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from PIL import Image

        return plt, Image
    except Exception as exc:  # pragma: no cover - depends on local env
        raise RuntimeError(
            "Formula rendering requires matplotlib and Pillow. Install "
            "matplotlib or add it to the skill runtime dependencies."
        ) from exc


def normalize_formula(text: str) -> str:
    """Normalize one extracted formula into mathtext syntax."""
    formula = text.strip()
    formula = re.sub(r"^\s*\$\$", "", formula)
    formula = re.sub(r"\$\$\s*$", "", formula)
    formula = re.sub(r"^\s*\\\[\s*", "", formula)
    formula = re.sub(r"\s*\\\]\s*$", "", formula)
    formula = formula.strip()
    if not formula:
        raise ValueError("empty formula")
    if not (formula.startswith("$") and formula.endswith("$")):
        formula = f"${formula}$"
    return formula


def split_formula_file(text: str) -> list[str]:
    r"""Extract formulas from a text file.

    Supports $$...$$ blocks, \[...\] blocks, or one formula per non-empty line.
    """
    blocks: list[str] = []
    for pattern in (r"\$\$(.*?)\$\$", r"\\\[(.*?)\\\]"):
        for match in re.finditer(pattern, text, flags=re.DOTALL):
            value = match.group(1).strip()
            if value:
                blocks.append(value)
    if blocks:
        return blocks
    return [line.strip() for line in text.splitlines() if line.strip()]


def stable_name(prefix: str, formula: str, index: int) -> str:
    digest = hashlib.sha1(formula.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{index:02d}_{digest}.png"


def _load_pillow():
    try:
        from PIL import Image, ImageColor, ImageDraw, ImageFont

        return Image, ImageColor, ImageDraw, ImageFont
    except Exception as exc:  # pragma: no cover - depends on local env
        raise RuntimeError(
            "Formula block rendering requires Pillow. Install Pillow or add it to the skill runtime dependencies."
        ) from exc


def _font(ImageFont, size: int, *, bold: bool = False, font_path: str | None = None):
    candidates: list[str] = []
    if font_path:
        candidates.append(font_path)
    if bold:
        candidates.extend([r"C:/Windows/Fonts/msyhbd.ttc", r"C:/Windows/Fonts/simhei.ttf"])
    candidates.extend(DEFAULT_CJK_FONTS)
    for candidate in candidates:
        try:
            path = Path(candidate)
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _text_width(draw, text: str, font) -> int:
    if not text:
        return 0
    bbox = draw.textbbox((0, 0), text, font=font)
    return int(bbox[2] - bbox[0])


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    text = str(text or "").strip()
    if not text:
        return []
    lines: list[str] = []
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        current = ""
        tokens = list(paragraph) if re.search(r"[\u4e00-\u9fff]", paragraph) else paragraph.split(" ")
        sep = "" if re.search(r"[\u4e00-\u9fff]", paragraph) else " "
        for token in tokens:
            candidate = token if not current else current + sep + token
            if _text_width(draw, candidate, font) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = token
        if current:
            lines.append(current)
    return lines


_PLACEHOLDER_LABELS = {
    "",
    "???",
    "{{definition_label}}",
    "variables",
    "variable",
    "where",
    "where:",
    "where：",
}

_ROLE_TRANSLATIONS = {
    "ridership recoverability metric": "客流恢复力指标",
    "recoverability metric": "恢复力指标",
    "loss function": "损失函数",
    "objective function": "目标函数",
    "regression model": "回归模型",
    "shap value": "SHAP值解释",
    "shap values": "SHAP值解释",
    "attention mechanism": "注意力机制",
    "evaluation metric": "评价指标",
    "variable definition": "变量定义",
}


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _normalize_definition_label(value: object) -> str:
    raw = str(value or "").strip()
    key = raw.strip().strip(":：").lower()
    if "???" in raw or key in _PLACEHOLDER_LABELS:
        return "式中："
    if key in {"variables", "variable", "where"}:
        return "式中："
    return raw or "式中："


def _normalize_formula_role(value: object) -> str:
    raw = str(value or "").strip()
    if not raw or raw.startswith("{{") or "???" in raw:
        return "公式定义"
    if _has_cjk(raw):
        return raw
    key = re.sub(r"\s+", " ", raw).strip().lower()
    if key in _ROLE_TRANSLATIONS:
        return _ROLE_TRANSLATIONS[key]
    return "公式定义"


def _normalize_variable_meaning(value: str) -> str:
    raw = str(value or "").strip()
    if not raw or raw.startswith("{{") or "???" in raw:
        return raw
    if _has_cjk(raw):
        return raw
    lower = re.sub(r"\s+", " ", raw).strip().lower()
    phrase_map = {
        "station i recoverability": "站点 i 的客流恢复力",
        "larger value means smaller accumulated loss": "数值越大表示累计损失越小",
        "old-normal daily ridership": "旧常态日客流量",
        "recovery-phase daily ridership": "恢复阶段日客流量",
        "daily ridership": "日客流量",
        "recovery end time": "恢复结束时间",
        "normal state": "正常状态",
        "recovery phase": "恢复阶段",
    }
    parts = [part.strip(" .") for part in re.split(r"[;；]", lower) if part.strip(" .")]
    translated = [phrase_map.get(part, "") for part in parts]
    if parts and all(translated):
        return "；".join(translated)
    for key, zh in phrase_map.items():
        if key in lower:
            return zh
    return "对应变量的中文含义"


def _format_variable(item) -> str:
    if isinstance(item, str):
        value = item.strip()
        return value if _has_cjk(value) else "变量的中文含义"
    if not isinstance(item, dict):
        value = str(item).strip()
        return value if _has_cjk(value) else "变量的中文含义"
    symbol = str(item.get("symbol") or item.get("name") or "").strip()
    meaning = _normalize_variable_meaning(str(item.get("meaning") or item.get("description") or "").strip())
    suffix = str(item.get("suffix") or "").strip()
    if symbol and meaning:
        row = f"{symbol} \u4e3a{meaning}"
    else:
        row = symbol or meaning
    if suffix:
        row = f"{row}{suffix}"
    return row.strip()


def _fit_image(src, max_width: int, max_height: int):
    width, height = src.size
    if width <= 0 or height <= 0:
        return src
    scale = min(max_width / width, max_height / height, 1.0)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    if new_size == src.size:
        return src
    resampling = getattr(getattr(src, "Resampling", None), "LANCZOS", 1)
    return src.resize(new_size, resampling)


def render_formula_block(block: dict, output_path: Path, *, dpi: int, font_size: float, color: str, pad_inches: float) -> tuple[int, int]:
    """Render formula title, equation, and variable interpretation into one PNG."""
    Image, ImageColor, ImageDraw, ImageFont = _load_pillow()
    latex = str(block.get("latex") or block.get("formula") or "").strip()
    if not latex:
        raise ValueError("block JSON must include latex or formula")

    formula_role = _normalize_formula_role(block.get("formula_role_zh") or block.get("formula_role_cn") or block.get("formula_role") or block.get("role_text") or block.get("title") or "")
    intro_label = _normalize_definition_label(block.get("definition_label") or block.get("intro_label") or "式中：")
    variables = [_format_variable(item) for item in block.get("variables", [])]
    variables = [item for item in variables if item]
    if not variables:
        variables = ["{{variable_1}} \u4e3a{{variable_1_meaning}}\u3002"]

    canvas_width = int(block.get("width") or 1240)
    compact = str(block.get("layout") or "").lower() == "compact" or int(block.get("height") or 0) <= 150
    margin_x = int(block.get("margin_x") or (24 if compact else 56))
    top_y = int(block.get("top_y") or (12 if compact else 30))
    title_x = int(block.get("title_x") or margin_x)
    formula_y = int(block.get("formula_y") or (10 if compact else 18))
    formula_h = int(block.get("formula_height") or (52 if compact else 96))
    body_x = int(block.get("body_x") or (margin_x if compact else 74))
    row_gap = int(block.get("row_gap") or (22 if compact else 42))
    formula_gap = int(block.get("formula_gap") or (22 if compact else 30))
    min_formula_width = int(block.get("min_formula_width") or (440 if compact else 520))

    body_font_size = int(block.get("body_font_size") or (16 if compact else 28))
    title_font_size = int(block.get("title_font_size") or body_font_size)
    title_font = _font(ImageFont, title_font_size, bold=False, font_path=block.get("font_path"))
    body_font = _font(ImageFont, body_font_size, bold=False, font_path=block.get("font_path"))

    probe = Image.new("RGBA", (canvas_width, 240), (255, 255, 255, 0))
    draw = ImageDraw.Draw(probe)
    title_width = _text_width(draw, formula_role, title_font) if formula_role else 0

    if block.get("formula_x") is not None:
        formula_x = int(block.get("formula_x"))
    elif formula_role:
        formula_x = title_x + title_width + formula_gap
        available = canvas_width - formula_x - margin_x
        if available < min_formula_width:
            formula_x = margin_x
            formula_y = max(formula_y, top_y + title_font_size + (8 if compact else 18))
    else:
        formula_x = margin_x

    formula_x = min(max(formula_x, margin_x), canvas_width - margin_x - 180)
    formula_w = int(block.get("formula_width") or (canvas_width - formula_x - margin_x))
    formula_w = max(180, formula_w)

    title_bottom = top_y + (title_font_size + (6 if compact else 10) if formula_role else 0)
    formula_bottom = formula_y + formula_h
    intro_y = int(block.get("intro_y") or max(title_bottom, formula_bottom) + (8 if compact else 24))
    row_y = int(block.get("row_y") or intro_y + (24 if compact else 46))

    wrapped_rows: list[str] = []
    max_body_width = canvas_width - body_x - margin_x
    for variable in variables:
        wrapped = _wrap_text(draw, variable, body_font, max_body_width)
        wrapped_rows.extend(wrapped or [variable])
    row_count = max(1, len(wrapped_rows))
    if compact:
        canvas_height = int(block.get("height") or 120)
        available_rows = max(1, int((canvas_height - row_y - 8) // max(1, row_gap)))
        if len(wrapped_rows) > available_rows:
            wrapped_rows = wrapped_rows[:available_rows]
            if wrapped_rows:
                wrapped_rows[-1] = wrapped_rows[-1].rstrip("。；;,.，") + "..."
    else:
        canvas_height = int(block.get("height") or max(230, row_y + row_count * row_gap + 30))

    bg = block.get("background") or "transparent"
    if str(bg).lower() == "transparent":
        bg_rgba = (255, 255, 255, 0)
    else:
        bg_rgba = ImageColor.getcolor(str(bg), "RGBA")
    image = Image.new("RGBA", (canvas_width, canvas_height), bg_rgba)
    draw = ImageDraw.Draw(image)
    text_color = ImageColor.getcolor(str(color or block.get("color") or "#111111"), "RGBA")

    if formula_role:
        draw.text((title_x, top_y), formula_role, font=title_font, fill=text_color)
    draw.text((body_x, intro_y), intro_label, font=body_font, fill=text_color)

    with tempfile.TemporaryDirectory() as tmp:
        formula_path = Path(tmp) / "formula_inner.png"
        render_formula(latex, formula_path, dpi=dpi, font_size=font_size, color=color, pad_inches=pad_inches)
        formula_img = Image.open(formula_path).convert("RGBA")
        formula_img = _fit_image(formula_img, formula_w, formula_h)
        image.alpha_composite(formula_img, (formula_x, formula_y + max(0, (formula_h - formula_img.height) // 2)))

    y = row_y
    for line in wrapped_rows:
        draw.text((body_x, y), line, font=body_font, fill=text_color)
        y += row_gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return image.size


def render_formula(
    formula: str,
    output_path: Path,
    *,
    dpi: int,
    font_size: float,
    color: str,
    pad_inches: float,
) -> tuple[int, int]:
    plt, Image = _load_matplotlib()
    normalized = normalize_formula(formula)

    fig = plt.figure(figsize=(1, 1), dpi=dpi)
    fig.patch.set_alpha(0)
    text = fig.text(
        0,
        0,
        normalized,
        fontsize=font_size,
        color=color,
        ha="left",
        va="bottom",
    )
    fig.canvas.draw()
    bbox = text.get_window_extent(renderer=fig.canvas.get_renderer())
    width_in = max(bbox.width / dpi + pad_inches * 2, 0.1)
    height_in = max(bbox.height / dpi + pad_inches * 2, 0.1)
    plt.close(fig)

    fig = plt.figure(figsize=(width_in, height_in), dpi=dpi)
    fig.patch.set_alpha(0)
    fig.text(
        pad_inches / width_in,
        pad_inches / height_in,
        normalized,
        fontsize=font_size,
        color=color,
        ha="left",
        va="bottom",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=pad_inches)
    plt.close(fig)

    with Image.open(output_path) as img:
        return img.size


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render LaTeX-style formulas to transparent PNG files."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--formula", "--latex", dest="formula", help="Single formula string")
    source.add_argument("--input", help="Text file with formulas")
    source.add_argument("--block-json", help="JSON file describing one formula explanation block to render as one PNG")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--out", help="Exact output PNG path for a single formula")
    output.add_argument("--out-dir", help="Output directory for stable generated names")
    parser.add_argument("--prefix", default="formula", help="Output filename prefix")
    parser.add_argument("--dpi", type=int, default=240, help="PNG render DPI")
    parser.add_argument("--font-size", type=float, default=28, help="Formula font size in points")
    parser.add_argument("--color", default="#222222", help="Formula color")
    parser.add_argument("--pad-inches", type=float, default=0.04, help="Transparent padding around formula")
    parser.add_argument("--manifest", help="Optional JSON manifest output path")
    args = parser.parse_args()
    if args.input and args.out:
        parser.error("--out is only valid with --formula/--latex or --block-json; use --out-dir for --input batches")
    if not args.out and not args.out_dir:
        parser.error("one of --out or --out-dir is required")
    return args


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else None

    if args.block_json:
        block_path = Path(args.block_json).expanduser().resolve()
        if not block_path.exists():
            print(f"Error: block JSON file not found: {block_path}", file=sys.stderr)
            return 1
        try:
            block = json.loads(block_path.read_text(encoding="utf-8-sig"))
            latex = str(block.get("latex") or block.get("formula") or "")
            if args.out:
                out_path = Path(args.out).expanduser().resolve()
            else:
                assert out_dir is not None
                formula_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(block.get("formula_id") or "formula_block_01"))
                out_path = out_dir / stable_name(formula_id, latex, 1)
            width, height = render_formula_block(
                block,
                out_path,
                dpi=args.dpi,
                font_size=args.font_size,
                color=args.color,
                pad_inches=args.pad_inches,
            )
        except Exception as exc:
            print(f"Error rendering formula block: {exc}", file=sys.stderr)
            return 1
        print(f"[OK] formula block: {out_path} ({width}x{height})")
        if args.manifest:
            manifest_path = Path(args.manifest).expanduser().resolve()
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps([
                    {
                        "index": 1,
                        "formula_id": block.get("formula_id") or "formula_block_01",
                        "latex": normalize_formula(latex),
                        "output": str(out_path),
                        "width_px": width,
                        "height_px": height,
                        "usage": "formula_block_png",
                    }
                ], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Manifest: {manifest_path}")
        return 0

    if args.formula:
        formulas = [args.formula]
    else:
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            print(f"Error: input file not found: {input_path}", file=sys.stderr)
            return 1
        formulas = split_formula_file(input_path.read_text(encoding="utf-8"))

    rendered: list[RenderedFormula] = []
    for index, formula in enumerate(formulas, start=1):
        try:
            normalized = normalize_formula(formula)
            if args.out:
                out_path = Path(args.out).expanduser().resolve()
            else:
                assert out_dir is not None
                out_path = out_dir / stable_name(args.prefix, normalized, index)
            width, height = render_formula(
                normalized,
                out_path,
                dpi=args.dpi,
                font_size=args.font_size,
                color=args.color,
                pad_inches=args.pad_inches,
            )
        except Exception as exc:
            print(f"Error rendering formula {index}: {exc}", file=sys.stderr)
            return 1
        rendered.append(RenderedFormula(index, normalized, str(out_path), width, height))
        print(f"[OK] {index}: {out_path} ({width}x{height})")

    if args.manifest:
        manifest_path = Path(args.manifest).expanduser().resolve()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps([item.__dict__ for item in rendered], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Manifest: {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

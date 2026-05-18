#!/usr/bin/env python3
"""
content_schema.py · 校验 content.yaml 是否符合 references/technicalroute/content-schema.md 中的契约。

Usage:
  python3 content_schema.py validate <project>/content.yaml

输出：
  - OK                — 全通过
  - OK with N warnings — 列出可继续的 warning 项
  - FAIL — 报错并阻塞 prompt 合成
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


VALID_ARCHETYPES = {"thinking", "method", "workflow"}
SUB_VARIANTS = {
    "thinking": {"quad", "cascade", "twin"},
    "method": {"core-steps", "vertical-stack", "formula-grid", "mechanism-block"},
    "workflow": {"horizontal-pipeline", "twin-track", "funnel", "circular"},
}

# 字段长度上限（chars）
LIMITS = {
    "title": 30,
    "subtitle": 60,
    "label": 12,
    "point": 25,
    "interpretation": 60,
    "bottom_anchor_text": 40,
    "core_idea_text": 50,
    "note": 60,
}

# 列表长度区间
LIST_RANGES = {
    "sections_quad": (4, 4),
    "sections_cascade": (3, 5),
    "sections_twin": (2, 2),
    "sections_default": (2, 6),
    "points": (0, 4),
    "steps_core_steps": (2, 4),
    "steps_vertical": (4, 8),
    "steps_default": (1, 8),
    "assumptions": (0, 3),
    "columns": (2, 5),
    "stages_circular": (4, 6),
    "glossary_preserve": (0, 20),
}


class ValidationResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def ok(self) -> bool:
        return not self.errors


def _len(s: Any) -> int:
    return len(str(s)) if s is not None else 0


def _check_str(result: ValidationResult, path: str, value: Any, limit_key: str):
    if value is None:
        return
    limit = LIMITS.get(limit_key)
    if limit is None:
        return
    if _len(value) > limit:
        result.warn(f"{path}: 长度 {_len(value)} > 上限 {limit}，建议截断")


def _check_range(result: ValidationResult, path: str, items: list, range_key: str):
    lo, hi = LIST_RANGES.get(range_key, (0, 99))
    n = len(items)
    if n < lo or n > hi:
        result.err(f"{path}: 长度 {n} 不在 [{lo}, {hi}] 范围内")


def validate_thinking(data: dict, result: ValidationResult):
    sub = data.get("sub_variant", "")
    sections = data.get("sections", [])
    if not isinstance(sections, list):
        result.err("sections must be a list")
        return
    key = "sections_default"
    if sub == "quad":
        key = "sections_quad"
    elif sub == "cascade":
        key = "sections_cascade"
    elif sub == "twin":
        key = "sections_twin"
    _check_range(result, "sections", sections, key)

    for i, sec in enumerate(sections):
        path = f"sections[{i}]"
        if not isinstance(sec, dict):
            result.err(f"{path} must be a mapping")
            continue
        _check_str(result, f"{path}.label", sec.get("label"), "label")
        pts = sec.get("points") or []
        if pts:
            _check_range(result, f"{path}.points", pts, "points")
            for j, p in enumerate(pts):
                _check_str(result, f"{path}.points[{j}]", p, "point")

    ba = data.get("bottom_anchor")
    if isinstance(ba, dict):
        if ba.get("kind") not in {None, "question", "claim", "call_to_action"}:
            result.warn("bottom_anchor.kind 未知，建议用 question / claim / call_to_action")
        _check_str(result, "bottom_anchor.text", ba.get("text"), "bottom_anchor_text")


def validate_method(data: dict, result: ValidationResult):
    sub = data.get("sub_variant", "")
    if sub == "core-steps":
        ci = data.get("core_idea")
        if not isinstance(ci, dict) or not ci.get("text"):
            result.err("core-steps 必须有 core_idea.text")
        else:
            _check_str(result, "core_idea.text", ci["text"], "core_idea_text")
        steps = data.get("steps") or []
        _check_range(result, "steps", steps, "steps_core_steps")
    elif sub == "vertical-stack":
        steps = data.get("steps") or []
        _check_range(result, "steps", steps, "steps_vertical")
    elif sub == "formula-grid":
        formulas = data.get("formulas") or []
        if not formulas:
            result.err("formula-grid 必须有 formulas")
    elif sub == "mechanism-block":
        m = data.get("mechanism")
        if not isinstance(m, dict):
            result.err("mechanism-block 必须有 mechanism dict")
        else:
            if not m.get("inputs"):
                result.err("mechanism.inputs 不能为空")
            if not m.get("outputs"):
                result.err("mechanism.outputs 不能为空")

    for i, step in enumerate(data.get("steps") or []):
        path = f"steps[{i}]"
        if not isinstance(step, dict):
            result.err(f"{path} must be a mapping")
            continue
        _check_str(result, f"{path}.label", step.get("label"), "label")
        _check_str(result, f"{path}.interpretation", step.get("interpretation"), "interpretation")

    assumptions = data.get("assumptions") or []
    if assumptions:
        _check_range(result, "assumptions", assumptions, "assumptions")


def validate_workflow(data: dict, result: ValidationResult):
    sub = data.get("sub_variant", "")
    if sub == "horizontal-pipeline":
        cols = data.get("columns") or []
        _check_range(result, "columns", cols, "columns")
        for i, col in enumerate(cols):
            path = f"columns[{i}]"
            if not isinstance(col, dict):
                result.err(f"{path} must be a mapping")
                continue
            _check_str(result, f"{path}.label", col.get("label"), "label")
    elif sub == "twin-track":
        tracks = data.get("tracks") or []
        if len(tracks) != 2:
            result.err(f"twin-track 必须正好 2 条 track，实际 {len(tracks)}")
        if not data.get("confluence"):
            result.err("twin-track 必须有 confluence")
        if not data.get("output"):
            result.err("twin-track 必须有 output")
    elif sub == "funnel":
        if not data.get("inputs"):
            result.err("funnel 必须有 inputs")
        if not data.get("core"):
            result.err("funnel 必须有 core")
    elif sub == "circular":
        stages = data.get("stages") or []
        _check_range(result, "stages", stages, "stages_circular")


def validate(data: dict) -> ValidationResult:
    result = ValidationResult()

    # 顶层必填
    arche = data.get("archetype")
    if arche not in VALID_ARCHETYPES:
        result.err(f"archetype 必须是 {sorted(VALID_ARCHETYPES)}，当前 = {arche!r}")
        return result
    if not data.get("title"):
        result.err("title 必填")
    _check_str(result, "title", data.get("title"), "title")
    _check_str(result, "subtitle", data.get("subtitle"), "subtitle")

    sub = data.get("sub_variant")
    if sub is not None and sub not in SUB_VARIANTS[arche]:
        result.err(f"sub_variant {sub!r} 不属于 archetype={arche}（合法值 {sorted(SUB_VARIANTS[arche])}）")

    glossary = data.get("glossary_preserve") or []
    if glossary:
        _check_range(result, "glossary_preserve", glossary, "glossary_preserve")

    # 分支
    if arche == "thinking":
        validate_thinking(data, result)
    elif arche == "method":
        validate_method(data, result)
    elif arche == "workflow":
        validate_workflow(data, result)

    return result


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.is_file():
        print(f"❌ 文件不存在：{path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        try:
            data = json.loads(text)
        except Exception:
            print("❌ 未安装 pyyaml 且文件不是合法 JSON。请 `pip install pyyaml`。", file=sys.stderr)
            return 2
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        print("❌ 顶层必须是 mapping / dict", file=sys.stderr)
        return 2

    result = validate(data)

    if args.json:
        out = {
            "ok": result.ok(),
            "errors": result.errors,
            "warnings": result.warnings,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if result.errors:
            print("FAIL")
            for e in result.errors:
                print(f"  ✗ {e}")
        elif result.warnings:
            print(f"OK with {len(result.warnings)} warnings")
            for w in result.warnings:
                print(f"  ⚠ {w}")
        else:
            print("OK")
    return 0 if result.ok() else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate content.yaml against schema")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_v = sub.add_parser("validate", help="校验 content.yaml")
    p_v.add_argument("path", help="content.yaml 路径")
    p_v.add_argument("--json", action="store_true", help="JSON 格式输出")
    p_v.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

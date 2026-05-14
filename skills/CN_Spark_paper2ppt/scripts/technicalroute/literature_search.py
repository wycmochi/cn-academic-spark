#!/usr/bin/env python3
"""
literature_search.py · 学术文献样式检索

按 seed_sites.json 的优先级顺序拼装搜索 URL，配合 IDE 提供的 WebSearch / WebFetch
工具抓取候选论文及其 figure 缩略，落地到 ``<out>/style_refs/``。

主代理（Claude / GPT-4V）应在 SKILL.md Step 2 中：
  1. 调用本脚本 --emit-plan 生成检索计划与每个站点的搜索 URL；
  2. 用 WebSearch / WebFetch 按计划逐站执行；
  3. 用 --record 把抓到的 figure URL + DOI 注入到 manifest.json。

本脚本不直接发起网络请求（避免把 cookie / 限频 / 验证码逻辑揉进来）；它做：
  - 读取 seed_sites.json
  - 编码主题词 + archetype 关键词构造 URL
  - 校验候选图片元信息（尺寸 / 宽高比 / 关键词命中）
  - 维护 manifest.json

Usage:
  python3 literature_search.py emit-plan --topic "<text>" --archetype thinking \\
        --max 8 --out <project_path>/style_refs/

  python3 literature_search.py record --out <project_path>/style_refs/ \\
        --doi "10.xxxx/xxxx" --title "..." --image-url "..." --downloaded ref_001.png

  python3 literature_search.py offline --hints <folder> --out <project_path>/style_refs/

  python3 literature_search.py filter --image <path> --topic "<text>"
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import urllib.parse
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
SEED_SITES = HERE.parent.parent / "references" / "technicalroute" / "seed_sites.json"


def load_seed_sites() -> dict:
    with SEED_SITES.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def archetype_keywords(archetype: str) -> list[str]:
    """每个 archetype 添加的检索词增强。"""
    base = {
        "thinking": [
            "research framework",
            "research design",
            "conceptual framework",
            "研究框架",
            "理论框架",
        ],
        "method": [
            "method overview",
            "model architecture",
            "algorithm framework",
            "方法框架",
            "技术原理",
        ],
        "workflow": [
            "technical route",
            "study workflow",
            "data pipeline",
            "技术路线",
            "研究流程",
        ],
    }
    return base.get(archetype, base["workflow"])


def build_search_urls(topic: str, archetype: str, sites: list[dict]) -> list[dict]:
    """对每个 seed site 构造若干检索 URL。每个站点最多用 2 个增强词。"""
    enhancements = archetype_keywords(archetype)[:2]
    plans: list[dict] = []
    for site in sorted(sites, key=lambda s: s.get("priority", 99)):
        for enhancement in enhancements:
            query = f"{topic} {enhancement}".strip()
            q = urllib.parse.quote_plus(query)
            url = site["search_template"].replace("{q}", q)
            plans.append(
                {
                    "site": site["name"],
                    "kind": site.get("kind", "scholar"),
                    "needs_login": site.get("needs_login", False),
                    "query": query,
                    "url": url,
                    "notes": site.get("notes", ""),
                }
            )
    return plans


@dataclass
class Manifest:
    topic: str
    archetype: str
    max_refs: int
    refs: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def load_manifest(out_dir: Path) -> Manifest | None:
    path = out_dir / "manifest.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Manifest(
        topic=data.get("topic", ""),
        archetype=data.get("archetype", ""),
        max_refs=data.get("max_refs", 8),
        refs=data.get("refs", []),
    )


def save_manifest(out_dir: Path, manifest: Manifest) -> None:
    path = out_dir / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def cmd_emit_plan(args: argparse.Namespace) -> int:
    sites_cfg = load_seed_sites()
    plans = build_search_urls(args.topic, args.archetype, sites_cfg["sites"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if not (out / "manifest.json").exists():
        manifest = Manifest(topic=args.topic, archetype=args.archetype, max_refs=args.max)
        save_manifest(out, manifest)

    plan_path = out / "search_plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "topic": args.topic,
                "archetype": args.archetype,
                "max_refs": args.max,
                "min_refs": sites_cfg.get("min_refs", 5),
                "filter_hints": sites_cfg.get("image_filter_hints", {}),
                "plan": plans,
                "instructions": (
                    "主代理按 priority 顺序执行：调用 WebSearch(url) 取候选论文，"
                    "对每篇 paper 用 WebFetch 获取其 figure URLs，再下载 figure 到 "
                    "style_refs/ref_XXX.png，最后跑 `literature_search.py record` 注入元信息。"
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"✅ 已写入检索计划：{plan_path}")
    print(f"   共 {len(plans)} 个站点检索 URL（{len(sites_cfg['sites'])} 站点 × {len(archetype_keywords(args.archetype)[:2])} 关键词增强）")
    print(f"   目标参考图数：{sites_cfg.get('min_refs', 5)}–{args.max}")
    print()
    print("下一步：主代理用 WebSearch / WebFetch 按 plan 执行，下载图到 style_refs/")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(out) or Manifest(topic="", archetype="", max_refs=8)

    record = {
        "ref_id": f"ref_{len(manifest.refs) + 1:03d}",
        "doi": args.doi or "",
        "title": args.title or "",
        "journal": args.journal or "",
        "year": args.year or "",
        "authors": args.authors or "",
        "source_url": args.source_url or "",
        "image_url": args.image_url or "",
        "local_file": args.downloaded or "",
        "caption_hint": args.caption_hint or "",
        "score": args.score,
    }
    manifest.refs.append(record)
    save_manifest(out, manifest)
    print(f"✅ 已记录 {record['ref_id']} ({record['title']!r})")
    return 0


def cmd_offline(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hints_dir = Path(args.hints)
    if not hints_dir.is_dir():
        print(f"❌ hints 目录不存在：{hints_dir}", file=sys.stderr)
        return 2

    manifest = Manifest(topic=args.topic or "(offline)", archetype=args.archetype or "workflow", max_refs=args.max or 8)
    n = 0
    for src in sorted(hints_dir.iterdir()):
        if src.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        n += 1
        ref_id = f"ref_{n:03d}"
        dest = out / f"{ref_id}{src.suffix.lower()}"
        shutil.copy2(src, dest)
        manifest.refs.append(
            {
                "ref_id": ref_id,
                "doi": "",
                "title": f"(user-supplied) {src.stem}",
                "source_url": "",
                "image_url": "",
                "local_file": dest.name,
                "score": None,
            }
        )
    save_manifest(out, manifest)
    print(f"✅ 离线模式：从 {hints_dir} 复制 {n} 张参考图到 {out}")
    if n < (load_seed_sites().get("min_refs", 5)):
        print(f"⚠️ 参考图数 {n} < 推荐下限 {load_seed_sites().get('min_refs', 5)}，可能影响生图稳定性")
    return 0


GOOD_HINTS = {
    "technical route",
    "research framework",
    "research design",
    "study workflow",
    "conceptual framework",
    "技术路线",
    "研究框架",
    "研究设计",
    "pipeline",
    "workflow",
    "framework",
}
BAD_HINTS = {
    "histogram",
    "scatter plot",
    "regression",
    "boxplot",
    "heatmap",
    "loss curve",
    "ROC",
    "AUC",
    "violin plot",
}


def score_caption(caption: str, topic: str) -> int:
    text = caption.lower()
    s = 0
    for kw in GOOD_HINTS:
        if kw.lower() in text:
            s += 1
    for kw in BAD_HINTS:
        if kw.lower() in text:
            s -= 1
    if topic.lower() and topic.lower() in text:
        s += 1
    return s


def cmd_filter(args: argparse.Namespace) -> int:
    """快速判断一张已下载图是否值得保留。需要 Pillow 才能读尺寸。"""
    try:
        from PIL import Image
    except ImportError:
        print("⚠️ Pillow 未安装，跳过像素 / 宽高比检查，仅打字符串得分", file=sys.stderr)
        Image = None

    img_path = Path(args.image)
    if not img_path.is_file():
        print(f"❌ 文件不存在：{img_path}", file=sys.stderr)
        return 2

    width = height = None
    if Image is not None:
        with Image.open(img_path) as im:
            width, height = im.size

    aspect = (width / height) if width and height else None
    cap_score = score_caption(args.caption or "", args.topic)

    decision = "keep"
    reasons: list[str] = [f"caption_score={cap_score}"]
    if cap_score < 0:
        decision = "drop"
        reasons.append("caption contains too many result-chart hints")
    if width is not None and width < 800:
        decision = "drop"
        reasons.append(f"width {width} < 800")
    if aspect is not None and (aspect < 1.2 or aspect > 3.0):
        decision = "drop"
        reasons.append(f"aspect {aspect:.2f} outside [1.2, 3.0]")

    print(
        json.dumps(
            {
                "image": str(img_path),
                "width": width,
                "height": height,
                "aspect": round(aspect, 3) if aspect else None,
                "caption_score": cap_score,
                "decision": decision,
                "reasons": reasons,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if decision == "keep" else 1


def cmd_assess(args: argparse.Namespace) -> int:
    """评估 style_refs 目录的整体质量，输出 score + recommended_mode（literature / offline / atlas_only）。

    用于 SKILL.md Step 2 完成后，判断是否需要降级到 handling-no-references.md fallback。
    """
    out = Path(args.out)
    manifest = load_manifest(out)
    sites_cfg = load_seed_sites()
    min_refs = sites_cfg.get("min_refs", 5)

    if manifest is None or not manifest.refs:
        decision = {
            "score": 0.0,
            "ref_count": 0,
            "min_required": min_refs,
            "recommended_mode": "atlas_only",
            "rationale": "manifest.json not found or empty; trigger handling-no-references.md fallback",
        }
        print(json.dumps(decision, ensure_ascii=False, indent=2))
        return 1

    # 计分启发式
    n = len(manifest.refs)
    with_doi = sum(1 for r in manifest.refs if r.get("doi"))
    with_local = sum(1 for r in manifest.refs if r.get("local_file"))
    avg_caption_score = (
        sum(r.get("score", 0) or 0 for r in manifest.refs) / max(n, 1)
    )

    # 总分 ∈ [0,1]
    quantity_score = min(n / min_refs, 1.0)
    quality_score = (
        0.4 * (with_local / max(n, 1))
        + 0.3 * (with_doi / max(n, 1))
        + 0.3 * min(max(avg_caption_score, 0) / 3.0, 1.0)
    )
    score = round(0.55 * quantity_score + 0.45 * quality_score, 3)

    if score >= 0.6 and n >= min_refs and with_local >= 3:
        mode = "literature"
        rationale = "sufficient quantity + local files; proceed with literature reference mode"
    elif n >= 3 and with_local >= 3:
        mode = "offline"
        rationale = "marginal quantity but enough local files; treat as offline (user-supplied) refs"
    else:
        mode = "atlas_only"
        rationale = "too few usable refs; fall back to atlas-only per handling-no-references.md"

    decision = {
        "score": score,
        "ref_count": n,
        "min_required": min_refs,
        "with_doi": with_doi,
        "with_local_file": with_local,
        "avg_caption_score": round(avg_caption_score, 2),
        "recommended_mode": mode,
        "rationale": rationale,
    }

    out_file = out / "assess.json"
    out_file.write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    print(f"\n✅ 已写入 {out_file}")
    return 0 if mode != "atlas_only" else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Literature style search for paper2ppt built-in TechnicalRoute")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("emit-plan", help="生成检索计划（搜索 URL + 过滤启发式）")
    p_plan.add_argument("--topic", required=True)
    p_plan.add_argument("--archetype", choices=["thinking", "method", "workflow"], required=True)
    p_plan.add_argument("--max", type=int, default=8)
    p_plan.add_argument("--out", required=True)
    p_plan.set_defaults(func=cmd_emit_plan)

    p_rec = sub.add_parser("record", help="向 manifest.json 注入一条 ref 元信息")
    p_rec.add_argument("--out", required=True)
    p_rec.add_argument("--doi", default="")
    p_rec.add_argument("--title", default="")
    p_rec.add_argument("--journal", default="")
    p_rec.add_argument("--year", default="")
    p_rec.add_argument("--authors", default="")
    p_rec.add_argument("--source-url", default="")
    p_rec.add_argument("--image-url", default="")
    p_rec.add_argument("--downloaded", default="", help="本地文件名（已下载到 out/）")
    p_rec.add_argument("--caption-hint", default="")
    p_rec.add_argument("--score", type=int, default=0)
    p_rec.set_defaults(func=cmd_record)

    p_off = sub.add_parser("offline", help="离线模式：用用户上传的参考图")
    p_off.add_argument("--hints", required=True)
    p_off.add_argument("--out", required=True)
    p_off.add_argument("--topic", default="")
    p_off.add_argument("--archetype", default="workflow")
    p_off.add_argument("--max", type=int, default=8)
    p_off.set_defaults(func=cmd_offline)

    p_flt = sub.add_parser("filter", help="对单张图打分判断是否值得保留")
    p_flt.add_argument("--image", required=True)
    p_flt.add_argument("--topic", default="")
    p_flt.add_argument("--caption", default="")
    p_flt.set_defaults(func=cmd_filter)

    p_ass = sub.add_parser("assess", help="评估 style_refs 整体质量并给出 recommended_mode（literature/offline/atlas_only）")
    p_ass.add_argument("--out", required=True, help="style_refs 目录")
    p_ass.set_defaults(func=cmd_assess)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())


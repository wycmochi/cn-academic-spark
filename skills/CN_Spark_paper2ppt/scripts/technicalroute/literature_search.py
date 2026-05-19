#!/usr/bin/env python3
"""
literature_search.py · 学术文献样式检索

按 seed_sites.json 的优先级顺序拼装搜索 URL，配合 IDE 提供的 WebSearch / WebFetch
工具抓取候选论文及其 figure 缩略，落地到 ``<out>/style_refs/``。

主代理应在 SKILL.md Step 5.5 的 reference collection 阶段：
  1. 先读 references/technicalroute/seed_urls.md（分支规则）和 references/technicalroute/seed_sites.json（唯一站点配置）；
  2. 调用本脚本 emit-plan 生成检索计划与每个站点的搜索 URL；
  2. 用 WebSearch / WebFetch 按计划逐站执行；
  3. 用 record 把抓到的 figure URL + DOI 注入到 manifest.json；
  4. 若文献检索无可用图，则只能用 prepare-ai-refs 进入 Custom_gallery 最近意图兜底。

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

  # offline/user-upload references are rejected for Version B; use prepare-ai-refs fallback.

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
CUSTOM_GALLERY = HERE.parent.parent / "templates" / "technicalroute" / "Custom_gallery"
GALLERY_INDEX = CUSTOM_GALLERY / "gallery_index.json"
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
FORBIDDEN_AI_REF_SUFFIXES = {".svg", ".pptx", ".ppt", ".odp", ".key"}
ARCHETYPE_NEARNESS = {
    "workflow": {"workflow": 6, "method": 4, "thinking": 3},
    "method": {"method": 6, "workflow": 4, "thinking": 2},
    "thinking": {"thinking": 6, "workflow": 3, "method": 2},
}


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
            "model principle diagram",
            "mechanism diagram",
            "algorithm framework",
            "方法框架",
            "模型原理图",
            "机制图",
            "技术原理",
        ],
        "workflow": [
            "technical route",
            "technical route diagram",
            "study workflow",
            "research workflow figure",
            "mechanism diagram",
            "model principle diagram",
            "data pipeline",
            "技术路线",
            "技术路线图",
            "机制图",
            "模型原理图",
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
    print(
        "Error: the offline/user-upload reference branch is forbidden for TechnicalRoute "
        "Version B. Use seed-sites literature refs first, then prepare-ai-refs "
        "--allow-gallery-fallback-after-search --search-completed for Custom_gallery "
        "nearest-intent fallback.",
        file=sys.stderr,
    )
    return 2

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
    "mechanism diagram",
    "model principle diagram",
    "model architecture",
    "methodological framework",
    "graphical abstract",
    "技术路线",
    "技术路线图",
    "机制图",
    "模型原理图",
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


def load_gallery_index() -> dict:
    if GALLERY_INDEX.is_file():
        return json.loads(GALLERY_INDEX.read_text(encoding="utf-8"))
    return {"disciplines": {}}


def _contains_any(text: str, needles: list[str]) -> bool:
    low = text.lower()
    return any(str(needle).lower() in low for needle in needles if needle)


def _tokenize_intent_text(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in re.split(r"[\s,;，；、/|()\[\]{}:：.!?。！？\"'“”‘’<>]+", text.lower()):
        raw = raw.strip()
        if len(raw) >= 2:
            tokens.append(raw)
    return tokens


def _valid_raster_ref(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in RASTER_SUFFIXES


def _reject_forbidden_ref(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in FORBIDDEN_AI_REF_SUFFIXES:
        return f"forbidden AI reference type: {suffix}"
    if suffix not in RASTER_SUFFIXES:
        return f"unsupported AI reference type: {suffix}"
    return None


def _manifest_local_refs(out_dir: Path) -> list[dict]:
    manifest = load_manifest(out_dir)
    if manifest is None:
        return []
    refs: list[dict] = []
    for record in manifest.refs:
        local = str(record.get("local_file") or record.get("downloaded") or "").strip()
        if not local:
            continue
        candidate = Path(local)
        if not candidate.is_absolute():
            candidate = out_dir / candidate
        candidate = candidate.resolve()
        reject = _reject_forbidden_ref(candidate)
        if reject or not candidate.is_file():
            continue
        item = dict(record)
        item["path"] = str(candidate)
        item["source"] = "literature_manifest"
        refs.append(item)
    return refs


def _discipline_candidates(index: dict, discipline: str, topic: str) -> list[tuple[str, dict]]:
    disciplines = index.get("disciplines") or {}
    if not disciplines:
        return []
    wanted = f"{discipline} {topic}".strip()
    scored: list[tuple[int, str, dict]] = []
    for key, cfg in disciplines.items():
        aliases = [key] + list(cfg.get("aliases") or []) + [cfg.get("label_zh", "")]
        score = 2 if discipline and _contains_any(key + " " + cfg.get("label_zh", ""), [discipline]) else 0
        if _contains_any(wanted, aliases):
            score += 4
        scored.append((score, key, cfg))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return []
    positives = [(key, cfg) for score, key, cfg in scored if score > 0]
    if positives:
        return positives
    # Keep fallback gallery-only: when no discipline alias matches, use the
    # closest available gallery discipline rather than borrowing any SVG/PPT
    # template, exported slide, or external image.
    return [(scored[0][1], scored[0][2])]


def _score_gallery_ref(item: dict, topic: str, archetype: str, sub_variant: str) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    item_arch = str(item.get("archetype") or "").strip()
    arch_score = ARCHETYPE_NEARNESS.get(archetype, {}).get(item_arch, 0)
    if arch_score:
        score += arch_score
        reasons.append("exact_archetype" if item_arch == archetype else f"near_archetype:{item_arch}")
    if sub_variant and item.get("sub_variant") == sub_variant:
        score += 4
        reasons.append("exact_sub_variant")
    hay = " ".join([item.get("label", ""), item.get("sub_variant", ""), " ".join(item.get("keywords") or [])])
    hay_low = hay.lower()
    for token in _tokenize_intent_text(topic):
        if token in hay_low:
            score += 1
            reasons.append(f"topic_token:{token}")
    if _contains_any(topic, list(item.get("keywords") or [])):
        score += 3
        reasons.append("keyword_hit")
    if not reasons:
        reasons.append("nearest_available_gallery_anchor")
    return score, reasons


def _select_gallery_refs(
    *,
    topic: str,
    discipline: str,
    archetype: str,
    sub_variant: str,
    max_refs: int,
) -> list[dict]:
    index = load_gallery_index()
    selected: list[tuple[int, dict]] = []
    for discipline_key, cfg in _discipline_candidates(index, discipline, topic):
        for item in cfg.get("refs") or []:
            rel = Path(str(item.get("file") or ""))
            full = (CUSTOM_GALLERY / rel).resolve()
            reject = _reject_forbidden_ref(full)
            if reject or not full.is_file():
                continue
            enriched = dict(item)
            enriched["discipline"] = discipline_key
            enriched["path"] = str(full)
            enriched["source"] = "custom_gallery"
            score, reasons = _score_gallery_ref(enriched, topic, archetype, sub_variant)
            enriched["selection_score"] = score
            enriched["selection_reasons"] = reasons
            enriched["selection_policy"] = "nearest_intent_within_custom_gallery_only"
            enriched["selection_note"] = (
                "Selected from Custom_gallery after completed zero-result seed-site search; "
                "if no exact discipline/archetype match exists, the highest-scoring nearest "
                "intent raster anchor is used. No SVG/PPT/PPTX or editable route source is allowed."
            )
            selected.append((score, enriched))
    selected.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _score, item in selected[:max_refs]]


def _seed_search_completed_evidence(out_dir: Path) -> bool:
    """Return True only when the seed-site academic search has explicit completion evidence."""
    for marker in (
        out_dir / "search_completed.json",
        out_dir / "seed_search_completed.json",
        out_dir / "manifest.json",
    ):
        if not marker.is_file():
            continue
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if bool(data.get("seed_search_completed") or data.get("search_completed") or data.get("completed")):
            return True
    return False


def cmd_prepare_ai_refs(args: argparse.Namespace) -> int:
    """Create the complete, auditable reference plan consumed by run-ai-variant.

    The path is intentionally strict:
    1. Build a search plan only from seed_sites.json and the paper topic/keywords.
    2. Read existing style_refs/manifest.json records produced by literature search.
    3. If those records contain usable raster academic references, use only them.
    4. If and only if no usable literature refs exist, select discipline-matched
       Custom_gallery raster anchors as fallback.
    5. Write route_ai_refs.json; SVG/PPTX/editable route pages are never admitted.
    """
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    topic = " ".join([args.topic or "", args.keywords or ""]).strip()
    if not topic:
        print("Error: --topic or --keywords is required to prepare AI route references", file=sys.stderr)
        return 2

    sites_cfg = load_seed_sites()
    search_plan = {
        "topic": topic,
        "discipline": args.discipline,
        "archetype": args.archetype,
        "sub_variant": args.sub_variant,
        "seed_sites_path": str(SEED_SITES.resolve()),
        "min_refs": sites_cfg.get("min_refs", 5),
        "max_refs": args.max_literature_refs,
        "filter_hints": sites_cfg.get("image_filter_hints", {}),
        "plan": build_search_urls(topic, args.archetype, sites_cfg["sites"]),
        "instructions": [
            "Run WebSearch/WebFetch according to this plan.",
            "Keep only paper figures that are mechanism diagrams, model-principle diagrams, research frameworks, or technical-route/workflow diagrams.",
            "Download accepted raster figures into this style_refs directory and record them with literature_search.py record.",
            "Do not record SVG, PPTX, screenshots of Version A, or any editable PPT route page as AI references."
        ],
    }
    search_plan_path = out / "search_plan.json"
    search_plan_path.write_text(json.dumps(search_plan, ensure_ascii=False, indent=2), encoding="utf-8")

    if not (out / "manifest.json").exists():
        save_manifest(out, Manifest(topic=topic, archetype=args.archetype, max_refs=args.max_literature_refs))

    literature_refs = _manifest_local_refs(out)[: args.max_literature_refs]
    seed_search_completed = (
        bool(literature_refs)
        or bool(getattr(args, "search_completed", False))
        or _seed_search_completed_evidence(out)
    )
    if literature_refs:
        gallery_refs: list[dict] = []
        refs = [item["path"] for item in literature_refs]
        gallery_only = False
        mode = "literature_only"
    else:
        if not getattr(args, "allow_gallery_fallback_after_search", False):
            print(
                "Error: no usable academic-search raster refs are recorded in style_refs/manifest.json. "
                "Do not fall back to Custom_gallery yet. First run the seed_sites.json search plan, "
                "inspect similar papers for mechanism diagrams / model-principle diagrams / technical-route figures, "
                "record accepted raster figures with literature_search.py record, then rerun prepare-ai-refs. "
                "Pass --allow-gallery-fallback-after-search only after that search completed and produced zero usable refs.",
                file=sys.stderr,
            )
            return 2
        if not seed_search_completed:
            print(
                "Error: gallery fallback is blocked because the seed_sites academic search has no completion evidence. "
                "Run the generated search_plan.json first, then either pass --search-completed or write "
                "search_completed.json with {\"completed\": true} only if the search produced zero usable raster refs.",
                file=sys.stderr,
            )
            return 2
        gallery_refs = _select_gallery_refs(
            topic=topic,
            discipline=args.discipline,
            archetype=args.archetype,
            sub_variant=args.sub_variant,
            max_refs=args.max_gallery_refs,
        )
        if not gallery_refs:
            print(
                f"Error: no usable academic-search raster refs and no raster Custom_gallery "
                f"fallback found for discipline={args.discipline!r}, archetype={args.archetype!r}. "
                f"Update {GALLERY_INDEX} or record literature refs from {SEED_SITES}.",
                file=sys.stderr,
            )
            return 2
        refs = [item["path"] for item in gallery_refs]
        gallery_only = True
        mode = "gallery_only_fallback"
    refs_plan = {
        "version": 1,
        "topic": topic,
        "discipline": args.discipline,
        "archetype": args.archetype,
        "sub_variant": args.sub_variant,
        "mode": mode,
        "gallery_only": gallery_only,
        "reference_flow": "academic_search_then_gallery_fallback",
        "seed_search_completed": bool(seed_search_completed),
        "gallery_fallback_after_search": bool(gallery_only and getattr(args, "allow_gallery_fallback_after_search", False)),
        "seed_sites_path": str(SEED_SITES.resolve()),
        "gallery_index_path": str(GALLERY_INDEX.resolve()),
        "search_plan_path": str(search_plan_path),
        "style_refs_manifest": str((out / "manifest.json").resolve()),
        "refs_manifest": "" if gallery_only else str((out / "manifest.json").resolve()),
        "gallery_refs": gallery_refs,
        "literature_refs": literature_refs,
        "refs": refs,
        "forbidden_reference_types": sorted(FORBIDDEN_AI_REF_SUFFIXES),
        "source_policy": {
            "semantic_source": "paper content/content.yaml only",
            "style_sources": [
                "seed_sites literature raster mechanism/model-principle/technical-route figures first",
                "Custom_gallery raster anchors only after seed-site search completed and yielded zero usable literature refs",
                "if no exact Custom_gallery match exists, choose the highest-scoring nearest-intent gallery raster"
            ],
            "fallback_gate": "gallery_only_fallback requires --allow-gallery-fallback-after-search plus seed_search_completed=true",
            "gallery_selection_policy": "nearest_intent_within_custom_gallery_only",
            "forbidden": [
                "Version A editable SVG",
                "any SVG file",
                "any PPTX/PPT file",
                "screenshots of the editable technical route page",
                "any exported PPT slide image or screenshot",
            ],
        },
    }
    refs_plan_path = out / "route_ai_refs.json"
    refs_plan_path.write_text(json.dumps(refs_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: route_ai_refs_plan = {refs_plan_path}")
    print(f"OK: reference_mode = {refs_plan['mode']}")
    print(f"OK: gallery_refs = {len(gallery_refs)}; literature_refs = {len(literature_refs)}")
    if gallery_only:
        print("Warning: no usable literature raster refs recorded yet; using discipline Custom_gallery fallback.", file=sys.stderr)
    return 0


def cmd_assess(args: argparse.Namespace) -> int:
    """评估 style_refs 目录的整体质量，输出 score + recommended_mode（literature_only / gallery_only_fallback）。

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
            "recommended_mode": "gallery_only_fallback",
            "rationale": "manifest.json not found or empty; trigger Custom_gallery fallback after completed seed-site search",
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
        mode = "literature_only"
        rationale = "sufficient quantity + local files; proceed with literature_only reference mode"
    else:
        mode = "gallery_only_fallback"
        rationale = "too few usable literature refs; fall back to Custom_gallery only after completed seed-site search"

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
    return 0 if mode == "literature_only" else 1


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

    p_off = sub.add_parser("offline", help="blocked: user-uploaded references are forbidden for Version B")
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

    p_prep = sub.add_parser(
        "prepare-ai-refs",
        help="Build route_ai_refs.json from seed_sites search plan plus discipline Custom_gallery raster fallback.",
    )
    p_prep.add_argument("--topic", default="", help="Paper topic, title, or abstract keywords.")
    p_prep.add_argument("--keywords", default="", help="Extra paper keywords for seed-site search.")
    p_prep.add_argument("--discipline", default="transportation", help="Discipline key or alias in Custom_gallery/gallery_index.json.")
    p_prep.add_argument("--archetype", choices=["thinking", "method", "workflow"], default="workflow")
    p_prep.add_argument("--sub-variant", default="", help="Optional route subtype, for example recoverability.")
    p_prep.add_argument("--out", required=True, help="Project style_refs directory.")
    p_prep.add_argument("--max-literature-refs", type=int, default=6)
    p_prep.add_argument("--max-gallery-refs", type=int, default=4)
    p_prep.add_argument(
        "--allow-gallery-fallback-after-search",
        action="store_true",
        help=(
            "Allow Custom_gallery fallback only after the seed_sites search plan has been executed "
            "and no usable literature raster refs were found."
        ),
    )
    p_prep.add_argument(
        "--search-completed",
        action="store_true",
        help=(
            "Explicitly mark that search_plan.json was executed and produced zero usable literature "
            "raster references. Required for Custom_gallery fallback unless search_completed.json "
            "or manifest.json already records completed=true."
        ),
    )
    p_prep.set_defaults(func=cmd_prepare_ai_refs)

    p_ass = sub.add_parser("assess", help="评估 style_refs 整体质量并给出 recommended_mode（literature_only/gallery_only_fallback）")
    p_ass.add_argument("--out", required=True, help="style_refs 目录")
    p_ass.set_defaults(func=cmd_assess)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

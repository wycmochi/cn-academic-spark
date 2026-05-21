#!/usr/bin/env python3
"""Maintenance checks for the CN academic paper2ppt skill.

This script is intentionally local-only. It validates the fragile routes that
agents rely on before a release: Python syntax, JSON and template indexes,
conditional workflow readability, formula rendering, TechnicalRoute AI-slide
embedding, and a minimal SVG -> DrawingML PPTX export with openability checks.
"""

from __future__ import annotations

import argparse
import ast
import base64
import json
import os
import re
import shutil
import subprocess
import struct
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import tempfile
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable or "python"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


class IntegrityCheck:
    def __init__(self, *, keep_temp: bool = False, skip_smoke: bool = False) -> None:
        self.keep_temp = keep_temp
        self.skip_smoke = skip_smoke
        self.results: list[CheckResult] = []
        self.failures: list[str] = []
        self.temp_paths: list[Path] = []

    def run(self) -> int:
        checks = [
            self.check_required_docs,
            self.check_python_ast,
            self.check_json_files,
            self.check_template_indexes,
            self.check_core_svg_xml,
            self.check_conditional_workflows,
            self.check_export_docs_guardrails,
        ]
        if not self.skip_smoke:
            checks.extend([
                self.check_formula_png_route,
                self.check_formula_block_no_truncation_gate,
                self.check_technicalroute_ai_slide,
                self.check_direct_ai_pptx_image_slide,
                self.check_route_ai_svg_wrapper_blocked,
                self.check_technicalroute_ai_ref_gate,
                self.check_no_full_slide_raster_gate,
                self.check_empty_content_container_gate,
                self.check_inferred_textbox_shape_gate,
                self.check_multiline_tspan_merge_gate,
                self.check_technicalroute_declared_requirement_gate,
                self.check_technicalroute_default_required_gate,
                self.check_technicalroute_skip_marker_forbidden_gate,
                self.check_technicalroute_stage_gate_blocks_next_phase,
                self.check_route_ai_path_quality_gate,
                self.check_semantic_text_completion_gate,
                self.check_chinese_language_policy_gate,
                self.check_vertical_bounds_quality_gate,
                self.check_textbox_quality_gate,
                self.check_hidden_academic_project_export_blocked,
                self.check_export_quality_gate_blocks_invalid_svg,
                self.check_minimal_pptx_export,
            ])

        for check in checks:
            name = check.__name__.replace("check_", "")
            try:
                detail = check()
            except Exception as exc:  # noqa: BLE001 - maintenance script should report all context
                self._fail(name, f"{type(exc).__name__}: {exc}")
            else:
                self._pass(name, detail)

        if not self.keep_temp:
            for path in self.temp_paths:
                shutil.rmtree(path, ignore_errors=True)

        print("\nSkill integrity summary")
        print("=" * 28)
        for item in self.results:
            prefix = "OK" if item.ok else "FAIL"
            suffix = f" - {item.detail}" if item.detail else ""
            print(f"[{prefix}] {item.name}{suffix}")

        if self.failures:
            print("\nFailures")
            for failure in self.failures:
                print(f"- {failure}")
            return 1
        return 0

    def _pass(self, name: str, detail: str = "") -> None:
        self.results.append(CheckResult(name, True, detail))

    def _fail(self, name: str, detail: str) -> None:
        self.results.append(CheckResult(name, False, detail))
        self.failures.append(f"{name}: {detail}")

    def _run_cmd(self, args: list[str], *, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            args,
            cwd=str(cwd or ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        if proc.returncode != 0:
            tail = "\n".join(proc.stdout.splitlines()[-20:])
            raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(args)}\n{tail}")
        return proc

    def check_required_docs(self) -> str:
        required = [
            "SKILL.md",
            "references/strategist.md",
            "references/executor-base.md",
            "references/academic/executor-academic.md",
            "references/academic/paper-type-guidance.md",
            "references/academic/formula-rendering.md",
            "references/technicalroute/diagram-contract.md",
            "references/technicalroute/seed_sites.json",
            "references/technicalroute/seed_urls.md",
            "references/technicalroute/image-templatedraw.md",
            "references/technicalroute/image-aigenerate.md",
            "templates/design_spec_reference.md",
            "templates/spec_lock_reference.md",
            "scripts/svg_to_pptx.py",
            "scripts/notes_to_docx.py",
            "scripts/pptx_openability_check.py",
            "scripts/template_import/layout_guard.py",
        ]
        missing = [path for path in required if not (ROOT / path).exists()]
        if missing:
            raise AssertionError("missing required files: " + ", ".join(missing))
        return f"{len(required)} files"

    def check_python_ast(self) -> str:
        errors: list[str] = []
        count = 0
        for path in ROOT.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            count += 1
            try:
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
        if errors:
            raise AssertionError("\n".join(errors[:20]))
        return f"{count} Python files"

    def check_json_files(self) -> str:
        count = 0
        errors: list[str] = []
        for path in ROOT.rglob("*.json"):
            count += 1
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
        if errors:
            raise AssertionError("\n".join(errors[:20]))
        return f"{count} JSON files"

    def check_template_indexes(self) -> str:
        errors: list[str] = []

        layouts = self._json(ROOT / "templates/layouts/layouts_index.json")
        for key in layouts:
            folder = ROOT / "templates/layouts" / key
            if not folder.is_dir():
                errors.append(f"layout missing folder: {key}")
            elif not (folder / "design_spec.md").is_file():
                errors.append(f"layout missing design_spec.md: {key}")

        charts = self._json(ROOT / "templates/charts/charts_index.json")
        for key in charts.get("charts", {}):
            if not (ROOT / "templates/charts" / f"{key}.svg").is_file():
                errors.append(f"chart missing SVG: {key}.svg")

        formula = self._json(ROOT / "templates/formula/formula_templates_index.json")
        for key, entry in formula.get("templates", {}).items():
            filename = entry.get("file") or f"{key}.svg"
            if not (ROOT / "templates/formula" / filename).is_file():
                errors.append(f"formula missing SVG: {filename}")
            if entry.get("maxBlocksPerSlide") != 5:
                errors.append(f"formula maxBlocksPerSlide must stay 5: {key}")

        tech = self._json(ROOT / "templates/technicalroute/templates/templates_index.json")
        for key in tech.get("templates", {}):
            if not (ROOT / "templates/technicalroute/templates" / f"{key}.svg").is_file():
                errors.append(f"technicalroute missing SVG: {key}.svg")

        if errors:
            raise AssertionError("\n".join(errors[:50]))
        return (
            f"layouts={len(layouts)}, charts={len(charts.get('charts', {}))}, "
            f"formula={len(formula.get('templates', {}))}, technicalroute={len(tech.get('templates', {}))}"
        )

    @staticmethod
    def _json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def check_core_svg_xml(self) -> str:
        svg_paths: list[Path] = []
        svg_paths.extend((ROOT / "templates/charts").glob("*.svg"))
        svg_paths.extend((ROOT / "templates/formula").glob("*.svg"))
        svg_paths.extend((ROOT / "templates/technicalroute/templates").glob("*.svg"))
        for folder in (ROOT / "templates/layouts").iterdir():
            if folder.is_dir():
                svg_paths.extend(folder.glob("*.svg"))

        errors: list[str] = []
        for path in svg_paths:
            try:
                ET.parse(path)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
        if errors:
            raise AssertionError("\n".join(errors[:50]))
        return f"{len(svg_paths)} core SVG templates"

    def check_conditional_workflows(self) -> str:
        expected = {
            "create-template.md",
            "customize-animations.md",
            "generate-audio.md",
            "resume-execute.md",
            "topic-research.md",
            "verify-charts.md",
            "visual-edit.md",
        }
        folder = ROOT / "conditional-workflows"
        found = {path.name for path in folder.glob("*.md")}
        missing = sorted(expected - found)
        extra = sorted(found - expected)
        if missing:
            raise AssertionError("missing workflows: " + ", ".join(missing))
        bad: list[str] = []
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8-sig")
            if "##" not in text:
                bad.append(f"{path.name}: no section headings")
            if "scripts/" not in text and path.name not in {"topic-research.md"}:
                bad.append(f"{path.name}: no script command references")
        if bad:
            raise AssertionError("\n".join(bad))
        detail = f"{len(found)} workflows"
        if extra:
            detail += f", extra={','.join(extra)}"
        return detail

    def check_export_docs_guardrails(self) -> str:
        checks = {
            "SKILL.md": [
                "Native DrawingML export must read `svg_output/`, not `svg_final/`",
                "pptx_openability_check.py",
                "Never solve this by switching to python-pptx",
                "references/technicalroute/seed_sites.json",
            ],
            "references/technicalroute/seed_urls.md": [
                "references/technicalroute/seed_sites.json",
                "must not become a second hard-coded site list",
            ],
            "references/technicalroute/image-aigenerate.md": [
                "seed_sites.json",
                "exactly two allowed source classes",
                "literature_only",
                "gallery_only_fallback",
                "_direct_image_slides.json",
            ],
            "references/shared-standards.md": [
                "main editable pptx reads `svg_output/`",
                "--allow-legacy-image-pptx",
                "slide-raster-image",
                "default `none`",
            ],
            "scripts/docs/troubleshooting.md": [
                "Do not force native export from `svg_final/`",
                "pptx_openability_check.py",
            ],
        }
        missing: list[str] = []
        for rel, needles in checks.items():
            text = (ROOT / rel).read_text(encoding="utf-8-sig", errors="replace")
            for needle in needles:
                if needle not in text:
                    missing.append(f"{rel}: missing guardrail text: {needle}")

        cli_text = (ROOT / "scripts/svg_to_pptx/pptx_cli.py").read_text(encoding="utf-8")
        if "default: fade" in cli_text:
            missing.append("pptx_cli.py still says transition default is fade")
        if missing:
            raise AssertionError("\n".join(missing))
        return "export/openability guardrails present"

    def check_formula_png_route(self) -> str:
        workdir = Path(tempfile.mkdtemp(prefix="paper2ppt_formula_"))
        self.temp_paths.append(workdir)
        block_json = workdir / "formula_block.json"
        output = workdir / "images/formulas/formula_block_01.png"
        block_json.write_text(
            json.dumps({
                "formula_id": "formula_block_01",
                "formula_role": "核心步骤公式",
                "latex": r"A_{i,\tau}=\sum_j P_j f(C_{ij},\tau),\quad f(C_{ij},\tau)=\begin{cases}1,&C_{ij}<\tau\\0,&C_{ij}\ge \tau\end{cases}",
                "definition_label": "式中：",
                "variables": [
                    {"symbol": "A_{i,\\tau}", "meaning": "县域 i 在成本阈值 tau 下的人口可达性"},
                    {"symbol": "P_j", "meaning": "目的地 j 的人口机会规模"},
                    {"symbol": "C_{ij}", "meaning": "由多模式路径规划得到的 OD 广义阻抗"},
                ],
                "width": 1136,
                "height": 130,
                "layout": "compact",
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._run_cmd([
            PYTHON,
            str(ROOT / "scripts/latex_formula_to_png.py"),
            "--block-json",
            str(block_json),
            "--out",
            str(output),
        ])
        if not output.is_file() or output.stat().st_size < 1000:
            raise AssertionError(f"formula PNG was not created correctly: {output}")
        meta_path = output.with_suffix(".meta.json")
        if not meta_path.is_file():
            raise AssertionError("formula PNG metadata sidecar was not created")
        meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        normalized = str(meta.get("normalized_latex") or "")
        if meta.get("mathtext_validated") is not True or meta.get("renderer") != "matplotlib.mathtext":
            raise AssertionError("formula PNG metadata does not record mathtext validation")
        if r"\begin{cases}" in normalized or r"\end{cases}" in normalized:
            raise AssertionError("formula sanitizer did not normalize unsupported cases syntax")
        return output.name

    def check_formula_block_no_truncation_gate(self) -> str:
        workdir = Path(tempfile.mkdtemp(prefix="paper2ppt_formula_notruncate_"))
        self.temp_paths.append(workdir)
        block_json = workdir / "formula_block.json"
        output = workdir / "images/formulas/formula_block_cost.png"
        block_json.write_text(
            json.dumps({
                "formula_id": "formula_block_cost",
                "formula_role": "广义出行成本",
                "latex": r"G = T \times VoTT + M",
                "definition_label": "式中：",
                "variables": [
                    {"symbol": "G", "meaning": "OD 间综合出行成本，包含时间价值和货币成本。"},
                    {"symbol": "T", "meaning": "路径或方式组合对应的总出行时间。"},
                    {"symbol": "VoTT", "meaning": "时间价值，用于把时间消耗转换为可比较的货币成本。"},
                    {"symbol": "M", "meaning": "票价、燃油、停车、换乘等直接货币成本。"},
                ],
                "width": 900,
                "height": 90,
                "layout": "compact",
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._run_cmd([
            PYTHON,
            str(ROOT / "scripts/latex_formula_to_png.py"),
            "--block-json",
            str(block_json),
            "--out",
            str(output),
        ])
        meta = json.loads(output.with_suffix(".meta.json").read_text(encoding="utf-8-sig"))
        if meta.get("truncated") is not False:
            raise AssertionError("formula block metadata did not record truncated=false")
        variable_rows = meta.get("variable_rows")
        if not isinstance(variable_rows, list) or len(variable_rows) < 4:
            raise AssertionError("formula block metadata lost variable explanation rows")
        if any(str(row).rstrip().endswith(("...", "…")) for row in variable_rows):
            raise AssertionError("formula renderer still truncates variable explanations with ellipses")
        if int(meta.get("height_px") or 0) <= int(meta.get("requested_height_px") or 0):
            raise AssertionError("formula renderer did not grow a too-short compact canvas")
        return "formula block explanations grow canvas instead of truncating"

    def check_technicalroute_ai_slide(self) -> str:
        workdir = Path(tempfile.mkdtemp(prefix="paper2ppt_route_ai_"))
        self.temp_paths.append(workdir)
        png = workdir / "route_ai.png"
        png.write_bytes(base64.b64decode(_ONE_PIXEL_PNG_B64))
        out_svg = workdir / "route_ai_slide.svg"
        proc = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/technicalroute/generate_route_image.py"),
                "create-ai-slide",
                "--image",
                str(png),
                "--out-svg",
                str(out_svg),
            ],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("create-ai-slide should be blocked by default; Version B must not go through SVG")
        if "_direct_image_slides.json" not in proc.stdout or "Do not wrap" not in proc.stdout:
            raise AssertionError("create-ai-slide block did not explain the direct picture manifest route")

        return "create-ai-slide is blocked by default; Version B uses direct PPTX image manifest"


    def check_direct_ai_pptx_image_slide(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_direct_ai_slide_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "images").mkdir(parents=True)
        (project / "notes").mkdir(parents=True)
        (project / "project.json").write_text(
            json.dumps({"name": "paper2ppt_direct_ai_slide", "format": "ppt169"}),
            encoding="utf-8",
        )
        (project / "design_spec.md").write_text(
            "project_type: academic\n"
            "user_requested_page_count: 1\n"
            "requested_regular_page_count: 1\n",
            encoding="utf-8",
        )
        (project / "spec_lock.md").write_text(
            "user_requested_page_count: 1\n"
            "requested_regular_page_count: 1\n",
            encoding="utf-8",
        )
        (project / "ppt_outline_cn.md").write_text(
            "用户页数指标：1 页；AI 技术路线参考图页不计入用户页数指标，最终导出 2 页。\n",
            encoding="utf-8",
        )
        (project / "notes/01_route_template.md").write_text("第 1 页：Version A 技术路线。\n", encoding="utf-8")
        (project / "svg_output/01_route_template.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <text x="64" y="58" font-size="30" font-family="Microsoft YaHei, Arial, sans-serif">研究路线：可编辑模板版</text>
              <g id="technicalroute-template" data-route-version="A">
                <rect x="120" y="150" width="1040" height="380" fill="#F8FAFC" stroke="#CBD5E1"/>
                <text x="170" y="300" font-size="24" font-family="Microsoft YaHei, Arial, sans-serif">路线模板</text>
                <text x="170" y="350" font-size="16" font-family="Microsoft YaHei, Arial, sans-serif">可编辑路线正文用于验证 AI 参考图直插。</text>
              </g>
            </svg>
            """),
            encoding="utf-8",
        )
        route_png = project / "images/route_ai_direct.png"
        try:
            from PIL import Image
        except ImportError as exc:
            raise AssertionError("Pillow is required for direct AI slide smoke PNG generation") from exc
        Image.new("RGB", (4400, 2475), "#0B3A66").save(route_png)
        prompt_gate = route_png.parent / "prompt_ai_refs_gate.md"
        prompt_gate.write_text(
            "[REFERENCE SOURCE GATE - HARD]\n"
            "Allowed visual reference files come from route_ai_refs.json.\n"
            "Do NOT use Version A editable SVGs.\n"
            "Use seed_sites first and Custom_gallery only after zero-result search.\n",
            encoding="utf-8",
        )
        gallery_root = (ROOT / "templates/technicalroute/Custom_gallery").resolve()
        gallery_ref = next(
            (p for p in gallery_root.rglob("*") if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}),
            None,
        )
        if gallery_ref is None:
            raise AssertionError("Custom_gallery has no raster reference for direct AI slide smoke")
        route_style_refs = project / "technicalroute/route_01/style_refs"
        route_style_refs.mkdir(parents=True)
        (route_style_refs / "route_ai_refs.json").write_text(
            json.dumps({
                "version": 1,
                "mode": "gallery_only_fallback",
                "gallery_only": True,
                "reference_flow": "academic_search_then_gallery_fallback",
                "seed_search_completed": True,
                "gallery_fallback_after_search": True,
                "seed_sites_path": str(ROOT / "references/technicalroute/seed_sites.json"),
                "gallery_index_path": str(ROOT / "templates/technicalroute/Custom_gallery/gallery_index.json"),
                "refs": [str(gallery_ref)],
                "gallery_refs": [{
                    "path": str(gallery_ref),
                    "source": "custom_gallery",
                    "selection_policy": "nearest_intent_within_custom_gallery_only",
                }],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        refs_plan_path = route_style_refs / "route_ai_refs.json"
        (route_png.parent / "route_ai_direct_generation_meta.json").write_text(
            json.dumps({
                "version": 1,
                "generator": "image_gen.py",
                "local_fallback": False,
                "image_path": str(route_png),
                "backend_prompt_path": str(prompt_gate),
                "refs_plan_path": str(refs_plan_path),
                "reference_flow": "academic_search_then_gallery_fallback",
                "refs_plan_mode": "gallery_only_fallback",
                "refs": [str(gallery_ref)],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (project / "svg_output/_direct_image_slides.json").write_text(
            json.dumps({
                "version": 1,
                "slides": [{
                    "kind": "technicalroute_ai",
                    "image_path": "../images/route_ai_direct.png",
                    "after_svg_stem": "01_route_template",
                    "fit": "stretch",
                    "role": "technicalroute_ai_reference",
                    "page_count_policy": "extra_reference_page_not_counted",
                    "counts_against_user_page_count": False,
                    "page_count_delta": 1,
                    "narrative_policy": "insert_immediately_after_version_a_without_changing_regular_page_roster",
                    "layout_policy": "direct_full_slide_picture_no_global_layout",
                }],
                "page_count_policy": {
                    "technicalroute_ai": "extra_reference_page_not_counted",
                    "final_slide_count_rule": "final_pptx_slides = user_requested_regular_pages + technicalroute_ai_direct_picture_pages",
                },
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._run_cmd([
            PYTHON,
            str(ROOT / "scripts/svg_to_pptx.py"),
            str(project),
            "--only",
            "native",
            "--no-notes",
            "-q",
        ], timeout=180)
        pptx_files = sorted((project / "exports").glob("*.pptx"))
        if not pptx_files:
            raise AssertionError("direct AI image slide did not export a PPTX")
        with zipfile.ZipFile(pptx_files[-1], "r") as zf:
            slides = sorted(name for name in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", name))
            if len(slides) != 2:
                raise AssertionError(f"expected 2 slides after direct AI insertion, got {len(slides)}")
            slide2 = zf.read("ppt/slides/slide2.xml").decode("utf-8", errors="replace")
            rels2 = zf.read("ppt/slides/_rels/slide2.xml.rels").decode("utf-8", errors="replace")
            if "asvg:svgBlip" in slide2 or ".svg" in rels2.lower():
                raise AssertionError("direct AI picture slide was wrapped as SVG")
            if "relationships/image" not in rels2 or "../media/" not in rels2:
                raise AssertionError("direct AI picture slide missing image relationship")
        return "_direct_image_slides.json inserts route AI PNG as a PPTX picture slide"

    def check_route_ai_svg_wrapper_blocked(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_route_ai_svg_block_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_output/08_research_route_visual.svg").write_text(
            textwrap.dedent(f"""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720" data-route-version="B" data-route-source="ai-reference">
              <image id="technicalroute-ai-reference-image" data-route-version="B" data-route-source="ai-reference"
                     href="data:image/png;base64,{_ONE_PIXEL_PNG_B64}" x="0" y="0" width="1280" height="720"
                     preserveAspectRatio="xMidYMid meet"/>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed a TechnicalRoute AI SVG wrapper")
        output = proc.stdout.lower()
        if "technicalroute_ai_svg_wrapper_forbidden" not in output and "_direct_image_slides.json" not in output:
            raise AssertionError("quality checker did not report the direct PPTX image-slide requirement")
        return "TechnicalRoute AI SVG wrappers are blocked; direct image-slide manifest is required"

    def check_technicalroute_ai_ref_gate(self) -> str:
        workdir = Path(tempfile.mkdtemp(prefix="paper2ppt_route_ref_gate_"))
        self.temp_paths.append(workdir)
        prompt = workdir / "prompt_ai.md"
        prompt.write_text("Create an academic technical route diagram.", encoding="utf-8")
        out_dir = workdir / "output"
        out_dir.mkdir()

        style_refs = workdir / "style_refs"
        style_refs.mkdir()
        lit_ref = style_refs / "literature_route.png"
        lit_ref.write_bytes(base64.b64decode(_ONE_PIXEL_PNG_B64))
        (style_refs / "manifest.json").write_text(
            json.dumps({
                "topic": "metro recoverability",
                "archetype": "workflow",
                "max_refs": 8,
                "refs": [{"local_file": lit_ref.name, "kind": "workflow", "caption": "literature route"}],
            }),
            encoding="utf-8",
        )

        self._run_cmd([
            PYTHON,
            str(ROOT / "scripts/technicalroute/literature_search.py"),
            "prepare-ai-refs",
            "--topic", "metro recoverability xgboost workflow",
            "--discipline", "transportation",
            "--archetype", "workflow",
            "--out", str(style_refs),
        ], timeout=120)
        plan = json.loads((style_refs / "route_ai_refs.json").read_text(encoding="utf-8"))
        if plan.get("mode") != "literature_only":
            raise AssertionError("literature refs were not prioritized as literature_only")
        if [Path(ref).resolve() for ref in plan.get("refs", [])] != [lit_ref.resolve()]:
            raise AssertionError("literature_only plan included non-literature refs")
        if plan.get("gallery_refs"):
            raise AssertionError("gallery refs leaked into literature_only refs plan")

        fallback_refs = workdir / "style_refs_fallback"
        fallback_refs.mkdir()
        (fallback_refs / "manifest.json").write_text(
            json.dumps({"topic": "metro", "archetype": "workflow", "max_refs": 8, "refs": []}),
            encoding="utf-8",
        )
        blocked = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/technicalroute/literature_search.py"),
                "prepare-ai-refs",
                "--topic", "metro recoverability xgboost workflow",
                "--discipline", "transportation",
                "--archetype", "workflow",
                "--out", str(fallback_refs),
            ],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if blocked.returncode == 0:
            raise AssertionError("empty literature manifest fell back to Custom_gallery before search was confirmed")
        if "--allow-gallery-fallback-after-search" not in blocked.stdout:
            raise AssertionError("gallery fallback gate did not explain the required post-search flag")
        self._run_cmd([
            PYTHON,
            str(ROOT / "scripts/technicalroute/literature_search.py"),
            "prepare-ai-refs",
            "--topic", "metro recoverability xgboost workflow",
            "--discipline", "transportation",
            "--archetype", "workflow",
            "--out", str(fallback_refs),
            "--allow-gallery-fallback-after-search",
            "--search-completed",
        ], timeout=120)
        fallback_plan = json.loads((fallback_refs / "route_ai_refs.json").read_text(encoding="utf-8"))
        if fallback_plan.get("mode") != "gallery_only_fallback":
            raise AssertionError("empty literature manifest did not fall back to Custom_gallery only")
        if not fallback_plan.get("gallery_fallback_after_search"):
            raise AssertionError("gallery fallback plan did not record post-search fallback proof")
        gallery_root = (ROOT / "templates/technicalroute/Custom_gallery").resolve()
        for ref in fallback_plan.get("refs", []):
            Path(ref).resolve().relative_to(gallery_root)
        if not all(
            item.get("selection_policy") == "nearest_intent_within_custom_gallery_only"
            for item in fallback_plan.get("gallery_refs", [])
        ):
            raise AssertionError("gallery fallback did not record nearest-intent Custom_gallery selection policy")

        outside = workdir / "outside_ref.png"
        outside.write_bytes(base64.b64decode(_ONE_PIXEL_PNG_B64))
        bad_plan = workdir / "bad_route_ai_refs.json"
        bad_plan.write_text(
            json.dumps({
                "version": 1,
                "mode": "gallery_only_fallback",
                "gallery_only": True,
                "reference_flow": "academic_search_then_gallery_fallback",
                "seed_search_completed": True,
                "gallery_fallback_after_search": True,
                "seed_sites_path": str(ROOT / "references/technicalroute/seed_sites.json"),
                "gallery_index_path": str(ROOT / "templates/technicalroute/Custom_gallery/gallery_index.json"),
                "refs": [str(outside)],
            }),
            encoding="utf-8",
        )

        def run_bad(args: list[str]) -> str:
            proc = subprocess.run(
                [PYTHON, str(ROOT / "scripts/technicalroute/generate_route_image.py"), *args],
                cwd=str(ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=120,
            )
            if proc.returncode == 0:
                raise AssertionError("run-ai-variant unexpectedly passed an invalid reference gate")
            return proc.stdout

        missing_plan_output = run_bad([
            "run-ai-variant",
            "--prompt", str(prompt),
            "--out", str(out_dir),
            "--refs", str(lit_ref),
        ])
        if "--refs-plan" not in missing_plan_output:
            raise AssertionError("missing refs-plan was not reported")

        rejected_ref_output = run_bad([
            "run-ai-variant",
            "--prompt", str(prompt),
            "--out", str(out_dir),
            "--refs-plan", str(bad_plan),
        ])
        if "allowed source classes" not in rejected_ref_output:
            raise AssertionError("non-plan reference was not rejected")

        override_proc = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/technicalroute/generate_route_image.py"),
                "run-ai-variant",
                "--prompt", str(prompt),
                "--out", str(out_dir),
                "--refs-plan", str(fallback_refs / "route_ai_refs.json"),
                "--backend", "openai",
            ],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if override_proc.returncode == 0:
            raise AssertionError("run-ai-variant allowed backend override instead of .env/process config")
        if "must be selected through .env" not in override_proc.stdout:
            raise AssertionError("backend override gate did not explain .env.example-based configuration")

        env = os.environ.copy()
        env["IMAGE_GEN_PATH"] = str(workdir / "missing_image_gen.py")
        no_agent = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/technicalroute/generate_route_image.py"),
                "run-ai-variant",
                "--prompt", str(prompt),
                "--out", str(out_dir),
                "--refs-plan", str(fallback_refs / "route_ai_refs.json"),
                "--filename", "route_ai_should_not_be_local.png",
            ],
            cwd=str(ROOT),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if no_agent.returncode == 0:
            raise AssertionError("run-ai-variant created a local fallback when image_gen.py was missing")
        if "local deterministic fallback is disabled" not in no_agent.stdout.lower():
            raise AssertionError("missing image agent did not fail with the production fallback gate")
        if any(out_dir.glob("route_ai_should_not_be_local*.png")):
            raise AssertionError("missing image agent still wrote a local route AI PNG")

        allow_local = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/technicalroute/generate_route_image.py"),
                "run-ai-variant",
                "--prompt", str(prompt),
                "--out", str(out_dir),
                "--refs-plan", str(fallback_refs / "route_ai_refs.json"),
                "--filename", "route_ai_allow_local_still_blocked.png",
                "--allow-local-fallback",
            ],
            cwd=str(ROOT),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if allow_local.returncode == 0:
            raise AssertionError("--allow-local-fallback still created a fake route AI image")
        if any(out_dir.glob("route_ai_allow_local_still_blocked*.png")):
            raise AssertionError("--allow-local-fallback wrote a forbidden local route AI PNG")

        return "AI refs require seed-site literature search before Custom_gallery fallback; backend/model uses .env; local fallback is blocked"

    def check_no_full_slide_raster_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_raster_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_output/01_bad_raster.svg").write_text(
            textwrap.dedent(f"""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <image id="slide-raster-image" href="data:image/png;base64,{_ONE_PIXEL_PNG_B64}" x="0" y="0" width="1280" height="720"/>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed a full-slide raster page")
        output = proc.stdout.lower()
        if "full-slide raster image" not in output and "slide-raster-image" not in output:
            raise AssertionError("quality checker did not report full-slide raster image")
        return "full-slide raster SVG pages are blocked before PPTX export"

    def check_empty_content_container_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_empty_card_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_output/01_empty_card.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <rect id="findings-panel" x="760" y="150" width="380" height="420" rx="6" fill="#FFFFFF" stroke="#0070C0"/>
              <text x="800" y="205" font-size="28" font-family="Microsoft YaHei, Arial, sans-serif" font-weight="700">发现</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed a large generated content card with no body")
        output = proc.stdout.lower()
        if "heading but no body content" not in output and "content container appears blank" not in output:
            raise AssertionError("quality checker did not report the empty generated content container")
        return "large titled content cards cannot be empty"

    def check_inferred_textbox_shape_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_textbox_shape_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_output/01_overflow_card.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <rect id="header-shape" x="76" y="160" width="238" height="328" rx="6" fill="#FFFFFF" stroke="#CAD8E2"/>
              <rect id="header-shape" x="76" y="160" width="238" height="12" rx="5" fill="#1C9A8A"/>
              <text x="102" y="276" font-size="19" font-family="Microsoft YaHei, Arial, sans-serif"
                    data-box-x="102" data-box-y="258.5" data-box-width="246.2" data-box-height="80">
                <tspan x="102" dy="0">This text box is wider than the card and must fail containment.</tspan>
              </text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed a text box to overflow a header-shape card")
        output = proc.stdout.lower()
        if "not fully wrapped by its visible shape" not in output and "inside its background shape" not in output:
            raise AssertionError("quality checker did not report inferred visible-shape containment")
        return "header-shape card text boxes are bounded by inferred visible shapes"

    def check_multiline_tspan_merge_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_tspan_merge_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "project.json").write_text(
            json.dumps({"name": "paper2ppt_tspan_merge", "format": "ppt169"}),
            encoding="utf-8",
        )
        (project / "svg_output/01.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <rect id="header-shape" x="76" y="160" width="238" height="328" rx="6" fill="#FFFFFF" stroke="#CAD8E2"/>
              <text x="102" y="276" font-size="19" font-family="Microsoft YaHei, Arial, sans-serif"
                    data-box-x="102" data-box-y="258.5" data-box-width="246.2" data-box-height="104">
                <tspan x="102" dy="0">用 XGBoost</tspan>
                <tspan x="102" dy="25.65">捕捉复杂非线性关系，再用</tspan>
                <tspan x="102" dy="25.65">ALE</tspan>
                <tspan x="102" dy="25.65">图解释变量的边际效应与阈值。</tspan>
              </text>
            </svg>
            """),
            encoding="utf-8",
        )
        self._run_cmd([
            PYTHON,
            str(ROOT / "scripts/svg_to_pptx.py"),
            str(project),
            "--only",
            "native",
            "-s",
            "output",
            "-t",
            "none",
            "-a",
            "none",
            "-q",
        ], timeout=180)
        repaired = (project / "svg_output/01.svg").read_text(encoding="utf-8")
        if repaired.count("<text") > 3:
            raise AssertionError("multiline tspan block was split into too many text boxes")
        if "用 XGBoost\n捕捉复杂非线性关系，再用\nALE" not in repaired:
            raise AssertionError("multiline tspan block was not merged into one newline text box")
        self._run_cmd([PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)], timeout=120)
        return "simple multiline tspans merge into one bounded PPT text box"

    def check_technicalroute_declared_requirement_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_route_declared_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "notes").mkdir(parents=True)
        (project / "notes/09.md").write_text("技术路线页：这是全文方法链条。", encoding="utf-8")
        (project / "ppt_outline_cn.md").write_text("09 Workflow - full-paper technical route\n", encoding="utf-8")
        (project / "svg_output/09.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <text x="58" y="58" font-size="28" font-family="Arial, sans-serif">Research Workflow</text>
              <rect x="120" y="180" width="180" height="100" fill="#FFFFFF" stroke="#CBD5E1"/>
              <text x="210" y="235" font-size="20" text-anchor="middle" font-family="Arial, sans-serif">Local flow</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed a declared route/workflow page without TechnicalRoute A/B")
        output = proc.stdout.lower()
        if "technicalroute_requirement_unfulfilled" not in output:
           raise AssertionError("quality checker did not report missing TechnicalRoute A/B chain")
        return "declared workflow pages require TechnicalRoute A/B output"

    def check_technicalroute_default_required_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_route_default_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "ppt_outline_cn.md").write_text(
            "中文学术汇报 | 论文 DOI: 10.0000/example\n"
            "Pages: cover, agenda, method, results, conclusion\n",
            encoding="utf-8",
        )
        (project / "svg_output/01_normal.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <text x="80" y="120" font-size="28" font-family="Arial, sans-serif">Academic report body.</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed an academic deck without TechnicalRoute A/B")
        output = proc.stdout.lower()
        if "academic_default_technicalroute_required" not in output and "academic_project_default_technicalroute_required" not in output:
            raise AssertionError("quality checker did not report the default academic TechnicalRoute gate")
        return "academic decks require TechnicalRoute A/B by default"

    def check_technicalroute_skip_marker_forbidden_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_route_skip_forbidden_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "ppt_outline_cn.md").write_text(
            "中文学术汇报 | paper DOI: 10.0000/example\nPages: cover, methods, results\n",
            encoding="utf-8",
        )
        (project / "spec_lock.md").write_text(
            "technicalroute_required: false\n"
            "technical_route_required: false\n"
            "skip_technicalroute: true\n",
            encoding="utf-8",
        )
        (project / "svg_output/01_normal.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <text x="80" y="120" font-size="28" font-family="Arial, sans-serif">Academic report body.</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed generated skip_technicalroute markers")
        output = proc.stdout.lower()
        if "technicalroute_skip_marker_forbidden" not in output:
            raise AssertionError("quality checker did not report forbidden TechnicalRoute skip markers")
        return "generated technicalroute false/skip markers cannot bypass academic route gate"

    def check_technicalroute_stage_gate_blocks_next_phase(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_route_stage_gate_"))
        self.temp_paths.append(project)
        route_dir = project / "technicalroute/route_01"
        (project / "svg_output").mkdir(parents=True)
        (route_dir / "output").mkdir(parents=True)
        (route_dir / "content.yaml").write_text("archetype: workflow\nstages: []\n", encoding="utf-8")
        (route_dir / "spec_lock.md").write_text(
            "route_template_svg_path: technicalroute/route_01/output/route_template_01.svg\n",
            encoding="utf-8",
        )
        route_svg = textwrap.dedent("""\
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720" data-route-version="A">
          <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
          <g id="technicalroute-template" data-route-version="A">
            <rect x="120" y="150" width="1040" height="380" fill="#F8FAFC" stroke="#CBD5E1"/>
          </g>
        </svg>
        """)
        (route_dir / "output/route_template_01.svg").write_text(route_svg, encoding="utf-8")
        (project / "svg_output/01_route_template.svg").write_text(route_svg, encoding="utf-8")
        gate_proc = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/technicalroute/generate_route_image.py"),
                "gate",
                "--project",
                str(project),
                "--route-workdir",
                str(route_dir),
                "--after-svg-stem",
                "01_route_template",
            ],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if gate_proc.returncode == 0:
            raise AssertionError("TechnicalRoute stage gate passed even though Version B was missing")
        gate_output = gate_proc.stdout.lower()
        if "version b ai route png is missing" not in gate_output:
            raise AssertionError("TechnicalRoute stage gate did not report missing Version B PNG")

        finalize_proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/finalize_svg.py"), str(project), "-q"],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if finalize_proc.returncode == 0:
            raise AssertionError("finalize_svg continued even though TechnicalRoute A/B gate failed")
        if "TechnicalRoute stage gate failed" not in finalize_proc.stdout:
            raise AssertionError("finalize_svg did not surface the TechnicalRoute stage gate failure")
        return "missing TechnicalRoute Version B blocks gate and finalize"

    def check_route_ai_path_quality_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_route_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "technicalroute/route_01/output").mkdir(parents=True)
        route_png = project / "technicalroute/route_01/output/route_ai_gate.png"
        route_png.write_bytes(base64.b64decode(_ONE_PIXEL_PNG_B64))
        (project / "spec_lock.md").write_text(
            "route_ai_image_path: technicalroute/route_01/output/route_ai_gate.png\n",
            encoding="utf-8",
        )
        (project / "svg_output/01_route_template.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <text x="64" y="58" font-size="30" font-family="Arial, sans-serif">Research Route: Editable Template Version</text>
              <g id="technicalroute-template" data-route-version="A">
                <rect x="120" y="150" width="1040" height="380" fill="#F8FAFC" stroke="#CBD5E1"/>
              </g>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker did not fail when route_ai_image_path was not embedded")
        output = proc.stdout.lower()
        if "technicalroute_ai_slide_missing" not in output and "technicalroute_missing_ai_page" not in output:
            raise AssertionError("quality checker did not report missing AI route slide")
        return "missing route_ai_image_path embedding is blocked"

    def check_semantic_text_completion_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_semantic_text_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_output/01_truncated_text.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <text id="bottom-insight" x="90" y="620" font-size="24" font-family="Arial, sans-serif"
                    data-box-x="80" data-box-y="590" data-box-width="980" data-box-height="50">本文切入点 构建多模式、多尺度城际可达性框架,</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed visible text ending with dangling punctuation")
        output = proc.stdout.lower()
        if "semantically truncated" not in output:
            raise AssertionError("quality checker did not report dangling/truncated visible text")
        return "dangling punctuation at the end of visible content text is blocked"

    def check_chinese_language_policy_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_language_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "ppt_outline_cn.md").write_text("中文学术汇报输出；英文论文正文页也需要中文讲述。", encoding="utf-8")
        (project / "svg_output/01_cover.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <text x="90" y="210" font-size="38" font-family="Arial, sans-serif"
                    data-box-x="90" data-box-y="170" data-box-width="900" data-box-height="70">High-speed rail impacts on intercity accessibility</text>
            </svg>
            """),
            encoding="utf-8",
        )
        (project / "svg_output/02_body.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <text x="72" y="76" font-size="32" font-family="Arial, sans-serif"
                    data-box-x="72" data-box-y="42" data-box-width="1040" data-box-height="48">1 Problem Definition: HSR Accessibility Needs Integrated Network Evaluation</text>
              <text x="100" y="180" font-size="24" font-family="Arial, sans-serif"
                    data-box-x="100" data-box-y="150" data-box-width="760" data-box-height="70">Transportation networks and land use jointly determine accessibility outcomes.</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed English-only generated PPT text in a Chinese deck")
        output = proc.stdout.lower()
        if "cover_title_missing_chinese_translation" not in output or "non_chinese_generated_text" not in output:
            raise AssertionError("quality checker did not report the Chinese output language policy violations")
        return "Chinese academic decks block English-only cover/body generated text"

    def check_vertical_bounds_quality_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_vertical_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_output/01_overflow_table.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <rect id="table-row-late" x="150" y="680" width="960" height="64" fill="#F8FAFC" stroke="#CBD5E1"/>
              <text id="table-row-text" x="170" y="704" font-size="18" font-family="Arial, sans-serif"
                    data-box-x="170" data-box-y="692" data-box-width="900" data-box-height="28">Stage 3 must not enter the footer zone.</text>
              <rect id="bottom_banner" data-role="footer" x="64" y="656" width="1152" height="32" fill="#003D73"/>
              <text id="citation-footer" data-role="footer" x="64" y="704" font-size="10" font-family="Arial, sans-serif">[1] Citation footer</text>
              <text id="page-number" data-role="page-number" x="1216" y="704" font-size="12" font-family="Arial, sans-serif">05</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker allowed body content to overflow into footer/canvas bounds")
        output = proc.stdout.lower()
        if "footer protected-region violation" not in output and "slide canvas bounds violation" not in output:
            raise AssertionError("quality checker did not report vertical bounds/footer protected-region violation")
        return "body content cannot overflow canvas or footer protected regions"

    def check_textbox_quality_gate(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_textbox_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_output/01_bad_textbox.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <rect id="card-a" x="100" y="120" width="260" height="96" fill="#F8FAFC" stroke="#CBD5E1"/>
              <text x="110" y="150" font-size="24" font-family="Arial, sans-serif">This long sentence crosses the card boundary and should fail.</text>
              <text x="112" y="158" font-size="24" font-family="Arial, sans-serif">Overlapping text box should fail.</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [PYTHON, str(ROOT / "scripts/svg_quality_checker.py"), str(project)],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("quality checker did not fail overflowing/overlapping text boxes")
        output = proc.stdout.lower()
        if "overlapping text boxes" not in output and "not fully wrapped" not in output:
            raise AssertionError("quality checker did not report text box overlap/containment")
        return "overflowing and overlapping text boxes are blocked"

    def check_hidden_academic_project_export_blocked(self) -> str:
        temp = Path(tempfile.mkdtemp(prefix="paper2ppt_hidden_project_"))
        self.temp_paths.append(temp)
        project = temp / ".codex" / "skills" / "CN_Spark_paper2ppt" / "projects" / "hidden_academic"
        (project / "svg_output").mkdir(parents=True)
        (project / "notes").mkdir(parents=True)
        (project / "design_spec.md").write_text("project_type: academic\n", encoding="utf-8")
        (project / "spec_lock.md").write_text("project_type: academic\n", encoding="utf-8")
        (project / "ppt_outline_cn.md").write_text("中文学术汇报 | DOI: 10.0000/example\n", encoding="utf-8")
        (project / "project.json").write_text(
            json.dumps({"name": "hidden_academic", "format": "ppt169"}),
            encoding="utf-8",
        )
        (project / "notes/01.md").write_text("第 1 页讲稿。\n", encoding="utf-8")
        (project / "svg_output/01.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <text x="80" y="120" font-size="28" font-family="Arial, sans-serif">Academic body.</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/svg_to_pptx.py"),
                str(project),
                "--only",
                "native",
                "-s",
                "output",
                "-q",
            ],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        if proc.returncode == 0:
            raise AssertionError("PPTX export allowed an academic project under .codex/skills")
        if "must not live under .codex/skills" not in proc.stdout:
            raise AssertionError("hidden-project block did not explain the visible artifact requirement")
        return "academic exports require a user-visible project tree"

    def check_export_quality_gate_blocks_invalid_svg(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_export_gate_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir(parents=True)
        (project / "project.json").write_text(
            json.dumps({"name": "paper2ppt_export_gate", "format": "ppt169"}),
            encoding="utf-8",
        )
        (project / "svg_output/01_bad_overlap.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <rect id="card-a" x="120" y="120" width="360" height="180" rx="6" fill="#F8FAFC" stroke="#CBD5E1"/>
              <text id="bad-a" x="150" y="180" font-family="Arial, sans-serif" font-size="24" fill="#111827" data-box-x="150" data-box-y="140" data-box-width="260" data-box-height="82" data-shape-x="120" data-shape-y="120" data-shape-width="360" data-shape-height="180">Invalid overlapping content A</text>
              <text id="bad-b" x="154" y="184" font-family="Arial, sans-serif" font-size="24" fill="#111827" data-box-x="154" data-box-y="144" data-box-width="260" data-box-height="82" data-shape-x="120" data-shape-y="120" data-shape-width="360" data-shape-height="180">Invalid overlapping content B</text>
            </svg>
            """),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                PYTHON,
                str(ROOT / "scripts/svg_to_pptx.py"),
                str(project),
                "--only",
                "native",
                "-s",
                "output",
                "--no-notes",
                "-q",
            ],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
        )
        if proc.returncode == 0:
            raise AssertionError("PPTX export succeeded even though SVG quality errors were present")
        if "SVG quality gate failed before PPTX export" not in proc.stdout:
            raise AssertionError("PPTX export did not report the pre-export quality gate failure")
        if list((project / "exports").glob("*.pptx")):
            raise AssertionError("PPTX was exported after a failed quality gate")
        reports = list((project / "exports").glob("*quality_report.md"))
        if not reports:
            raise AssertionError("failed quality gate did not write a Markdown quality report")
        if "Detected overlapping text boxes" not in reports[-1].read_text(encoding="utf-8", errors="replace"):
            raise AssertionError("quality report does not include the blocking text-box failure")
        return "invalid SVG cannot bypass pre-export quality gate"

    def check_minimal_pptx_export(self) -> str:
        project = Path(tempfile.mkdtemp(prefix="paper2ppt_export_"))
        self.temp_paths.append(project)
        (project / "svg_output").mkdir()
        (project / "notes").mkdir()
        (project / "project.json").write_text(
            json.dumps({"name": "paper2ppt_export", "format": "ppt169"}),
            encoding="utf-8",
        )
        (project / "svg_output/01_smoke.svg").write_text(
            textwrap.dedent("""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
              <rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
              <rect x="120" y="120" width="360" height="115" rx="6" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="2"/>
              <text id="smoke-card-body" x="148" y="190" font-family="Arial, sans-serif" font-size="18" fill="#334155" data-box-x="148" data-box-y="164" data-box-width="304" data-box-height="44" data-shape-x="120" data-shape-y="120" data-shape-width="360" data-shape-height="115">Editable smoke body validates a stable card.</text>
              <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M 0 0 L 8 4 L 0 8 Z" fill="#64748B"/></marker></defs>
              <line x1="120" y1="340" x2="1160" y2="340" stroke="#A6A6A6" stroke-width="2" stroke-dasharray="8 6"/>
              <polyline points="140,470 320,470 360,510 540,510" fill="none" stroke="#64748B" stroke-width="3" marker-end="url(#arrow)"/>
              <path d="M 620 470 L 780 470 L 820 510 L 980 510" fill="none" stroke="#64748B" stroke-width="3" marker-end="url(#arrow)"/>
              <text x="140" y="400" font-family="Arial, sans-serif" font-size="24" fill="#334155">Native DrawingML should stay stable.</text>
            </svg>
            """),
            encoding="utf-8",
        )
        (project / "notes/01_smoke.md").write_text(
            "# 1_Smoke Export\nThis note validates notesSlide and notesMaster packaging.\n",
            encoding="utf-8",
        )
        self._run_cmd([
            PYTHON,
            str(ROOT / "scripts/svg_to_pptx.py"),
            str(project),
            "--only",
            "native",
            "-s",
            "output",
            "-t",
            "none",
            "-a",
            "none",
            "-q",
        ], timeout=180)
        pptx_files = sorted((project / "exports").glob("*.pptx"))
        if not pptx_files:
            raise AssertionError("no PPTX exported")
        quality_reports = sorted((project / "exports").glob("*quality_report.md"))
        if not quality_reports:
            raise AssertionError("PPTX export did not write a Markdown quality report")
        if "Status: `PASS`" not in quality_reports[-1].read_text(encoding="utf-8", errors="replace"):
            raise AssertionError("successful export quality report does not record PASS status")
        artifact_manifests = sorted((project / "exports").glob("*intermediate_artifacts.md"))
        if not artifact_manifests:
            raise AssertionError("PPTX export did not write an intermediate artifact manifest")
        if "svg_output" not in artifact_manifests[-1].read_text(encoding="utf-8", errors="replace"):
            raise AssertionError("intermediate artifact manifest does not list svg_output")
        pptx = pptx_files[-1]
        self._run_cmd([
            PYTHON,
            str(ROOT / "scripts/pptx_openability_check.py"),
            str(pptx),
            "--fix-permissions",
        ], timeout=120)
        with zipfile.ZipFile(pptx, "r") as zf:
            names = set(zf.namelist())
            if "ppt/notesMasters/notesMaster1.xml" in names:
                raise AssertionError("minimal export unexpectedly embedded PPTX notes")
            if any(name.startswith("ppt/notesSlides/") or name.startswith("ppt/notesMasters/") for name in names):
                raise AssertionError("minimal export unexpectedly contains PPTX notes parts")
            if "ppt/presentation.xml" in names:
                pres_xml = zf.read("ppt/presentation.xml").decode("utf-8", errors="replace")
                if "<p:notesMasterIdLst" in pres_xml or "<p:notesMasterId" in pres_xml:
                    raise AssertionError("minimal export unexpectedly contains notes master metadata")
                if "<p:notesSz" not in pres_xml:
                    raise AssertionError("minimal export is missing required presentation notesSz metadata")
            for rel_name in sorted(name for name in names if name.endswith(".rels")):
                rel_xml = zf.read(rel_name).decode("utf-8", errors="replace")
                if "relationships/notesSlide" in rel_xml or "relationships/notesMaster" in rel_xml:
                    raise AssertionError(f"minimal export unexpectedly contains notes relationship: {rel_name}")
            slide_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8", errors="replace")
            if "<p:transition" in slide_xml:
                raise AssertionError("minimal native export contains a slide transition")
            if slide_xml.count("<a:custGeom") > 0:
                raise AssertionError("line/polyline/simple path smoke exported custom geometry")
        if any((project / "backup").glob("**/*.pptx")):
            raise AssertionError("default native export unexpectedly created a legacy backup PPTX")
        if any((project / "exports").glob("*_svg.pptx")):
            raise AssertionError("default native export unexpectedly created an SVG-image PPTX")
        docx_files = sorted((project / "exports").glob("*speaker_notes.docx"))
        if not docx_files:
            raise AssertionError("speaker notes DOCX was not exported")
        with zipfile.ZipFile(docx_files[-1], "r") as zf:
            if "word/document.xml" not in set(zf.namelist()):
                raise AssertionError("speaker notes DOCX missing word/document.xml")
            doc_xml = zf.read("word/document.xml").decode("utf-8", errors="replace")
            if "01_smoke" in doc_xml or "w:type=\"page\"" in doc_xml:
                raise AssertionError("speaker notes DOCX should be a continuous manuscript without slide headings or page breaks")
            if "This note validates notesSlide" not in doc_xml:
                raise AssertionError("speaker notes DOCX missing continuous note body")
            if "第 1 页：This note validates notesSlide" not in doc_xml:
                raise AssertionError("speaker notes DOCX missing slide-number paragraph prefix")
        return pptx.name


_ONE_PIXEL_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAF"
    "gwJ/lm1sTAAAAABJRU5ErkJggg=="
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local integrity checks for CN_Spark_paper2ppt.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary smoke-test projects.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip formula, TechnicalRoute, and PPTX export smoke tests.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return IntegrityCheck(keep_temp=args.keep_temp, skip_smoke=args.skip_smoke).run()


if __name__ == "__main__":
    raise SystemExit(main())

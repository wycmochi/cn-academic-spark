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
import shutil
import subprocess
import sys
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
                self.check_technicalroute_ai_slide,
                self.check_technicalroute_ai_ref_gate,
                self.check_route_ai_path_quality_gate,
                self.check_textbox_quality_gate,
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
            ],
            "references/shared-standards.md": [
                "native pptx reads `svg_output/`",
                "legacy/preview pptx reads `svg_final/`",
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
                "latex": r"y = \alpha + \beta x",
                "definition_label": "式中：",
                "variables": [
                    {"symbol": "y", "meaning": "因变量"},
                    {"symbol": "x", "meaning": "解释变量"},
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
        return output.name

    def check_technicalroute_ai_slide(self) -> str:
        workdir = Path(tempfile.mkdtemp(prefix="paper2ppt_route_ai_"))
        self.temp_paths.append(workdir)
        png = workdir / "route_ai.png"
        png.write_bytes(base64.b64decode(_ONE_PIXEL_PNG_B64))
        out_svg = workdir / "route_ai_slide.svg"
        self._run_cmd([
            PYTHON,
            str(ROOT / "scripts/technicalroute/generate_route_image.py"),
            "create-ai-slide",
            "--image",
            str(png),
            "--out-svg",
            str(out_svg),
            "--title",
            "Research Route: AI Reference Version",
        ])
        text = out_svg.read_text(encoding="utf-8")
        if 'href="data:image/png;base64,' not in text:
            raise AssertionError("AI route slide did not embed PNG data URI")
        if 'data-ai-image-source="route_ai.png"' not in text:
            raise AssertionError("AI route slide missing data-ai-image-source marker")

        project = workdir / "project"
        (project / "svg_output").mkdir(parents=True)
        (project / "project.json").write_text(
            json.dumps({"name": "route_ai_embed", "format": "ppt169"}),
            encoding="utf-8",
        )
        shutil.copy2(out_svg, project / "svg_output/01_route_ai.svg")
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
            "--no-notes",
            "-q",
        ], timeout=180)
        pptx_files = sorted((project / "exports").glob("*.pptx"))
        if not pptx_files:
            raise AssertionError("AI route slide did not export a PPTX")
        with zipfile.ZipFile(pptx_files[-1], "r") as zf:
            names = set(zf.namelist())
            media_pngs = [name for name in names if name.startswith("ppt/media/") and name.endswith(".png")]
            if not media_pngs:
                raise AssertionError("AI route PNG was not embedded into PPTX media")
            rels = zf.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8", errors="replace")
            if "../media/" not in rels or "image" not in rels:
                raise AssertionError("AI route slide missing image relationship in PPTX")
        return out_svg.name

    def check_technicalroute_ai_ref_gate(self) -> str:
        workdir = Path(tempfile.mkdtemp(prefix="paper2ppt_route_ref_gate_"))
        self.temp_paths.append(workdir)
        prompt = workdir / "prompt_ai.md"
        prompt.write_text("Create an academic technical route diagram.", encoding="utf-8")
        out_dir = workdir / "output"
        out_dir.mkdir()
        outside = workdir / "outside_ref.png"
        outside.write_bytes(base64.b64decode(_ONE_PIXEL_PNG_B64))
        style_refs = workdir / "style_refs"
        style_refs.mkdir()
        manifest = style_refs / "manifest.json"
        manifest.write_text(
            json.dumps({"topic": "smoke", "archetype": "workflow", "max_refs": 8, "refs": []}),
            encoding="utf-8",
        )
        gallery_root = ROOT / "templates/technicalroute/Custom_gallery"
        gallery_ref = next(gallery_root.rglob("*.png"), None)
        if gallery_ref is None:
            gallery_ref = next(gallery_root.rglob("*.jpg"), None)
        if gallery_ref is None:
            raise AssertionError("no Custom_gallery raster reference found for smoke test")

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

        missing_manifest_output = run_bad([
            "run-ai-variant",
            "--prompt", str(prompt),
            "--out", str(out_dir),
            "--refs", str(gallery_ref),
        ])
        if "--refs-manifest" not in missing_manifest_output:
            raise AssertionError("missing refs-manifest was not reported")

        rejected_ref_output = run_bad([
            "run-ai-variant",
            "--prompt", str(prompt),
            "--out", str(out_dir),
            "--refs-manifest", str(manifest),
            "--refs", str(gallery_ref), str(outside),
        ])
        if "must come from exactly two sources" not in rejected_ref_output:
            raise AssertionError("non-manifest reference was not rejected")

        return "AI refs limited to Custom_gallery plus manifest-listed research figures"

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
              <rect x="120" y="120" width="360" height="180" rx="6" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="2"/>
              <text id="smoke-card-label" x="148" y="206" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#111827" data-box-x="148" data-box-y="148" data-box-width="304" data-box-height="124" data-shape-x="120" data-shape-y="120" data-shape-width="360" data-shape-height="180">Smoke Export</text>
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
        docx_files = sorted((project / "exports").glob("*speaker_notes.docx"))
        if not docx_files:
            raise AssertionError("speaker notes DOCX was not exported")
        with zipfile.ZipFile(docx_files[-1], "r") as zf:
            if "word/document.xml" not in set(zf.namelist()):
                raise AssertionError("speaker notes DOCX missing word/document.xml")
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

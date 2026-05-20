#!/usr/bin/env python3
"""Export speaker notes to a standalone DOCX.

The PPTX exporter intentionally avoids embedding notes by default because some
PowerPoint COM/open flows fail on notes-heavy packages. This script keeps the
same slide-to-notes mapping internally but writes a continuous speech manuscript:
slide headings are structural only and are not printed by default. Each emitted
spoken paragraph is prefixed with its slide number so the manuscript stays
compact while remaining easy to locate against the deck.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

try:
    from total_md_split import parse_total_md
except ImportError:  # pragma: no cover - direct package import fallback
    parse_total_md = None  # type: ignore


def _find_svg_files(project_path: Path) -> list[Path]:
    svg_dir = project_path / "svg_output"
    if not svg_dir.is_dir():
        return []
    return sorted(svg_dir.glob("*.svg"))


def _read_notes(project_path: Path, svg_files: list[Path]) -> dict[str, str]:
    notes_dir = project_path / "notes"
    notes: dict[str, str] = {}
    svg_stems = [p.stem for p in svg_files]
    total_md = notes_dir / "total.md"
    if total_md.is_file() and parse_total_md is not None:
        parsed = parse_total_md(total_md, svg_stems, verbose=False)
        notes.update({k: v.strip() for k, v in parsed.items() if v.strip()})

    for svg in svg_files:
        md_path = notes_dir / f"{svg.stem}.md"
        if md_path.is_file():
            text = md_path.read_text(encoding="utf-8-sig").strip()
            if text:
                notes[svg.stem] = text

    return notes


def _plain_note_lines(md_text: str) -> list[str]:
    lines: list[str] = []
    for raw in md_text.splitlines():
        line = raw.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if line.startswith("#"):
            continue
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        line = re.sub(r"^\s*\d+[.)]\s+", "", line)
        line = line.replace("**", "").replace("__", "").replace("`", "")
        lines.append(line)
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _p(text: str = "", *, style: str | None = None) -> str:
    style_xml = f'<w:pStyle w:val="{style}"/>' if style else ""
    return (
        "<w:p>"
        f"<w:pPr>{style_xml}</w:pPr>"
        "<w:r><w:t xml:space=\"preserve\">"
        f"{escape(text)}"
        "</w:t></w:r>"
        "</w:p>"
    )


def _document_xml(svg_files: list[Path], notes: dict[str, str], *, include_slide_headings: bool = False) -> str:
    body: list[str] = []
    emitted_blocks = 0
    for idx, svg in enumerate(svg_files, 1):
        lines = _plain_note_lines(notes.get(svg.stem, ""))
        if not lines:
            continue
        if emitted_blocks:
            body.append(_p(""))
        if include_slide_headings:
            body.append(_p(f"第 {idx} 页：{svg.stem}", style="Heading1"))
        for line in lines:
            if line:
                prefix = "" if include_slide_headings else f"第 {idx} 页："
                body.append(_p(f"{prefix}{line}"))
            else:
                body.append(_p(""))
        emitted_blocks += 1
    if not body:
        body.append(_p("暂无讲稿内容。"))

    sect = (
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{"".join(body)}{sect}</w:body>'
        '</w:document>'
    )


def _styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei"/>'
        '<w:sz w:val="24"/></w:rPr>'
        '</w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1">'
        '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>'
        '<w:next w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>'
        '<w:rPr><w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei"/>'
        '<w:b/><w:sz w:val="32"/></w:rPr>'
        '</w:style>'
        '</w:styles>'
    )


def write_notes_docx(
    project_path: Path,
    output_path: Path | None = None,
    *,
    include_slide_headings: bool = False,
) -> Path:
    svg_files = _find_svg_files(project_path)
    if not svg_files:
        raise FileNotFoundError(f"No SVG files found under {project_path / 'svg_output'}")
    notes = _read_notes(project_path, svg_files)
    if output_path is None:
        exports = project_path / "exports"
        exports.mkdir(parents=True, exist_ok=True)
        output_path = exports / f"{project_path.name}_speaker_notes.docx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        '</Relationships>'
    )
    doc_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
        '</Relationships>'
    )

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("word/_rels/document.xml.rels", doc_rels)
        zf.writestr("word/styles.xml", _styles_xml())
        zf.writestr(
            "word/document.xml",
            _document_xml(svg_files, notes, include_slide_headings=include_slide_headings),
        )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export slide speaker notes to DOCX.")
    parser.add_argument("project_path", help="Project directory path")
    parser.add_argument("-o", "--output", help="Output DOCX path")
    parser.add_argument(
        "--include-slide-headings",
        action="store_true",
        help=(
            "Include slide number/file headings. Default is a continuous manuscript "
            "whose paragraphs are prefixed with slide page numbers."
        ),
    )
    args = parser.parse_args()

    project = Path(args.project_path).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else None
    try:
        docx = write_notes_docx(project, output, include_slide_headings=args.include_slide_headings)
    except Exception as exc:  # noqa: BLE001 - CLI needs concise failure text
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"OK: speaker notes DOCX exported: {docx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""PPTX package openability checks and Windows permission normalization."""

from __future__ import annotations

import os
import posixpath
import stat
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


PKG_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
CT_NS = "{http://schemas.openxmlformats.org/package/2006/content-types}"
NOTES_MASTER_CT = "application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"
NOTES_SLIDE_CT = "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"
NOTES_MASTER_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster"
NOTES_SLIDE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
MAX_NATIVE_CUSTGEOM = 60
MAX_TRANSITIONS = 0


@dataclass
class PptxOpenabilityReport:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def normalize_output_permissions(path: Path) -> list[str]:
    """Make a just-exported PPTX readable by the current Windows user.

    The exporter creates a temp package and moves it into ``exports/``. On
    Windows, inherited ACLs can occasionally leave PowerPoint without read
    access for the interactive user. This function keeps the package path and
    converter intact while granting the current account read/write access.
    """
    warnings: list[str] = []
    path = Path(path)

    try:
        current_mode = path.stat().st_mode
        path.chmod(current_mode | stat.S_IREAD | stat.S_IWRITE)
    except OSError as exc:
        warnings.append(f"Unable to clear read-only flag: {exc}")

    if os.name != "nt":
        return warnings

    username = os.environ.get("USERNAME")
    userdomain = os.environ.get("USERDOMAIN") or os.environ.get("COMPUTERNAME")
    principals: list[str] = []
    if userdomain and username:
        principals.append(f"{userdomain}\\{username}")
    if username:
        principals.append(username)

    for principal in dict.fromkeys(principals):
        try:
            subprocess.run(
                ["icacls", str(path), "/grant", f"{principal}:M"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return warnings
        except (OSError, subprocess.CalledProcessError):
            continue

    if principals:
        warnings.append(
            "Unable to grant explicit Windows ACL read/write permission "
            f"for {', '.join(principals)} with icacls."
        )
    return warnings


def validate_pptx_openability(path: Path) -> PptxOpenabilityReport:
    """Check common causes of PPTX open/repair failures."""
    errors: list[str] = []
    warnings: list[str] = []
    path = Path(path)

    try:
        with path.open("rb") as fh:
            if not fh.read(1):
                errors.append("PPTX file is empty.")
    except OSError as exc:
        errors.append(f"PPTX file is not readable by the current user: {exc}")
        return PptxOpenabilityReport(errors, warnings)

    if path.suffix.lower() != ".pptx":
        warnings.append(f"Output extension is not .pptx: {path.name}")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            bad_member = zf.testzip()
            if bad_member:
                errors.append(f"Zip CRC/read test failed for package member: {bad_member}")

            names = set(zf.namelist())
            required = {
                "[Content_Types].xml",
                "_rels/.rels",
                "ppt/presentation.xml",
                "ppt/_rels/presentation.xml.rels",
            }
            for part in sorted(required):
                if part not in names:
                    errors.append(f"Missing required PPTX part: {part}")
                elif zf.getinfo(part).file_size == 0:
                    errors.append(f"Required PPTX part is empty: {part}")

            rel_errors = _validate_relationship_targets(zf, names)
            errors.extend(rel_errors)

            if "[Content_Types].xml" in names:
                errors.extend(_validate_no_pptx_notes_package(zf, names))

            if "ppt/presentation.xml" in names:
                errors.extend(_validate_native_drawingml_stability(zf, names))

    except zipfile.BadZipFile as exc:
        errors.append(f"Output is not a valid PPTX zip package: {exc}")
    except OSError as exc:
        errors.append(f"Unable to inspect PPTX package: {exc}")

    return PptxOpenabilityReport(errors, warnings)


def _read_xml_part(zf: zipfile.ZipFile, name: str) -> str:
    return zf.read(name).decode("utf-8", errors="replace")


def _validate_native_drawingml_stability(zf: zipfile.ZipFile, names: set[str]) -> list[str]:
    """Catch packages likely to open with missing content or repair prompts."""
    errors: list[str] = []
    slides = sorted(
        name for name in names
        if name.startswith("ppt/slides/slide") and name.endswith(".xml")
    )
    custgeom_total = 0
    transition_total = 0
    worst: list[tuple[int, str]] = []
    transition_slides: list[str] = []
    for slide_name in slides:
        xml = _read_xml_part(zf, slide_name)
        cust_count = xml.count("<a:custGeom")
        trans_count = xml.count("<p:transition")
        custgeom_total += cust_count
        transition_total += trans_count
        if cust_count:
            worst.append((cust_count, slide_name))
        if trans_count:
            transition_slides.append(slide_name)

    if custgeom_total > MAX_NATIVE_CUSTGEOM:
        worst.sort(reverse=True)
        sample = ", ".join(f"{name}:{count}" for count, name in worst[:5])
        errors.append(
            f"Native PPTX contains {custgeom_total} custom geometry shapes "
            f"(limit {MAX_NATIVE_CUSTGEOM}). This usually means svg_final/pathified "
            "SVG was exported to native DrawingML, or SVG connectors/arrows were "
            "left as <path>/<polygon>/<polyline> custom geometry. Regenerate from "
            "svg_output and keep connectors as native <line> / simple polyline "
            f"segments where possible. Worst slides: {sample}."
        )

    if transition_total > MAX_TRANSITIONS:
        sample = ", ".join(transition_slides[:10])
        errors.append(
            f"Native PPTX contains {transition_total} slide transition element(s). "
            "Transitions are disabled by default because some repaired/open-failure "
            "cases involved transition markup plus heavy custom geometry. Use -t none "
            f"for regeneration unless the user explicitly requested transitions. Slides: {sample}."
        )

    return errors


def _source_part_for_rels(rels_name: str) -> PurePosixPath:
    rels_path = PurePosixPath(rels_name)
    if rels_path.name == ".rels":
        return PurePosixPath("")
    if rels_path.parent.name != "_rels":
        return PurePosixPath("")
    source_dir = rels_path.parent.parent
    source_name = rels_path.name[:-5] if rels_path.name.endswith(".rels") else rels_path.name
    return source_dir / source_name


def _resolve_relationship_target(rels_name: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    source_part = _source_part_for_rels(rels_name)
    base = source_part.parent if str(source_part) not in ("", ".") else PurePosixPath("")
    return posixpath.normpath(str(base / target)).lstrip("/")


def _validate_relationship_targets(zf: zipfile.ZipFile, names: set[str]) -> list[str]:
    errors: list[str] = []
    for rels_name in sorted(name for name in names if name.endswith(".rels")):
        try:
            root = ET.fromstring(zf.read(rels_name))
        except ET.ParseError as exc:
            errors.append(f"Invalid relationship XML: {rels_name}: {exc}")
            continue
        for rel in root.findall(f"{PKG_REL_NS}Relationship"):
            if rel.attrib.get("TargetMode") == "External":
                continue
            target = rel.attrib.get("Target", "")
            if not target:
                errors.append(f"{rels_name}: relationship {rel.attrib.get('Id', '')} has empty Target.")
                continue
            if target.startswith("#"):
                continue
            resolved = _resolve_relationship_target(rels_name, target)
            if resolved not in names:
                errors.append(
                    f"Broken relationship target: {rels_name} -> {target} "
                    f"(resolved {resolved}) is missing from the package."
                )
    return errors


def _validate_no_pptx_notes_package(zf: zipfile.ZipFile, names: set[str]) -> list[str]:
    """Generated decks must not carry PPTX notes parts.

    Notes are exported to DOCX. PPTX notesSlides/notesMasters have caused
    repair prompts and PowerPoint COM/RPC failures in otherwise valid decks.
    """
    errors: list[str] = []
    note_parts = sorted(
        name for name in names
        if name.startswith("ppt/notesSlides/") or name.startswith("ppt/notesMasters/")
    )
    if note_parts:
        sample = ", ".join(note_parts[:6])
        errors.append(
            "PPTX package must be notes-free; found notes part(s): "
            f"{sample}. Export speaker notes as standalone DOCX instead."
        )

    try:
        root = ET.fromstring(zf.read("[Content_Types].xml"))
    except ET.ParseError as exc:
        return errors + [f"Invalid [Content_Types].xml: {exc}"]

    for elem in root.findall(f"{CT_NS}Override"):
        content_type = elem.attrib.get("ContentType", "")
        if content_type in {NOTES_MASTER_CT, NOTES_SLIDE_CT}:
            errors.append(
                "PPTX package must not declare notes content types; remove "
                f"content type override for {elem.attrib.get('PartName', '')}."
            )

    for rels_name in sorted(name for name in names if name.endswith(".rels")):
        try:
            rels_root = ET.fromstring(zf.read(rels_name))
        except ET.ParseError:
            continue
        for rel in rels_root.findall(f"{PKG_REL_NS}Relationship"):
            if rel.attrib.get("Type") in {NOTES_MASTER_REL, NOTES_SLIDE_REL}:
                errors.append(
                    f"PPTX package must not include notes relationships: {rels_name} "
                    f"{rel.attrib.get('Id', '')} -> {rel.attrib.get('Target', '')}."
                )

    if "ppt/presentation.xml" in names:
        pres_xml = zf.read("ppt/presentation.xml").decode("utf-8", errors="replace")
        if "<p:notesMasterIdLst" in pres_xml or "<p:notesMasterId" in pres_xml:
            errors.append(
                "presentation.xml still contains notesMasterId markup; "
                "strip PPTX notes master metadata before export."
            )
        if "<p:notesSz" not in pres_xml:
            errors.append(
                "presentation.xml is missing <p:notesSz>. This root presentation "
                "size metadata is required by PowerPoint even when notesSlides and "
                "notesMasters are stripped."
            )

    return errors

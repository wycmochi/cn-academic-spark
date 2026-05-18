#!/usr/bin/env python3
"""Check a generated PPTX for common PowerPoint open/repair failures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from svg_to_pptx.pptx_openability import (  # noqa: E402
    normalize_output_permissions,
    validate_pptx_openability,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate PPTX package relationships, notes master parts, content types, and file readability."
    )
    parser.add_argument("pptx", help="Generated .pptx path")
    parser.add_argument(
        "--fix-permissions",
        action="store_true",
        help="Best-effort grant read/write access to the current Windows user before validating.",
    )
    args = parser.parse_args()

    pptx_path = Path(args.pptx).expanduser().resolve()
    if args.fix_permissions and pptx_path.exists():
        for warning in normalize_output_permissions(pptx_path):
            print(f"[warn] {warning}")

    report = validate_pptx_openability(pptx_path)
    for warning in report.warnings:
        print(f"[warn] {warning}")
    for error in report.errors:
        print(f"[error] {error}")
    if report.ok:
        print(f"OK: PPTX openability checks passed: {pptx_path}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

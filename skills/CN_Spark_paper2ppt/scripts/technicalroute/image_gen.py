#!/usr/bin/env python3
"""Compatibility wrapper for the skill-level image generator.

The TechnicalRoute pipeline must use scripts/image_gen.py because it supports
--reference / --refs and passes reference_images to capable backends. Keep this
file only so old IMAGE_GEN_PATH values continue to work without dropping gallery
references.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT_IMAGE_GEN = Path(__file__).resolve().parents[1] / "image_gen.py"

if __name__ == "__main__":
    if not ROOT_IMAGE_GEN.is_file():
        raise SystemExit(f"Root image_gen.py not found: {ROOT_IMAGE_GEN}")
    root_scripts = str(ROOT_IMAGE_GEN.parent)
    if root_scripts not in sys.path:
        sys.path.insert(0, root_scripts)
    sys.argv[0] = str(ROOT_IMAGE_GEN)
    runpy.run_path(str(ROOT_IMAGE_GEN), run_name="__main__")

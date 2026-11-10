#!/usr/bin/env python3
"""Inventory the global connector configs and shared operation wrappers of a Mule project and report duplicated operations and configs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _reuse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="path to a Mule project directory")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    parser.add_argument("--only", default="", help="comma-separated Mule file names; report only findings that involve them")
    parser.add_argument("--strict", action="store_true", help="exit 1 when a reportable finding exists")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    if not (project / "src" / "main" / "mule").is_dir():
        print(f"{project}: no src/main/mule directory", file=sys.stderr)
        return 2
    only = {name.strip() for name in args.only.split(",") if name.strip()} or None
    result = _reuse.scan(project)
    reportable = [f for f in result["findings"] if not f.get("info") and (only is None or only & set(f["files"]))]
    if args.json:
        result["findings"] = [f for f in result["findings"] if only is None or only & set(f["files"])]
        print(json.dumps(result, indent=1, default=list))
    else:
        print(_reuse.format_text(result, only))
    return 1 if args.strict and reportable else 0


if __name__ == "__main__":
    raise SystemExit(main())

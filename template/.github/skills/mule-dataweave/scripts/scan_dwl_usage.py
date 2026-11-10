#!/usr/bin/env python3
"""Find common DataWeave review targets in a Mule project."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


INLINE_VALUE_RE = re.compile(r'<(set-variable|set-payload)\b[^>]*\bvalue="(#\[[^"]+\])"', re.S)
RESOURCE_RE = re.compile(r'resource="dwl/([^"]+\.dwl)"')
TRIVIAL_RE = re.compile(r"^#\[(?:payload|vars\.[A-Za-z0-9_.-]+|attributes\.[A-Za-z0-9_.-]+|correlationId|true|false|null|\d+|'[^']*'|\"[^\"]*\")\]$")
DEEP_ACCESS_RE = re.compile(r"\b(?:payload|vars)\.[A-Za-z0-9_]+\.[A-Za-z0-9_.]+")
TODO_RE = re.compile(r"\b(?:TODO|FIXME|TBD|placeholder)\b", re.I)


def line_no(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    args = parser.parse_args()
    project = Path(args.project).resolve()

    xml_dir = project / "src/main/mule"
    dwl_dir = project / "src/main/resources/dwl"
    inline_findings: list[str] = []
    refs: set[str] = set()

    for path in sorted(xml_dir.glob("*.xml")) if xml_dir.exists() else []:
        text = path.read_text(errors="ignore")
        refs.update(RESOURCE_RE.findall(text))
        for match in INLINE_VALUE_RE.finditer(text):
            value = match.group(2).replace("\n", " ")
            if "%dw" in value or not TRIVIAL_RE.match(value):
                inline_findings.append(f"{path.relative_to(project)}:{line_no(text, match.start())}: {match.group(1)} value={value[:120]}")

    dwl_files = {path.name: path for path in sorted(dwl_dir.glob("*.dwl"))} if dwl_dir.exists() else {}
    missing_refs = sorted(ref for ref in refs if ref not in dwl_files)
    unused = sorted(name for name in dwl_files if name not in refs)

    deep_access: list[str] = []
    todos: list[str] = []
    for path in dwl_files.values():
        text = path.read_text(errors="ignore")
        for match in DEEP_ACCESS_RE.finditer(text):
            deep_access.append(f"{path.relative_to(project)}:{line_no(text, match.start())}: {match.group(0)}")
        for match in TODO_RE.finditer(text):
            todos.append(f"{path.relative_to(project)}:{line_no(text, match.start())}: {match.group(0)}")

    print(f"Project: {project.name}")
    print(f"DWL files: {len(dwl_files)}")
    print(f"XML DWL refs: {len(refs)}")
    print(f"Complex inline set-variable/set-payload: {len(inline_findings)}")
    for item in inline_findings[:30]:
        print(f"- {item}")
    if len(inline_findings) > 30:
        print(f"- ... {len(inline_findings) - 30} more")
    print(f"Missing DWL refs: {len(missing_refs)}")
    for ref in missing_refs[:30]:
        print(f"- {ref}")
    print(f"Potentially unused DWL files: {len(unused)}")
    for ref in unused[:30]:
        print(f"- {ref}")
    print(f"Direct deep payload/vars access occurrences: {len(deep_access)}")
    for item in deep_access[:30]:
        print(f"- {item}")
    print(f"TODO/FIXME/TBD markers in DWL: {len(todos)}")
    for item in todos[:30]:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

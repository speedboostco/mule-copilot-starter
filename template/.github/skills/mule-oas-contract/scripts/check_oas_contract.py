#!/usr/bin/env python3
"""Check EAPI OAS/APIkit wiring without network access."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


TAG_RE = re.compile(r"<(?P<tag>[\w.-]+)>(?P<value>[^<]+)</(?P=tag)>")
ATTR_RE = re.compile(r"([\w:-]+)=(?:\"([^\"]*)\"|'([^']*)')")


def tag_value(text: str, tag: str) -> str | None:
    match = re.search(rf"<{re.escape(tag)}>([^<]+)</{re.escape(tag)}>", text)
    return match.group(1).strip() if match else None


def dependency_blocks(text: str) -> list[dict[str, str]]:
    blocks = re.findall(r"<dependency>(.*?)</dependency>", text, flags=re.S)
    deps: list[dict[str, str]] = []
    for block in blocks:
        values = {m.group("tag"): m.group("value").strip() for m in TAG_RE.finditer(block)}
        if values:
            deps.append(values)
    return deps


def flow_names(project: Path) -> set[str]:
    names: set[str] = set()
    mule_dir = project / "src/main/mule"
    for path in mule_dir.glob("*.xml") if mule_dir.exists() else []:
        text = path.read_text(errors="ignore")
        for match in re.finditer(r"<(?:flow|sub-flow)\s+[^>]*\bname=(?:\"([^\"]*)\"|'([^']*)')", text):
            names.add(match.group(1) or match.group(2))
    return names


def flow_mappings(project: Path) -> list[tuple[Path, dict[str, str]]]:
    mappings: list[tuple[Path, dict[str, str]]] = []
    mule_dir = project / "src/main/mule"
    for path in mule_dir.glob("*.xml") if mule_dir.exists() else []:
        text = path.read_text(errors="ignore")
        for match in re.finditer(r"<apikit:flow-mapping\b[^>]*/?>", text):
            attrs = {key: value1 or value2 for key, value1, value2 in ATTR_RE.findall(match.group(0))}
            mappings.append((path, attrs))
    return mappings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    pom = project / "pom.xml"
    if not pom.exists():
        print(f"No pom.xml found under {project}")
        return 1

    pom_text = pom.read_text(errors="ignore")
    artifact_id = tag_value(pom_text, "artifactId") or project.name
    spec_name = tag_value(pom_text, "spec.name")
    spec_version = tag_value(pom_text, "spec.version")
    oas_deps = [
        dep for dep in dependency_blocks(pom_text)
        if dep.get("classifier") == "oas" or (dep.get("type") == "zip" and "oas" in dep.get("artifactId", ""))
    ]

    flows = flow_names(project)
    mappings = flow_mappings(project)
    missing = []
    health_without_flow = []
    for path, attrs in mappings:
        if attrs.get("flow-ref") in flows:
            continue
        item = (path.relative_to(project), attrs)
        if attrs.get("resource") == "/health":
            health_without_flow.append(item)
        else:
            missing.append(item)

    print(f"Project: {project.name}")
    print(f"artifactId: {artifact_id}")
    print(f"spec.name: {spec_name or 'not found'}")
    print(f"spec.version: {spec_version or 'not found'}")
    print(f"OAS dependencies: {len(oas_deps)}")
    for dep in oas_deps:
        print(f"- {dep.get('artifactId')}:{dep.get('version')} classifier={dep.get('classifier')} type={dep.get('type')}")
    print(f"APIkit flow mappings: {len(mappings)}")
    print(f"Flow/sub-flow names: {len(flows)}")
    if missing:
        print("\nMissing flow-ref targets:")
        for rel, attrs in missing:
            print(f"- {rel}: {attrs.get('action')} {attrs.get('resource')} -> {attrs.get('flow-ref')}")
    else:
        print("\nMissing flow-ref targets: none detected")
    if health_without_flow:
        print("\nHealth mappings without flow target:")
        for rel, attrs in health_without_flow:
            print(f"- {rel}: {attrs.get('action')} {attrs.get('resource')} -> {attrs.get('flow-ref')} (often OK if main.xml handles /health before APIkit)")

    api_dir = project / "src/main/resources/api"
    api_files = sorted(api_dir.glob("*.yaml")) if api_dir.exists() else []
    if api_files:
        print("\nLocal API YAML files:")
        for path in api_files:
            print(f"- {path.relative_to(project)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

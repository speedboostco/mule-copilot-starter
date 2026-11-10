#!/usr/bin/env python3
"""Summarize Mule config coverage for one project."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PLACEHOLDER_RE = re.compile(r'!\[\]|!\[TBD\]|\bTBD\b|\btbd\b')
KEY_RE = re.compile(r'^([A-Za-z0-9_.-]+)\s*:')


def config_files(project: Path) -> list[Path]:
    roots = [
        project / "src/main/resources/config",
        project / "src/main/resources",
        project / "src/test/resources/config",
        project / "src/test/resources",
    ]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(sorted(root.glob("config-*.yaml")))
            if (root / "config-common.yaml").exists():
                files.append(root / "config-common.yaml")
    return sorted(set(files))


def env_name(path: Path) -> str:
    name = path.name
    if name == "config-common.yaml":
        return "common"
    if name == "config-test.yaml":
        return "test"
    return name.removeprefix("config-").removesuffix(".yaml")


def flattened_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    stack: list[tuple[int, str]] = []
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or line.lstrip().startswith("-"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        match = KEY_RE.match(stripped)
        if not match:
            continue
        key = match.group(1).strip("'\"")
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path_key = ".".join([item[1] for item in stack] + [key])
        keys.add(path_key)
        stack.append((indent, key))
    return keys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    files = config_files(project)
    data = {}
    for path in files:
        rel = str(path.relative_to(project))
        text = path.read_text(errors="ignore")
        keys = sorted(flattened_keys(path))
        data[rel] = {
            "env": env_name(path),
            "key_count": len(keys),
            "top_level": sorted({key.split(".", 1)[0] for key in keys}),
            "placeholder_count": len(PLACEHOLDER_RE.findall(text)),
        }

    env_entries = {rel: meta for rel, meta in data.items() if meta["env"] not in {"common", "local", "test"}}
    env_key_sets = {rel: flattened_keys(project / rel) for rel in env_entries}
    env_union = set().union(*env_key_sets.values()) if env_key_sets else set()
    missing_by_env = {
        rel: sorted(env_union - keys)
        for rel, keys in env_key_sets.items()
        if env_union - keys
    }

    result = {
        "project": str(project),
        "config_file_count": len(files),
        "files": data,
        "env_files": sorted(env_entries),
        "missing_env_keys": missing_by_env,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Project: {project.name}")
    print(f"Config files: {len(files)}")
    for rel, meta in data.items():
        placeholder = f", placeholders={meta['placeholder_count']}" if meta["placeholder_count"] else ""
        print(f"- {rel}: env={meta['env']}, keys={meta['key_count']}{placeholder}")
    if missing_by_env:
        print("\nMissing keys across env files:")
        for rel, keys in missing_by_env.items():
            preview = ", ".join(keys[:12])
            suffix = f" (+{len(keys) - 12} more)" if len(keys) > 12 else ""
            print(f"- {rel}: {preview}{suffix}")
    else:
        print("\nMissing keys across env files: none detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

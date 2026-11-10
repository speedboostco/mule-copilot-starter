#!/usr/bin/env python3
"""
Lightweight DWL mutation testing for Mule projects.

There is no off-the-shelf mutation-testing tool for DataWeave, and most
projects in this workspace carry ~1 boilerplate Java file (see
`find src/main/java -name '*.java'`), so a classic bytecode mutation tool
(PIT) has almost nothing to mutate. This script applies small, well-known
mutation operators directly to a .dwl file, re-runs the MUnit suite that
exercises it, and reports whether the suite caught the change (killed) or
not (survived == untested logic).

Usage:
  python3 mutate_dwl.py <project-dir> <relative/path/to/file.dwl> \
      --munit-test <suite.xml>[#<test-name>]

Exit code is always 0; read the report for kill/survive counts.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MUTATION_OPERATORS = [
    ("relational: == -> !=", re.compile(r"=="), "!="),
    ("relational: != -> ==", re.compile(r"!="), "=="),
    ("relational: > -> <", re.compile(r"(?<![<>=!])>(?!=)"), "<"),
    ("relational: < -> >", re.compile(r"(?<![<>=!])<(?!=)"), ">"),
    ("relational: >= -> <=", re.compile(r">="), "<="),
    ("relational: <= -> >=", re.compile(r"<="), ">="),
    ("boolean: true -> false", re.compile(r"\btrue\b"), "false"),
    ("boolean: false -> true", re.compile(r"\bfalse\b"), "true"),
    ("boolean: and -> or", re.compile(r"\band\b"), "or"),
    ("boolean: or -> and", re.compile(r"\bor\b"), "and"),
    ("null-safety: default removed", re.compile(r"\bdefault\b[^,\n]*"), ""),
    ("optional access: ?. -> .", re.compile(r"\?\."), "."),
]


def find_mvn_cmd(project_dir: Path, munit_test: str) -> list:
    return [
        "mvn",
        "clean",
        "test",
        "-Dmule.env=test",
        f"-Dmule.key={os.environ.get('MULE_TEST_KEY', 'testtesttesttest')}",
        f"-Dmunit.test={munit_test}",
        "-q",
    ]


def run_suite(project_dir: Path, munit_test: str) -> bool:
    """Returns True if the MUnit suite passed (mutant survived)."""
    result = subprocess.run(
        find_mvn_cmd(project_dir, munit_test),
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("dwl_path", help="Path relative to the project root, e.g. src/main/resources/dwl/set-x-request.dwl")
    parser.add_argument("--munit-test", required=True, help="Suite or suite#test that exercises this DWL file")
    parser.add_argument("--max-mutants", type=int, default=20)
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    dwl_file = project_dir / args.dwl_path
    if not dwl_file.is_file():
        print(f"ERROR: {dwl_file} not found")
        sys.exit(1)

    original = dwl_file.read_text()
    backup = dwl_file.with_suffix(dwl_file.suffix + ".mutation-backup")
    shutil.copy(dwl_file, backup)

    print(f"Baseline: confirming the suite passes on unmutated code")
    baseline_ok = run_suite(project_dir, args.munit_test)
    if not baseline_ok:
        print("ERROR: baseline MUnit run fails before any mutation was applied. Fix the suite first.")
        dwl_file.write_text(original)
        backup.unlink(missing_ok=True)
        sys.exit(1)

    killed, survived, skipped = 0, 0, 0
    mutant_id = 0

    try:
        for label, pattern, replacement in MUTATION_OPERATORS:
            if mutant_id >= args.max_mutants:
                break
            matches = list(pattern.finditer(original))
            if not matches:
                continue
            for m in matches:
                if mutant_id >= args.max_mutants:
                    break
                mutant_id += 1
                mutated = original[: m.start()] + replacement + original[m.end() :]
                dwl_file.write_text(mutated)
                try:
                    survived_flag = run_suite(project_dir, args.munit_test)
                except subprocess.TimeoutExpired:
                    print(f"[{mutant_id}] {label} @ offset {m.start()} -> TIMEOUT (skipped)")
                    skipped += 1
                    continue
                finally:
                    dwl_file.write_text(original)
                if survived_flag:
                    survived += 1
                    print(f"[{mutant_id}] {label} @ offset {m.start()} -> SURVIVED (suite did not notice)")
                else:
                    killed += 1
                    print(f"[{mutant_id}] {label} @ offset {m.start()} -> KILLED (suite caught it)")
    finally:
        dwl_file.write_text(original)
        backup.unlink(missing_ok=True)

    total = killed + survived
    score = (killed / total * 100) if total else 0.0
    print()
    print(f"Mutants generated: {mutant_id} (skipped/timeout: {skipped})")
    print(f"Killed: {killed}  Survived: {survived}")
    print(f"Mutation score for {args.dwl_path}: {score:.1f}%")
    if survived:
        print("Surviving mutants indicate assertions that do not actually check the mutated logic branch.")


if __name__ == "__main__":
    main()

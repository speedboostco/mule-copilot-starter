#!/usr/bin/env python3
"""Measure the human-written style of a Mule workspace.

Walks every Mule project under ROOT, measures layout/naming/text conventions of
Mule XML, DataWeave, property YAML, MUnit, OAS, Markdown docs and git history,
and picks exemplar files that best match the dominant style.

Only files last changed before --before (default: .github/mule-starter/installed-at)
are measured, so code written by agents after install does not teach the style.

Stdlib only. Read-only. Prints a compact Markdown summary; --out writes full JSON.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {
    "target", "node_modules", ".git", ".mule", ".terraform", ".tooling-project", "bin", ".idea",
    ".vscode", ".settings", ".github", ".claude", ".agents", ".copilot", ".mvn", ".apivcs",
    "exchange_modules", ".exchange_modules_tmp", "archive", "backup", "logs", "tmp", "temp",
    "__pycache__", "dist", "build", "out",
}
MAX_SAMPLES = 12
CYRILLIC = re.compile(r"[А-Яа-яЁё]")
LATIN = re.compile(r"[A-Za-z]")


def share(counter: Counter) -> list[list]:
    total = sum(counter.values())
    if not total:
        return []
    return [[k, v, round(v / total, 2)] for k, v in counter.most_common(6)]


def dominant(counter: Counter):
    total = sum(counter.values())
    if not total:
        return None, 0.0
    key, val = counter.most_common(1)[0]
    return key, round(val / total, 2)


def ratio(a: int, b: int) -> float:
    return round(a / b, 2) if b else 0.0


def case_of(name: str) -> str:
    s = name.strip()
    if not s:
        return "empty"
    if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)+", s):
        return "kebab-case"
    if re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)+", s):
        return "snake_case"
    if re.fullmatch(r"[A-Z0-9]+(_[A-Z0-9]+)*", s) and len(s) > 1:
        return "UPPER_SNAKE"
    if re.fullmatch(r"[a-z][a-z0-9]*([A-Z][a-z0-9]*)+", s):
        return "camelCase"
    if re.fullmatch(r"[A-Z][a-z0-9]+([A-Z][a-z0-9]*)+", s):
        return "PascalCase"
    if re.fullmatch(r"[a-z0-9]+", s):
        return "lowercase"
    if re.fullmatch(r"[A-Z][a-z0-9]+", s):
        return "Capitalized"
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*", s)
    if " " in s and words:
        caps = [w[0].isupper() for w in words if len(w) > 2]
        if caps and all(caps):
            return "Title Case words"
        if words[0][0].isupper() and not any(caps[1:]):
            return "Sentence case words"
        if not words[0][0].isupper():
            return "lower case words"
        return "Mixed words"
    return "other"


def indent_profile(lines: list[str]) -> tuple[str, int]:
    tabs = spaces = 0
    widths = Counter()
    prev = None
    for line in lines:
        if not line.strip():
            continue
        lead = line[: len(line) - len(line.lstrip(" \t"))]
        if lead.startswith("\t"):
            tabs += 1
        elif lead:
            spaces += 1
        n = len(lead.replace("\t", "    "))
        if prev is not None and n > prev:
            widths[n - prev] += 1
        prev = n
    if not tabs and not spaces:
        return "none", 0
    kind = "tabs" if tabs > spaces else "spaces"
    width = widths.most_common(1)[0][0] if widths else 0
    return kind, width


def indent_label(kind: str, width: int) -> str:
    return f"spaces:{width}" if kind == "spaces" else kind


class GitIndex:
    """Per-repo knowledge of files touched after the cutoff (likely agent-written)."""

    def __init__(self, before: str | None):
        self.before = before
        self.repos: dict[Path, set[str]] = {}
        self.ok = self._has_git()

    @staticmethod
    def _has_git() -> bool:
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True, timeout=10)
            return True
        except Exception:
            return False

    def repo_of(self, path: Path) -> Path | None:
        for parent in [path] + list(path.parents):
            if (parent / ".git").exists():
                return parent
        return None

    def recent(self, repo: Path) -> set[str]:
        if repo in self.repos:
            return self.repos[repo]
        touched: set[str] = set()
        if self.ok and self.before:
            for args in (
                ["log", f"--since={self.before}", "--name-only", "--format="],
                ["diff", "--name-only"],
                ["diff", "--name-only", "--cached"],
                ["ls-files", "--others", "--exclude-standard"],
            ):
                out = git(repo, args)
                touched.update(line.strip() for line in out.splitlines() if line.strip())
        self.repos[repo] = touched
        return touched

    def eligible(self, path: Path, cutoff_ts: float | None) -> bool:
        if not self.before:
            return True
        repo = self.repo_of(path.parent)
        if repo is not None and self.ok:
            rel = path.relative_to(repo).as_posix()
            return rel not in self.recent(repo)
        return cutoff_ts is None or path.stat().st_mtime < cutoff_ts


def git(repo: Path, args: list[str]) -> str:
    try:
        res = subprocess.run(["git", "-C", str(repo)] + args, capture_output=True, text=True, timeout=30)
        return res.stdout
    except Exception:
        return ""


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        yield Path(dirpath), dirnames, filenames


def find_projects(root: Path):
    mule, terraform, archetypes = [], [], []
    for d, dirnames, files in walk(root):
        rel_depth = len(d.relative_to(root).parts)
        if "archetype-resources" in d.parts:
            dirnames[:] = []
            continue
        if (d / "src/main/resources/archetype-resources").exists():
            archetypes.append(d)
            dirnames[:] = []
            continue
        if "pom.xml" in files and (d / "src/main/mule").is_dir():
            mule.append(d)
            dirnames[:] = []
            continue
        if any(f.endswith(".tf") for f in files) and rel_depth <= 2:
            terraform.append(d)
        if rel_depth >= 3:
            dirnames[:] = []
    return sorted(mule), sorted(set(terraform)), sorted(archetypes)


def layer_of(name: str) -> str:
    m = re.search(r"(?:^|[-_])(e|p|s|exp|prc|sys|experience|process|system)[-_]?api$", name, re.I)
    if not m:
        return "other"
    key = m.group(1).lower()[0]
    return {"e": "experience", "p": "process", "s": "system"}[key]


def pom_facts(pom: Path) -> dict:
    t = pom.read_text(errors="ignore")
    parent = re.search(r"<parent>.*?<artifactId>([^<]+)</artifactId>.*?<version>([^<]+)</version>.*?</parent>", t, re.S)
    own = re.sub(r"<(parent|dependencies|dependencyManagement|build|profiles|repositories|pluginRepositories|distributionManagement|reporting)>.*?</\1>", "", t, flags=re.S)
    group = re.search(r"<groupId>([^<]+)</groupId>", own)
    parent_group = re.search(r"<parent>.*?<groupId>([^<]+)</groupId>", t, re.S)
    spec = re.search(r"<spec\.name>([^<]+)</spec\.name>", t)
    props = dict(re.findall(r"<(app\.runtime|mule\.version|munit\.version|mule\.maven\.plugin\.version)>([^<]+)</", t))
    return {
        "parent": f"{parent.group(1)}:{parent.group(2)}" if parent else None,
        "groupId": group.group(1) if group else (f"inherited:{parent_group.group(1)}" if parent_group else None),
        "spec": bool(spec),
        "props": props,
    }


class Stats:
    def __init__(self):
        self.c = defaultdict(Counter)
        self.n = Counter()
        self.samples = defaultdict(list)
        self.files = defaultdict(list)

    def add_sample(self, key: str, value: str):
        lst = self.samples[key]
        if value not in lst and len(lst) < MAX_SAMPLES:
            lst.append(value)


START_TAG = re.compile(r"<([A-Za-z][\w:.-]*)((?:\s+[\w:.-]+\s*=\s*(?:\"[^\"]*\"|'[^']*'))+)\s*(/?)>", re.S)
ATTR = re.compile(r"[\w:.-]+\s*=\s*(\"[^\"]*\"|'[^']*')")


def measure_xml(path: Path, st: Stats, project_layer: str) -> dict:
    t = path.read_text(errors="ignore")
    lines = t.splitlines()
    st.n["xml_files"] += 1
    st.n["xml_lines"] += len(lines)
    kind, width = indent_profile(lines)
    st.c["xml_indent"][indent_label(kind, width)] += 1
    multi = single = 0
    for m in START_TAG.finditer(t):
        attrs = ATTR.findall(m.group(2))
        if len(attrs) >= 2:
            if "\n" in m.group(2):
                multi += 1
            else:
                single += 1
    layout = "one-attribute-per-line" if multi > single else "attributes-on-one-line"
    if multi + single:
        st.c["xml_attr_layout"][layout] += 1
    st.n["xml_selfclose_tight"] += len(re.findall(r"[\"']/>", t))
    st.n["xml_selfclose_space"] += len(re.findall(r"[\"'] />", t))
    st.n["xml_attr_dq"] += len(re.findall(r"=\"", t))
    st.n["xml_attr_sq"] += len(re.findall(r"='", t))
    st.n["xml_blank_lines"] += sum(1 for l in lines if not l.strip())
    comments = len(re.findall(r"<!--", t))
    st.n["xml_comments"] += comments
    st.n["xml_files_with_comments"] += 1 if comments else 0
    st.c["xml_decl"]["present" if t.lstrip().startswith("<?xml") else "absent"] += 1
    st.c["xml_final_newline"]["yes" if t.endswith("\n") else "no"] += 1
    doc_names = re.findall(r"doc:name=\"([^\"]*)\"", t)
    st.n["xml_doc_name"] += len(doc_names)
    st.n["xml_doc_id"] += len(re.findall(r"doc:id=\"", t))
    for dn in doc_names:
        c = case_of(dn)
        st.c["doc_name_case"][c] += 1
        st.add_sample(f"doc_name:{c}", dn)
    for name in re.findall(r"<(?:sub-)?flow\s[^>]*?name=\"([^\"]+)\"", t, re.S):
        if "\\" in name or re.match(r"^(get|post|put|patch|delete|options|head):", name, re.I) and "\\" in name:
            st.c["flow_name_style"]["apikit-generated"] += 1
            continue
        style = "module:operation" if ":" in name else case_of(name)
        st.c["flow_name_style"][style] += 1
        st.add_sample(f"flow_name:{style}", name)
    st.c["xml_file_name"][case_of(path.stem)] += 1
    st.n["ee_resource"] += len(re.findall(r"<ee:set-(?:payload|variable)[^>]*\sresource=", t))
    st.n["ee_inline"] += len(re.findall(r"<ee:set-(?:payload|variable)[^>]*>\s*<!\[CDATA\[", t))
    st.n["setvar_inline_dw"] += len(re.findall(r"<set-(?:variable|payload)[^>]*value=\"#\[[^\"]*(?:\{|map|filter|\+\+)", t))
    for lg in re.finditer(r"<logger\b([^>]*)>", t, re.S):
        attrs = lg.group(1)
        lvl = re.search(r"level=\"([A-Z]+)\"", attrs)
        st.c["logger_level"][lvl.group(1) if lvl else "default"] += 1
        st.c["logger_category"]["set" if "category=" in attrs else "unset"] += 1
        msg = re.search(r"message=\"([^\"]*)\"", attrs)
        if msg:
            norm = re.sub(r"'[^']*'", "'…'", msg.group(1))
            norm = re.sub(r"\s+", " ", norm)[:90]
            st.c["logger_message_shape"][norm] += 1
    reqs = re.findall(r"<http:request\b[^>]*>", t, re.S)
    st.n["http_request"] += len(reqs)
    st.n["http_request_corr"] += sum(1 for r in reqs if "sendCorrelationId" in r)
    st.n["try"] += len(re.findall(r"<try\b", t))
    st.n["on_error_propagate"] += len(re.findall(r"<on-error-propagate\b", t))
    st.n["on_error_continue"] += len(re.findall(r"<on-error-continue\b", t))
    for typ in re.findall(r"<raise-error[^>]*type=\"([^\"]+)\"", t):
        st.c["raise_error_ns"][typ.split(":")[0]] += 1
    st.c["until_successful_by_layer"][project_layer] += len(re.findall(r"<until-successful\b", t))
    return {"indent": indent_label(kind, width), "layout": layout, "lines": len(lines),
            "comments": comments}


def measure_dwl(path: Path, st: Stats, proj: Path) -> dict:
    t = path.read_text(errors="ignore")
    lines = t.splitlines()
    st.n["dwl_files"] += 1
    st.n["dwl_lines"] += len(lines)
    rel = path.relative_to(proj / "src/main/resources").parts
    st.c["dwl_folder"]["src/main/resources/" + rel[0] if len(rel) > 1 else "src/main/resources"] += 1
    st.c["dwl_subfolders"]["yes" if len(rel) > 2 else "no"] += 1
    first = next((l.strip() for l in lines if l.strip()), "")
    st.c["dwl_header"]["%dw 2.0" if first.startswith("%dw 2.0") else ("no header (expression only)" if first else "empty")] += 1
    out = re.search(r"^\s*output\s+([\w/+.-]+)(.*)$", t, re.M)
    st.c["dwl_output"][out.group(1) if out else "none"] += 1
    if out and out.group(2).strip():
        st.c["dwl_output_options"][out.group(2).strip()[:60]] += 1
    for imp in re.findall(r"^\s*import\s+(.+)$", t, re.M):
        st.c["dwl_imports"][imp.strip()[:70]] += 1
    kind, width = indent_profile(lines)
    st.c["dwl_indent"][indent_label(kind, width)] += 1
    for name in re.findall(r"^\s*(?:var|fun)\s+([A-Za-z_]\w*)", t, re.M):
        st.c["dwl_identifier_case"][case_of(name)] += 1
    st.n["dwl_dq"] += len(re.findall(r"\"[^\"\n]*\"", t))
    st.n["dwl_sq"] += len(re.findall(r"'[^'\n]*'", t))
    st.n["dwl_colon_tight"] += len(re.findall(r"[\w\"')]: ", t))
    st.n["dwl_colon_spaced"] += len(re.findall(r"[\w\"')] : ", t))
    st.n["dwl_if_space"] += len(re.findall(r"\bif \(", t))
    st.n["dwl_if_tight"] += len(re.findall(r"\bif\(", t))
    comments = len(re.findall(r"(^|\s)//|/\*", t))
    st.n["dwl_comments"] += comments
    st.n["dwl_files_with_comments"] += 1 if comments else 0
    st.n["dwl_default"] += len(re.findall(r"\bdefault\b", t))
    st.n["dwl_safe_nav"] += len(re.findall(r"\?\.", t))
    st.c["dwl_final_newline"]["yes" if t.endswith("\n") else "no"] += 1
    stem = path.stem
    prefix = re.split(r"[-_]", stem)[0] if re.search(r"[-_]", stem) else stem
    st.c["dwl_name_prefix"][prefix] += 1
    st.c["dwl_name_case"][case_of(stem)] += 1
    st.add_sample("dwl_name", stem)
    return {"indent": indent_label(kind, width), "lines": len(lines), "comments": comments}


YAML_KEY = re.compile(r"^(\s*)([\"']?)([\w.\-]+)\2\s*:\s*(.*)$")


def measure_yaml(path: Path, st: Stats, proj: Path) -> dict:
    t = path.read_text(errors="ignore")
    lines = t.splitlines()
    st.n["yaml_files"] += 1
    kind, width = indent_profile(lines)
    st.c["yaml_indent"][indent_label(kind, width)] += 1
    m = re.match(r"config-(.+)\.ya?ml$", path.name)
    if m:
        st.c["config_env_names"][m.group(1)] += 1
    st.c["config_location"][path.parent.relative_to(proj).as_posix()] += 1
    comments = 0
    for line in lines:
        if line.strip().startswith("#"):
            comments += 1
            continue
        km = YAML_KEY.match(line)
        if not km:
            continue
        key, value = km.group(3), km.group(4).split(" #")[0].strip()
        st.c["yaml_key_shape"]["dotted" if "." in key else "nested"] += 1
        for part in key.split("."):
            st.c["yaml_key_case"][case_of(part)] += 1
        if value and not value.startswith(("{", "[", "|", ">", "&", "*")):
            if value.startswith('"'):
                st.c["yaml_value_quote"]["double"] += 1
            elif value.startswith("'"):
                st.c["yaml_value_quote"]["single"] += 1
            elif not re.fullmatch(r"-?\d+(\.\d+)?|true|false|null|~", value):
                st.c["yaml_value_quote"]["plain"] += 1
        if "![" in value:
            st.c["secret_placeholder"][re.sub(r"!\[[^\]]+\]", "![<encrypted>]", value.strip("\"'"))[:20]] += 1
    st.n["yaml_comments"] += comments
    st.n["yaml_lines"] += len(lines)
    return {"indent": indent_label(kind, width), "lines": len(lines), "comments": comments}


def measure_munit(path: Path, st: Stats) -> dict:
    t = path.read_text(errors="ignore")
    st.n["munit_files"] += 1
    suffix = re.search(r"([-_](?:test[-_]suite|suite|tests?)|Test(?:Suite)?)\.xml$", path.name)
    st.c["munit_suite_suffix"][suffix.group(1) if suffix else "other"] += 1
    for name in re.findall(r"<munit:test\b[^>]*name=\"([^\"]+)\"", t, re.S):
        c = case_of(name)
        st.c["munit_test_name_case"][c] += 1
        st.add_sample(f"munit_test:{c}", name)
    mocks = re.findall(r"<munit-tools:mock-when\b.*?</munit-tools:mock-when>", t, re.S)
    st.n["munit_mocks"] += len(mocks)
    st.n["munit_mocks_by_docname"] += sum(1 for m in mocks if "doc:name" in m)
    execs = re.findall(r"<munit:execution\b.*?</munit:execution>", t, re.S)
    st.n["munit_exec"] += len(execs)
    st.n["munit_exec_flowref"] += sum(1 for e in execs if "<flow-ref" in e)
    st.n["munit_exec_http"] += sum(1 for e in execs if "<http:request" in e)
    for res in re.findall(r"classpath://([\w./-]+)", t):
        parts = res.split("/")
        st.c["munit_fixture_dirs"]["/".join(parts[:-1]) or "."] += 1
    st.c["munit_fixture_loader"]["readUrl" if "readUrl(" in t else ("getResourceAs" if "getResourceAs" in t else "other")] += 1
    kind, width = indent_profile(t.splitlines())
    return {"indent": indent_label(kind, width), "lines": t.count("\n")}


def measure_oas(path: Path, st: Stats):
    t = path.read_text(errors="ignore")[:200000]
    head = t[:400]
    if path.suffix == ".raml" or head.startswith("#%RAML"):
        st.c["spec_format"]["raml"] += 1
    elif re.search(r"^openapi:\s*['\"]?3\.1", head, re.M):
        st.c["spec_format"]["openapi 3.1"] += 1
    elif re.search(r"^openapi:\s*['\"]?3", head, re.M):
        st.c["spec_format"]["openapi 3.0"] += 1
    elif "swagger:" in head:
        st.c["spec_format"]["swagger 2"] += 1
    else:
        st.c["spec_format"]["schema/fragment"] += 1
    for prop in re.findall(r"^\s{4,}([A-Za-z_][\w]*):\s*$", t, re.M)[:400]:
        if prop not in {"type", "properties", "items", "required", "example", "examples", "description", "schema", "content", "responses", "parameters", "allOf", "oneOf", "anyOf"}:
            st.c["spec_field_case"][case_of(prop)] += 1


def measure_md(path: Path, st: Stats):
    t = path.read_text(errors="ignore")[:100000]
    st.n["md_files"] += 1
    cyr, lat = len(CYRILLIC.findall(t)), len(LATIN.findall(t))
    st.c["doc_language"]["ru" if cyr > lat else "en"] += 1
    for h in re.findall(r"^(#{1,4})\s+(.+)$", t, re.M)[:40]:
        st.add_sample("md_heading", f"{h[0]} {h[1][:60]}")
        st.c["md_heading_case"][case_of(h[1])] += 1
    st.n["md_bullets_dash"] += len(re.findall(r"^\s*- ", t, re.M))
    st.n["md_bullets_star"] += len(re.findall(r"^\s*\* ", t, re.M))
    st.n["md_tables"] += len(re.findall(r"^\|.*\|\s*$", t, re.M))
    st.n["md_mermaid"] += t.count("```mermaid")


def commit_style(repos: list[Path], before: str | None) -> dict:
    subjects, authors = [], Counter()
    for repo in repos[:60]:
        args = ["log", "-n", "40", "--no-merges", "--format=%s%x1f%an"]
        if before:
            args.append(f"--before={before}")
        for line in git(repo, args).splitlines():
            if "\x1f" not in line:
                continue
            subj, author = line.split("\x1f", 1)
            if re.search(r"bot|dependabot|renovate|copilot|claude", author, re.I):
                continue
            subjects.append(subj.strip())
            authors[author] += 1
    c = Counter()
    for s in subjects:
        if re.match(r"^(feat|fix|chore|docs|refactor|test|build|ci|perf|style)(\(.+\))?!?:", s):
            c["conventional-commits"] += 1
        elif re.match(r"^(Merged PR|Merge)", s):
            c["merge"] += 1
        elif re.match(r"^\[?[A-Z]+-\d+", s):
            c["ticket-key-prefix"] += 1
        elif re.match(r"^#?\d+", s):
            c["numeric-id-prefix"] += 1
        else:
            c["free-text"] += 1
    ids = Counter()
    for s in subjects:
        if re.search(r"#\d+", s):
            ids["#123"] += 1
        elif re.search(r"\b[A-Z]{2,}-\d+\b", s):
            ids["KEY-123"] += 1
        elif re.search(r"\b\d{3,6}\b", s):
            ids["bare number"] += 1
    lang = Counter("ru" if CYRILLIC.search(s) else "en" for s in subjects)
    first = Counter("upper" if s[:1].isupper() else "lower" for s in subjects if s[:1].isalpha())
    lengths = [len(s) for s in subjects]
    seen, samples = set(), []
    for s in subjects:
        if s not in seen and not s.startswith("Merge"):
            samples.append(s)
            seen.add(s)
        if len(samples) >= 15:
            break
    branches = Counter()
    for repo in repos[:60]:
        for b in git(repo, ["branch", "-a", "--format=%(refname:short)"]).splitlines():
            b = b.replace("origin/", "")
            branches[b.split("/")[0] + "/" if "/" in b else b] += 1
    return {
        "subjects_seen": len(subjects),
        "style": share(c),
        "ticket_id_style": share(ids),
        "language": share(lang),
        "first_letter": share(first),
        "median_length": int(statistics.median(lengths)) if lengths else 0,
        "samples": samples,
        "branch_prefixes": share(branches),
    }


TRACE_DIRS = (".claude", ".cursor", ".windsurf", ".codex", ".agents", ".aider", ".continue")
TRACE_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules", ".windsurfrules", ".clinerules")
DATE_RE = re.compile(r"\b(20\d\d-[01]\d-[0-3]\d)\b")


def agent_traces(root: Path, projects: list[Path]) -> dict:
    """Find signs of earlier AI-agent use and the earliest date they point to."""
    found = []
    for d in TRACE_DIRS:
        p = root / d
        if not p.is_dir():
            continue
        dates = []
        if (p / ".git").exists():
            first = git(p, ["log", "--reverse", "--format=%ad", "--date=short"]).split("\n", 1)[0].strip()
            if first:
                dates.append(first)
        for f in list(p.rglob("*log*.md"))[:60] + list(p.rglob("*.md"))[:40]:
            try:
                dates += DATE_RE.findall(f.read_text(errors="ignore")[:3000])
            except Exception:
                pass
        found.append({"path": d, "earliest": min(dates) if dates else None})
    for base in [root] + projects[:200]:
        for name in TRACE_FILES:
            f = base / name
            if f.exists():
                repo = base if (base / ".git").exists() else None
                date = None
                if repo:
                    out = git(repo, ["log", "--diff-filter=A", "--format=%ad", "--date=short", "--", name]).strip().splitlines()
                    date = out[-1] if out else None
                if not date:
                    date = dt.date.fromtimestamp(f.stat().st_mtime).isoformat()
                found.append({"path": f.relative_to(root).as_posix(), "earliest": date})
    dates = sorted(x["earliest"] for x in found if x["earliest"])
    return {"traces": found[:20], "suggested_cutoff": dates[0] if dates else None}


def pick_exemplars(entries: list[tuple[Path, dict]], dominant_indent: str, root: Path, k: int, extra=None) -> list[str]:
    if not entries:
        return []
    sizes = sorted(e[1]["lines"] for e in entries)
    lo, hi = sizes[len(sizes) // 4], sizes[(len(sizes) * 3) // 4] or sizes[-1]
    scored = []
    for path, m in entries:
        score = 0
        score += 2 if m.get("indent") == dominant_indent else 0
        score += 1 if lo <= m["lines"] <= hi else 0
        score += 1 if extra and extra(m) else 0
        scored.append((score, path.stat().st_mtime, path))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    out, projects = [], set()
    for _, _, path in scored:
        proj = path.relative_to(root).parts[0]
        if proj in projects:
            continue
        projects.add(proj)
        out.append(path.relative_to(root).as_posix())
        if len(out) >= k:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--out", help="write full JSON here")
    ap.add_argument("--before", help="YYYY-MM-DD; measure only files unchanged since this date")
    ap.add_argument("--all", action="store_true", help="ignore the install-date cutoff")
    ap.add_argument("--exemplars", type=int, default=3)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    before = args.before
    marker = root / ".github/mule-starter/installed-at"
    if not before and not args.all and marker.exists():
        before = marker.read_text().strip()[:10] or None
    cutoff_ts = dt.datetime.fromisoformat(before).timestamp() if before else None

    projects, tf_projects, archetypes = find_projects(root)
    traces = agent_traces(root, projects)
    gi = GitIndex(before)
    st = Stats()
    proj_info = []
    xml_entries, dwl_entries, yaml_entries, munit_entries, md_entries = [], [], [], [], []
    excluded = 0
    per_project_score = {}

    for proj in projects:
        layer = layer_of(proj.name)
        pf = pom_facts(proj / "pom.xml")
        st.c["layer"][layer] += 1
        st.c["parent_pom"][pf["parent"] or "none"] += 1
        st.c["group_id"][pf["groupId"] or "none"] += 1
        for k, v in pf["props"].items():
            st.c[f"pom:{k}"][v] += 1
        globals_file = next((n for n in ("globals.xml", "global.xml", "global-config.xml") if (proj / "src/main/mule" / n).exists()), "other")
        st.c["globals_file"][globals_file] += 1
        st.c["has_beans_xml"]["yes" if list((proj / "src/main").rglob("beans.xml")) else "no"] += 1
        handler = [p.name for p in (proj / "src/main/mule").glob("*.xml") if re.search(r"error", p.name, re.I)]
        for h in handler:
            st.c["error_handler_file"][h] += 1
        is_git = (proj / ".git").exists()
        st.c["project_is_git_repo"]["yes" if is_git else "no"] += 1
        files = {"xml": 0, "dwl": 0, "munit": 0, "yaml": 0}
        for p in sorted((proj / "src/main/mule").rglob("*.xml")):
            if not gi.eligible(p, cutoff_ts):
                excluded += 1
                continue
            m = measure_xml(p, st, layer)
            files["xml"] += 1
            if p.name not in ("globals.xml", "global.xml", "main.xml") and "error" not in p.name:
                xml_entries.append((p, m))
        for p in sorted((proj / "src/main/resources").rglob("*.dwl")) if (proj / "src/main/resources").exists() else []:
            if "api" in p.relative_to(proj).parts or not gi.eligible(p, cutoff_ts):
                excluded += 1
                continue
            dwl_entries.append((p, measure_dwl(p, st, proj)))
            files["dwl"] += 1
        for base in ("src/main/resources", "src/test/resources"):
            for p in sorted((proj / base).rglob("*.yaml")) if (proj / base).exists() else []:
                if "api" in p.relative_to(proj).parts or "exchange_modules" in p.parts or "scaffolder" in p.parts:
                    continue
                if not gi.eligible(p, cutoff_ts):
                    excluded += 1
                    continue
                m = measure_yaml(p, st, proj)
                files["yaml"] += 1
                if base == "src/main/resources":
                    yaml_entries.append((p, m))
        for p in sorted((proj / "src/test/munit").rglob("*.xml")) if (proj / "src/test/munit").exists() else []:
            if not gi.eligible(p, cutoff_ts):
                excluded += 1
                continue
            munit_entries.append((p, measure_munit(p, st)))
            files["munit"] += 1
        api = proj / "src/main/resources/api"
        if api.exists():
            for p in list(api.rglob("*.yaml"))[:30] + list(api.rglob("*.raml"))[:10]:
                measure_oas(p, st)
        readme = proj / "README.md"
        if readme.exists() and gi.eligible(readme, cutoff_ts):
            measure_md(readme, st)
            md_entries.append((readme, {"lines": readme.read_text(errors="ignore").count("\n"), "indent": "n/a"}))
        per_project_score[proj] = (layer, files)
        proj_info.append({"name": proj.name, "layer": layer, "parent": pf["parent"], "git": is_git, **files})

    for d in ("docs", "doc", "documentation"):
        docs = root / d
        if docs.exists():
            for p in sorted(docs.rglob("*.md"))[:200]:
                if not gi.eligible(p, cutoff_ts):
                    continue
                measure_md(p, st)
                md_entries.append((p, {"lines": p.read_text(errors="ignore").count("\n"), "indent": "n/a"}))

    repos = [p for p in projects if (p / ".git").exists()]
    if (root / ".git").exists():
        repos.insert(0, root)
    commits = commit_style(repos, before)

    xml_indent = dominant(st.c["xml_indent"])[0]
    xml_layout = dominant(st.c["xml_attr_layout"])[0]
    dwl_indent = dominant(st.c["dwl_indent"])[0]
    yaml_indent = dominant(st.c["yaml_indent"])[0]

    reference = defaultdict(list)
    ranked = sorted(per_project_score.items(), key=lambda kv: -(min(kv[1][1]["dwl"], 15) + min(kv[1][1]["munit"], 10) * 2 + min(kv[1][1]["xml"], 10)))
    for proj, (layer, files) in ranked:
        if files["munit"] and files["dwl"] and len(reference[layer]) < 3:
            reference[layer].append(proj.name)

    k = args.exemplars
    exemplars = {
        "mule_flow_xml": pick_exemplars(xml_entries, xml_indent, root, k, lambda m: m["layout"] == xml_layout and m["comments"] == 0),
        "dataweave": pick_exemplars(dwl_entries, dwl_indent, root, k, lambda m: m["lines"] >= 8),
        "config_yaml": pick_exemplars(yaml_entries, yaml_indent, root, k),
        "munit_suite": pick_exemplars(munit_entries, dominant(Counter(m["indent"] for _, m in munit_entries))[0], root, k),
        "markdown_doc": pick_exemplars(md_entries, "n/a", root, k),
    }

    n = st.n
    result = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "learned_from_files_unchanged_since": before or "all files (no cutoff)",
        "files_excluded_as_recent": excluded,
        "earlier_agent_use": traces,
        "workspace": {
            "mule_projects": len(projects),
            "terraform_projects": [p.relative_to(root).as_posix() for p in tf_projects][:10],
            "archetypes": [p.relative_to(root).as_posix() for p in archetypes],
            "project_name_prefix": dominant(Counter(re.split(r"[-_]", p.name)[0] for p in projects)),
            "layers": share(st.c["layer"]),
            "parent_pom": share(st.c["parent_pom"]),
            "group_id": share(st.c["group_id"]),
            "pom_properties": {k[4:]: share(v) for k, v in st.c.items() if k.startswith("pom:")},
            "globals_file": share(st.c["globals_file"]),
            "error_handler_files": share(st.c["error_handler_file"]),
            "spring_beans_xml": share(st.c["has_beans_xml"]),
            "per_project_git_repos": share(st.c["project_is_git_repo"]),
            "reference_projects_by_layer": dict(reference),
        },
        "mule_xml": {
            "files": n["xml_files"],
            "indent": share(st.c["xml_indent"]),
            "attribute_layout_per_file": share(st.c["xml_attr_layout"]),
            "self_closing": {"tight '\"/>'": n["xml_selfclose_tight"], "spaced '\" />'": n["xml_selfclose_space"]},
            "attribute_quotes": {"double": n["xml_attr_dq"], "single": n["xml_attr_sq"]},
            "xml_declaration": share(st.c["xml_decl"]),
            "final_newline": share(st.c["xml_final_newline"]),
            "blank_line_ratio": ratio(n["xml_blank_lines"], n["xml_lines"]),
            "comments_per_100_lines": round(100 * n["xml_comments"] / max(n["xml_lines"], 1), 2),
            "files_with_comments": ratio(n["xml_files_with_comments"], n["xml_files"]),
            "doc_name_case": share(st.c["doc_name_case"]),
            "doc_name_samples": {k.split(":", 1)[1]: v[:6] for k, v in st.samples.items() if k.startswith("doc_name:")},
            "doc_id_per_doc_name": ratio(n["xml_doc_id"], n["xml_doc_name"]),
            "flow_name_style": share(st.c["flow_name_style"]),
            "flow_name_samples": {k.split(":", 1)[1]: v[:6] for k, v in st.samples.items() if k.startswith("flow_name:")},
            "file_name_case": share(st.c["xml_file_name"]),
            "transform_external_vs_inline": {"resource=": n["ee_resource"], "inline CDATA": n["ee_inline"], "set-variable/payload with inline mapping": n["setvar_inline_dw"]},
            "logger_level": share(st.c["logger_level"]),
            "logger_category": share(st.c["logger_category"]),
            "logger_message_shapes": [[k, v] for k, v in st.c["logger_message_shape"].most_common(4)],
            "http_request": {"count": n["http_request"], "with_sendCorrelationId": n["http_request_corr"]},
            "error_constructs": {"try": n["try"], "on-error-propagate": n["on_error_propagate"], "on-error-continue": n["on_error_continue"], "raise-error namespaces": share(st.c["raise_error_ns"])},
            "until_successful_by_layer": dict(st.c["until_successful_by_layer"]),
        },
        "dataweave": {
            "files": n["dwl_files"],
            "folder": share(st.c["dwl_folder"]),
            "nested_subfolders": share(st.c["dwl_subfolders"]),
            "header": share(st.c["dwl_header"]),
            "output": share(st.c["dwl_output"]),
            "output_options": share(st.c["dwl_output_options"]),
            "imports": [[k, v] for k, v in st.c["dwl_imports"].most_common(6)],
            "indent": share(st.c["dwl_indent"]),
            "identifier_case": share(st.c["dwl_identifier_case"]),
            "string_quotes": {"double": n["dwl_dq"], "single": n["dwl_sq"]},
            "object_colon": {"'key: v'": n["dwl_colon_tight"], "'key : v'": n["dwl_colon_spaced"]},
            "if_paren": {"'if ('": n["dwl_if_space"], "'if('": n["dwl_if_tight"]},
            "comments_per_100_lines": round(100 * n["dwl_comments"] / max(n["dwl_lines"], 1), 2),
            "files_with_comments": ratio(n["dwl_files_with_comments"], n["dwl_files"]),
            "default_per_file": ratio(n["dwl_default"], n["dwl_files"]),
            "safe_nav_per_file": ratio(n["dwl_safe_nav"], n["dwl_files"]),
            "final_newline": share(st.c["dwl_final_newline"]),
            "file_name_prefix": share(st.c["dwl_name_prefix"]),
            "file_name_case": share(st.c["dwl_name_case"]),
            "file_name_samples": st.samples["dwl_name"][:10],
        },
        "config_yaml": {
            "files": n["yaml_files"],
            "env_names": share(st.c["config_env_names"]),
            "env_names_all": dict(st.c["config_env_names"].most_common(20)),
            "location": share(st.c["config_location"]),
            "indent": share(st.c["yaml_indent"]),
            "key_shape": share(st.c["yaml_key_shape"]),
            "key_case": share(st.c["yaml_key_case"]),
            "value_quotes": share(st.c["yaml_value_quote"]),
            "secret_placeholder": share(st.c["secret_placeholder"]),
            "comments_per_100_lines": round(100 * n["yaml_comments"] / max(n["yaml_lines"], 1), 2),
        },
        "munit": {
            "files": n["munit_files"],
            "suite_suffix": share(st.c["munit_suite_suffix"]),
            "test_name_case": share(st.c["munit_test_name_case"]),
            "test_name_samples": {k.split(":", 1)[1]: v[:5] for k, v in st.samples.items() if k.startswith("munit_test:")},
            "mocks_by_doc_name": ratio(n["munit_mocks_by_docname"], n["munit_mocks"]),
            "execution_entry": {"flow-ref": n["munit_exec_flowref"], "http:request": n["munit_exec_http"], "total": n["munit_exec"]},
            "fixture_dirs": share(st.c["munit_fixture_dirs"]),
            "fixture_loader": share(st.c["munit_fixture_loader"]),
        },
        "api_spec": {"format": share(st.c["spec_format"]), "field_case": share(st.c["spec_field_case"])},
        "docs": {
            "files": n["md_files"],
            "language": share(st.c["doc_language"]),
            "heading_case": share(st.c["md_heading_case"]),
            "heading_samples": st.samples["md_heading"][:10],
            "bullets": {"-": n["md_bullets_dash"], "*": n["md_bullets_star"]},
            "table_rows": n["md_tables"],
            "mermaid_blocks": n["md_mermaid"],
        },
        "git_commits": commits,
        "exemplars": exemplars,
        "projects": proj_info,
    }

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=1, ensure_ascii=False))

    summary = {k: v for k, v in result.items() if k != "projects"}
    print("# Style facts (dominant value, count, share)")
    print(json.dumps(summary, indent=None, ensure_ascii=False, separators=(",", ":")).replace('},"', '},\n"'))
    return 0


if __name__ == "__main__":
    sys.exit(main())

---
name: mule-init
description: "Calibrate this workspace's agents to its human-written code. Measures style of Mule XML, DataWeave, config, MUnit, docs and commits, then writes house-style instructions and the workspace profile. Use for /init, /mule-init, \"initialize\", \"learn our style\", or after big codebase changes."
---

# mule-init — learn the house style

Goal: every file an agent writes after this is indistinguishable from what the team wrote by hand before agents arrived. Evidence first; no rule without a measurement or an exemplar behind it.

## Steps

### 1. Measure
```bash
python3 .github/skills/mule-init/scripts/profile_workspace.py . --out .github/mule-starter/style-facts.json
```
Read the printed summary only (never the JSON file whole). Fields are `[value, count, share]`.

### 2. Fix the learning cutoff
The script learns only from files unchanged since `learned_from_files_unchanged_since` (install date by default).
If `earlier_agent_use.suggested_cutoff` is earlier — AI agents already wrote code here — ask the user once:
"Learn style only from files unchanged since <suggested_cutoff> (first agent trace: <path>)?" Options: that date / install date / all files.
Unattended: take `suggested_cutoff`. Re-run step 1 with `--before <date>` (or `--all`). State the cutoff in the final reply.

### 3. Read exemplars (token budget)
For each category in `exemplars`, open the first 2 files, at most 120 lines each. Note what the numbers cannot show: blank-line rhythm between processors, logger wording, how DWL objects are laid out, how tests are named and grouped, doc tone.

### 4. Import knowledge from an earlier agent harness (if present)
If `CLAUDE.md`, `.claude/memory*`, `.cursor/rules`, or another agent's instruction files exist: grep them for build/test commands, explicit user decisions (usually dated), and verified gotchas. Copy durable facts only — ≤ 40 lines total into `profile.md` (facts, decisions) and `memory/lessons.md` (gotchas). Skip task history, logs, per-ticket notes.

### 5. Decide rules
| Share of dominant value | Rule strength in generated file |
|---|---|
| ≥ 0.80 | **MUST** — write the rule plainly |
| 0.60–0.79 | **PREFER** — "prefer X; inside an existing file, follow that file" |
| < 0.60 | **NO WORKSPACE RULE** — "mirror the file being edited, else its siblings in the same folder" |

Every rule line ends with its evidence: `[0.95 · 582 files]` or `[exemplar: path]`. Quote real samples (doc:name, flow names, test names, commit subjects) instead of describing them.

### 6. Write files
Follow `references/generated-files.md` for the exact layout of each file.

| File | applyTo |
|---|---|
| `.github/instructions/house-style.instructions.md` | `**` |
| `.github/instructions/house-style-mule-xml.instructions.md` | `**/src/main/mule/**/*.xml` |
| `.github/instructions/house-style-dataweave.instructions.md` | `**/*.dwl` |
| `.github/instructions/house-style-config.instructions.md` | `**/src/*/resources/**/*.yaml,**/src/*/resources/**/*.properties` |
| `.github/instructions/house-style-munit.instructions.md` | `**/src/test/**` |
| `.github/instructions/house-style-docs.instructions.md` | `**/*.md` |
| `.github/mule-starter/profile.md` | (read by agents on demand) |

Rules:
- Each instructions file ≤ 4 KB, `profile.md` ≤ 6 KB. Cut adjectives, not facts.
- Regenerating: overwrite everything except the `## Overrides` section, which is kept verbatim (team edits live there).
- Do not restate shipped defaults (`mule-*.instructions.md`); write only what this workspace does, including where it differs from the defaults.
- `profile.md` build/test commands: take them from READMEs, existing harness files, CI files, or `pom.xml` (MUnit plugin `mule.key`, env property). Never invent a command; mark unknowns `UNKNOWN — ask once`.

### 7. Wire up
- `.github/copilot-instructions.md` and `AGENTS.md`: the `mule-starter:begin … end` blocks exist and are unchanged (restore from `references/generated-files.md` if missing). Outside the block, `/init` may add a short project overview.
- Write `.github/mule-starter/installed-at` (today, `YYYY-MM-DD`) if missing.
- Check: every generated instructions file starts with valid frontmatter (`applyTo`, `description`).

### 8. Reply
Caveman mode. Table `File | Rules | Notable`, then: cutoff used, areas with no workspace rule, 3 strongest rules with evidence, anything marked UNKNOWN.

## Never
- Learn from files changed after the cutoff, generated code (`target/`), or archetype templates.
- Promote a minority style to a rule, or "improve" the team's style (no reformatting campaigns, no new conventions).
- Store secrets, hostnames with credentials, or client data in generated files.

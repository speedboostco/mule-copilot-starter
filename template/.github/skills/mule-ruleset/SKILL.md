---
name: mule-ruleset
description: "Analyze one Mule project and write .github/mule-starter/rulesets/<project>.md — the conventions, reuse inventory and error strategy every later edit must follow. Use before implementing in a project with no ruleset, or when the task adds an endpoint, downstream call or new error case the ruleset does not cover."
---

# mule-ruleset — project analysis

Output: `.github/mule-starter/rulesets/<project>.md` (≤ 15 KB) + `rulesets/current.md` (active run, ≤ 2 KB). Read-only on source code. Never run Maven here.

## Skip when
The ruleset exists, covers the target flow/resource, and its Error Strategy table covers this task's error cases. A newer log line is not a reason to re-run.

## Steps
1. **Scope** — target project(s) from the task; dependencies it calls are scanned read-only (contract only). Nothing else.
2. **Outline before reading** — big files (> 20 KB): `grep -n '<flow name=\|<sub-flow name=\|munit:test name='` then read ranges.
3. **Identity** — artifactId, version, parent (read this project's `pom.xml`; never assume the workspace dominant), layer, spec name/version, env files present.
4. **API contract mode** (experience layer) — APIkit `api=` points to an Exchange artifact (`resource::…:oas:zip`) or a local file; local `api/` gitignored? Spec version resolvable in `~/.m2` (`find ~/.m2/repository -ipath "*<spec.name>*" -iname "*oas*.zip"`)? Record once; never web-search publication status of a private spec.
5. **Global config & reuse inventory** — `python3 .github/skills/mule-reuse/scripts/reuse_scan.py <project>`; record global configs, wrapper sub-flows, placement file for new wrappers, existing duplicates (known debt).
6. **Flows table** — flow name | file | trigger/path | outbound `doc:name`s | DWLs used.
7. **Error strategy** — `mule-error-strategy` skill: locate the global handler and the DWL that builds the error; quote the facts that decide behavior (status source order, relay condition, status collapse). List existing local error constructs and label each: legitimate row (V/S/E) or legacy pattern not to copy. Build the table for this task (classes P/V/S/E/T).
8. **Conventions with real examples** — logger expression, transform wiring, DWL naming, config keys incl. secure ones, Spring security beans if any, retry (system layer), MUnit shape (main suite + per-resource suites, mocks by `doc:name`, fixtures).
9. **Inconsistencies** — when the project mixes patterns, name the dominant one to follow and the minority as legacy.
10. **Plan for this run** — one section `Implementation rules for this run`: files to touch, Reuse Plan (each call: REUSE `<wrapper>` | NEW `<system>-services:<op>` in `<file>`), error rows, tests expected by the Test Necessity Gate.

## Updating an existing ruleset
Edit base sections in place so they describe the code as it is now. Replace only `Implementation rules for this run`; move the old content as one dated line-summary into `rulesets/archive/<project>-history.md`. No dated sections in the live file.

## Template
`references/ruleset-template.md`.

## Return (caveman ultra)
`RULESET <path> | layer | contract mode + .m2 status | error rows P/V/S/E/T counts | reuse: n wrappers, n NEW planned | risks: …`

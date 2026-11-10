---
name: systematic-debugging
description: "Root-cause-first debugging for Mule bugs, MUnit failures, build or deploy errors, DataWeave exceptions and unexpected runtime behavior. Use before proposing any fix."
---

# systematic-debugging

**No fix without a reproduced root cause.**

## Phase 1 — Investigate
1. Read the whole error: Mule error type, error variable shape, stack trace, assertion diff — not just the first line.
2. Reproduce: targeted MUnit test entering by `flow-ref` (one targeted run is fine here), or a real request when the user has a running instance. Cannot reproduce → gather evidence, do not guess.
3. What changed: `git diff`, `git log -5`, `grep <project> .github/mule-starter/log.md | tail`, parent/dependency bumps, config per env.
4. Multi-layer failure: evidence at each boundary (experience → process → system → backend): status, body, error variable at each hop. Find where behavior first diverges.
5. Trace a wrong value backward: where it was set (transform/DWL) → its input → origin (backend response, request, config).

## Phase 2 — Compare
Diff the broken flow/DWL against a working sibling line by line; list every difference (media type, `doc:name`, key spelling, env naming). Read the ruleset section fully.

## Phase 3 — Hypothesis
"X is the root cause because Y." Change one thing. Re-run the exact reproduction. Not confirmed → back to Phase 1 (counts as an iteration).

## Phase 4 — Fix
Reproducing test first (or the existing failing one), minimum fix at the root, then `verify-before-done`.

## Stop rules
- 3 failed iterations on one issue → escalate with evidence; a fourth guess is not allowed.
- Three fixes each surfacing a new symptom elsewhere = architecture problem (layer boundary, shared DWL, retry in wrong layer) → escalate.
- Infrastructure failures (network, port clash, sleeping laptop) do not count as iterations.

Red flags: "quick fix for now", "let me just try", editing several things "to cover possibilities", blaming config you have not read.

Output: root cause (one sentence), evidence, the single fix, verification command + result.

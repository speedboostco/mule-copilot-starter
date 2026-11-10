---
name: mule-quality-gate
description: "Independent post-implementation review and Definition of Done gate for Mule changes (falls back to general code review for other languages). Use after any implementation or bug fix before handoff, and for PR/diff/code reviews."
---

# mule-quality-gate

Treat the change as a PR from another engineer. Re-derive everything from the working tree and commands you run; the author's summary and the log are claims to check.

## Workflow
1. **Scope** — `git status` / `git diff` in the project repo; changed files read fully, plus the flows, tests and config that give them meaning; ruleset; requirement.
2. **Checklist** (Mule: below; other languages: `references/general-code-review.md`).
3. **Run the gate yourself** (commands from `profile.md`): build from scratch, then the full test suite. Report the literal result lines (tests run, failures, skipped, coverage).
4. **Test ladder + DoD** — `references/test-ladder.md`: state each category as enforced / approximated / N/A with the reason. Never report a pass for a tool that did not run.
5. **High-risk change** (shared library, global handler, security-sensitive flow, irreversible backend op) → `premortem` skill red-team pass.
6. Re-read every changed file before the verdict.

## Mule checklist
- **Scope/MVP**: every hunk traces to the request or design doc. No unrequested batching, async, orchestration, rollback, filtering, renamed fields, or copied naming whose reason does not apply. No edits to working flows as a side effect. Leftovers the change created (DWL, config key, sub-flow, mock, fixture) removed; pre-existing dead code only noted.
- **Style**: diff indistinguishable from surrounding code (house-style files, neighbouring lines). No new comments unless house style shows them.
- **Contract**: spec/APIkit mappings match flows; response DWL keys == schema `properties` == example keys.
- **Layering**: experience shapes, process orchestrates, system adapts; no backend specifics leaking up.
- **Reuse**: `mule-reuse --only <changed>` clean; calls via wrappers; configs only in globals.
- **Errors**: every `raise-error`/`on-error-*`/`<error-handler`/`try`/error DWL maps to a V/S/E row; else blocking, correction = delete and propagate.
- **Retry/async**: retry only around system-layer backend calls; 202 does not imply process-layer `<async>`.
- **DataWeave**: externalized, null-safe, traps checked (`dataweave.instructions.md`).
- **Config**: all env files consistent, placeholders only, test stubs present.
- **Secrets/logging**: no credentials, tokens, PII, full payloads in code, fixtures, logs, docs. Outbound calls propagate correlation ID like siblings (`sendCorrelationId` or explicit header).
- **Tests**: ledger exists and holds against the diff; ADD lines have tests; shape rules kept (flow-ref entry, mocks by `doc:name`); nothing deleted, disabled or loosened; no passing test's expectations edited. A missing test for a SKIP case is never a finding.
- **XML**: layout matches file; `doc:name` selectors stable.

## Verdict
Findings first, ordered by severity, each `file:line` + concrete correction. Then: validation run, ladder status, DoD table, residual risk.
Last line exactly one of: `GATE_PASS` · `GATE_BLOCKING: <n> findings` · `ESCALATE: <reason>`.
Review only — never edit files; fixes go back to the implementer.

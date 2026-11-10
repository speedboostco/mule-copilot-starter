# Test ladder and Definition of Done (Mule)

Commands come from `profile.md`. Status per category: Enforced / Approximated (say how) / N/A (say why).

| # | Category | Mule mechanism |
|---|---|---|
| 1 | Format | `xmllint --noout` on changed XML; manual diff vs surrounding style for YAML/DWL (no auto-formatter) |
| 2 | Lint | `mule-dataweave` scanner + review (no DWL linter exists) — Approximated |
| 3 | Compile | project build command, from clean |
| 4 | Unit | full MUnit suite |
| 5 | Property-based | no framework for DWL — N/A |
| 6 | API schema | `mule-oas-contract` + response-shape assertions (experience layer) |
| 7 | Integration | real deployment — N/A unless the user deployed and asked for `mule-live-test` |
| 8 | Contract | inter-layer field casing + schema checks |
| 9 | Security | `mule-security-scan` when run (SCA + SAST); else credential/placeholder grep — say which |
| 10 | Mutation | `mule-dwl-mutation` when run for conditional DWL; else N/A |
| 11 | E2E | N/A unless `mule-live-test` on request |
| 12 | Performance smoke | N/A unless `mule-live-test` on request |

## Definition of Done (blocking unless N/A with reason)
| Criterion | Check |
|---|---|
| Builds from scratch | build command exit 0 |
| All tests pass, none skipped | full suite; no removed/disabled `<munit:test>` in diff |
| Coverage not decreased | before/after from coverage report; a drop is OK only when caused solely by code the ledger marks SKIP (state it) |
| Mutation score not decreased | real score if run, else N/A |
| Contract intact | `mule-oas-contract` clean |
| No new critical/high vulnerabilities | scan result if run (pom/dependency change → run it), else grep fallback stated |
| No secrets | grep diff: only placeholders |
| Acceptance tests untouched | no edited expectations of pre-existing passing tests |
| Smoke test | N/A unless live test requested |

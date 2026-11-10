---
name: mule-munit
description: "Decide which MUnit tests a change needs (Test Necessity Gate), design edge-case and regression scenarios, and build them with mocks by doc:name and flow-ref entry. Use after changing Mule XML, DWL, validation, downstream calls or error behavior, and for bug regression tests."
---

# mule-munit — only tests that earn their place

## 1. Test Necessity Gate (always first)
A test earns its place only if it would fail on a plausible defect in project-owned code this change touched, and no existing test already fails on it. Name that defect in a few words; if you cannot, write nothing. Coverage % is an outcome, never a reason.

Search `src/test/munit/` for the flow, the DWL file and the outbound `doc:name`. Then write one ledger line per changed branch, DWL file, validation and outbound call:
`ADD <test name>` · `COVERED <suite#test>` · `SKIP:<reason>`

| SKIP reason | Covers |
|---|---|
| `test-code` | change confined to `src/test/**` — no tests for tests |
| `no-logic` | pass-through, 1:1 field copy, logger, `doc:name`, rename, config/pom/OAS/doc-only edit |
| `framework` | anything APIkit/OAS enforces (types, required, enums, patterns, 400/404/405/415/501), listener/config wiring, connector timeout/retry mechanics, global handler's generic mapping |
| `equivalent` | input with the same behavior as a covered case (each null/blank/missing, each enum value, each 5xx) |
| `mock-only` | assertion whose subject is a mock/stub, or behavior the project does not implement |

ADD only for: one happy path per new endpoint/flow · a new or changed conditional/default/format/coercion/aggregation · each validation or business rule this project owns · one downstream-error test per new or changed outbound call · system-layer retry count when retry changed · the exact shape of a fixed bug (unless the reproducing test is it) · a consumer behavior of a changed shared DWL/flow that no test covers.

No ADD line → no test, no extra Maven run; say so.

## 2. Scenario design (for ADD lines with input handling or downstream calls)
Pick from `references/scenario-catalog.md` (a menu, not a checklist): boundary and malformed inputs only where project logic distinguishes them, one representative per equivalence class; downstream timeout/4xx/5xx/empty/malformed body as one propagation test per call; idempotency, ordering, partial success when relevant. A scenario that seems to need a local handler is a listed deviation (`mule-error-strategy`), not production code.

## 3. Test shape
- Main suite (`main-test-suite.xml` or the project's name): health check + router invoked with router and security filters mocked. Touch it only when the main flow changed.
- Every other test: per-resource suite, entry by `flow-ref` to the flow the router dispatches to; `munit:set-event` supplies payload and attributes (`uriParams`, `queryParams`, `headers`, `method`).
- Mock each outbound `http:request` (token calls included) by `doc:name`; mock a shared sub-flow `flow-ref` only when it is out of scope.
- Assert payload against response fixtures, `vars.httpStatus`, `verify-call` counts, END logger on success when siblings do.
- Never through the real listener/router: no `http:request` to localhost in execution, no enabling flow sources to drive a route, no `APIKIT:*` error mocks, no per-constraint variants. A ruleset or legacy suite showing otherwise is superseded; say so in the reply.

## 4. Build
1. Copy suite/test naming and fixture layout from `house-style-munit` and a sibling suite.
2. Fixtures in the existing scaffolder dirs (request / mock / response).
3. Run the full project suite once after the last test edit (command in `profile.md`). Single-test runs only to debug a failure.
4. Prove a new assertion is live: temporarily break one expected value, see it fail, restore.

## 5. Report
Ledger, tests added, commands + literal result line, coverage before/after (reported, never chased).

Gotchas: `references/checklist.md`.

# <project> ruleset
Analyzed <YYYY-MM-DD> · layer <experience|process|system> · scope: <this project; read-only deps: …>

## 1. Identity
| Key | Value |
|---|---|
| artifactId / version | |
| parent | |
| spec.name / spec.version | |
| contract mode | Exchange zip (local api/ is scratch) \| local file authoritative |
| spec in ~/.m2 | resolved \| not found (checked <date>) |
| env files | |

## 2. Flows
| Flow | File | Trigger / path | Outbound doc:name | DWL |
|---|---|---|---|---|

## 3. Global config and reuse inventory
- Global configs (globals file): `<name>` → host/basePath keys, auth.
- Wrappers: `<system>-services:<op>` (file) → method path.
- Placement for new wrappers: `<file>`.
- Known duplicates (debt, not this task): …

## 4. Error strategy
- Global handler: `<file>`; error DWL: `<path>`; template: system \| relay.
- Facts: status source order …; relay condition …; status collapse …; extra fields …
- Existing local constructs: `<file>/<flow>` — V/S/E row \| legacy, do not copy.

| Case (requirement/design doc) | Expected | Propagation yields (quoted) | Class | Decision |
|---|---|---|---|---|

## 5. Config
- Common keys pattern, env-specific keys, secure keys (`secure::…`), test config stubs.

## 6. Logging and transforms
- Logger: `<exact expression>` START/END INFO, DEBUG before outbound.
- Transform: `<ee:transform>` + `<folder>/<pattern>.dwl`.

## 7. Security
- Spring beans / filters, credential property names, health path excluded or not.

## 8. MUnit
- Suites: main (APIkit) + `<resource>-test-suite.xml`; entry by flow-ref; mocks by doc:name; fixtures `<dirs>`; retry count verified (system layer).

## 9. Read-only dependencies
| API | Method path | Request | Response | Auth | Errors |
|---|---|---|---|---|---|

## 10. Implementation rules for this run
- Task: …
- Files: …
- Reuse plan: | Call | REUSE/NEW | Where | Why |
- Error rows used: …
- Tests expected (gate): ADD … / SKIP …

## 11. Constraints and inconsistencies
- Dominant pattern to follow vs legacy patterns present.

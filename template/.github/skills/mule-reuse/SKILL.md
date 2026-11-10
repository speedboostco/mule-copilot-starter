---
name: mule-reuse
description: "Inventory a Mule project's global connector configs and wrapper sub-flows and flag duplicated operations/configs. Use before adding or changing any outbound call or publish (http, amqp, db, sftp, sap…), and to check a diff for new duplicates."
---

# mule-reuse — one wrapper per backend operation

```bash
python3 .github/skills/mule-reuse/scripts/reuse_scan.py <project>                       # inventory + placement
python3 .github/skills/mule-reuse/scripts/reuse_scan.py <project> --only a.xml,b.xml    # findings for changed files
```

## Decide per call (before writing XML)
- **REUSE** — a wrapper with the same config, method and path exists: `<flow-ref name="<system>-services:<op>"/>`. Read the wrapper and one existing caller to copy how inputs arrive (vars) and how result and `vars.httpStatus` come back. Never copy the operation, its logger pair, or its `doc:name`.
- **NEW** — no wrapper matches, or the contract differs (query, headers, body, response shape): add one sub-flow `<system>-services:<op>` with exactly one connector operation in the services file the scan names (create it if the backend has none). Do this even for a single caller. Never change an existing wrapper's inputs or response; add a sibling.
- Publishes (queues/topics) go through the project's publish wrapper with the routing key in the variable it reads.
- Global configs only in the globals file, one per backend; a second one only for a genuinely different connection setting, named in the reply.
- Cross-project sharing is the workspace shared library only; never copy its flows into a project.

## MUnit impact
Mocks key on the wrapper's `http:request doc:name`; reusing adds no selector. Mocking the `flow-ref` by `doc:name` also works; a mock on a `doc:name` that no longer exists is a silent no-op — check every selector.

## Finish
Re-run with `--only <changed files>`: no new `duplicate-operation`, `extract-candidate`, `duplicate-config`, `config-outside-globals`. Pre-existing duplicates are listed as extraction candidates, never refactored as a side effect.

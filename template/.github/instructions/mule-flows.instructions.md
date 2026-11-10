---
applyTo: "**/src/main/mule/**/*.xml"
description: "Shipped defaults for Mule 4 flow XML. House style and the project ruleset override these."
---
# Mule flow XML — defaults

Check `house-style-mule-xml.instructions.md` and the project ruleset first; where they state a different convention, follow them.

## Structure
- Data mapping (build a request, response, variable value): `<ee:transform>` with an external DWL file (folder and name pattern from house style; default `src/main/resources/dwl/set-<resource>-<purpose>.dwl`). Inline `#[...]` only for a plain variable read, a literal, or a logger expression.
- Flow names, file-per-resource layout, `doc:name` casing: copy the dominant pattern of the project (default flow name `<module>:<operation>`, one XML per resource).
- `doc:name` on `http:request` is the MUnit mock selector: unique per file, descriptive, never renamed without updating tests. `doc:id` is not a convention to add or audit.
- HTTP status via `vars.httpStatus` when the listener reads it.
- Loggers: copy the project's existing pattern (level, category, message builder). Never log credentials, auth headers, full payloads, or PII.

## Layers (`-eapi` / `-papi` / `-sapi` or the names in `profile.md`)
- Experience: consumer contract, APIkit routing, response shaping, 202 async handoff to process layer.
- Process: orchestration and business rules. A 202 response does not imply an `<async>` scope here.
- System: 1:1 backend adapter, connectivity retry, target-format mapping.
- Inter-layer payloads use the workspace field casing (default camelCase); the system layer maps to backend format in DWL.

## Retry
Retry belongs to the system layer only: `until-successful` (or the project's retry properties) around the backend `http:request` only, never around loggers or transforms. Other layers get retry only when the requirement names that layer.

## Errors (details: `mule-error-strategy` skill)
Propagate by default: a failed outbound call reaches the project's global error handler, which relays status and body upstream. Add `try`, `raise-error`, `on-error-*`, flow-level handlers, error DWLs or custom error namespaces only for an Error Strategy row of the project ruleset.

## Connector reuse (details: `mule-reuse` skill)
- Before adding an outbound operation: reuse an existing wrapper sub-flow with the same config, method and path via `flow-ref`; otherwise create one wrapper sub-flow (one connector operation) in the project's services file. Never copy an operation or create a second global config for the same backend.
- Global connector configs live only in the project's globals file.
- Do not refactor pre-existing duplicates as a side effect; list them in the reply.

## Editing discipline
- No auto-formatting. New/changed XML copies the surrounding indentation, attribute-per-line layout, quoting and blank-line rhythm.
- Validate with `xmllint --noout <file>`; never reformat to validate.
- `attributes` is overwritten by the latest `http:request` response: capture inbound `uriParams`/`queryParams`/headers into `vars` before the first outbound call if needed later.
- Report each XML change as file + flow/sub-flow + `doc:name`.

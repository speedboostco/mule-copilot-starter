---
name: mule-error-strategy
description: "Decide Mule error handling by propagation first. Classifies each error case of a requirement as P/V/S/E/T and says which local construct, if any, is allowed. Use before adding try, raise-error, on-error-*, error DWLs or handlers, when a design doc has an error table, or when an error status/body is wrong."
---

# mule-error-strategy — propagate by default

Mechanics: `references/propagation.md`. Workspace specifics (shared error library, business error namespace, decisions): `profile.md` and the project ruleset.

## Default
A failed outbound call needs no local construct. It reaches the project's global error handler, which builds the response; across layers the system layer's status/description is relayed upward. Catching it locally and re-raising a custom type throws away the downstream text and code and must then be rebuilt in every layer.

## Classify every error case (one row each in the ruleset table)
| Class | Meaning | Allowed construct |
|---|---|---|
| P | Global handler already yields an acceptable status/body | none |
| V | Business/validation outcome produced in this layer | `raise-error` with the workspace business namespace type that maps to the status (e.g. `<NS>:BAD_REQUEST`, `NOT_FOUND`, `CONFLICT`) + `description`; set `vars.httpStatus` first if the layer's DWL collapses statuses |
| S | A downstream status the layer's DWL would collapse must reach the client | reuse the project's existing relay pair exactly as sibling flows do (`try` + narrow `on-error-propagate` + shared DWLs + custom-relay error type); never a per-flow copy of DWLs |
| E | Design doc defines the failure as a normal outcome (unknown user → empty list) | `on-error-continue` with a narrow `type=` (never ANY) returning the defined success payload |
| T | Design doc wants a status/text/numeric code propagation cannot produce | none — implement P, quote both outputs in the reply and the ruleset as a deviation |

T rows become code only when the user explicitly files that row as a bug; then build the narrowest construct for that one row (`try` + narrow `on-error-propagate` + one external DWL + `raise-error` of the relay type, code from a config property). It is not a precedent for other rows.

## Never
- Invent error namespaces (`BACKEND:*`); only the workspace business namespace maps to statuses.
- Copy a sibling's `try`/handler chain unless this flow's row is S or E (siblings may carry legacy patterns).
- Add retry, status-text tables or `vars.targetStatus`-style variables outside the system layer.
- Add stub flows, handlers or invented error shapes in `src/main` to make a relayed body testable.

## Debugging a wrong error response
Find the layer where the information is lost, not where it becomes visible: system-layer error DWL (exposed backend text, app code) → each upstream layer's global-handler DWL (relay condition, status collapse). Fix that one DWL; never add a flow-level handler at each layer.

## Audit (before returning work)
`grep -n 'raise-error\|on-error-\|<error-handler\|<try' <changed files>` → each hit maps to a V/S/E row, else delete it.

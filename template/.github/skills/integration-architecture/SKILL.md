---
name: integration-architecture
description: "Turn a new integration requirement into an architecture package - reuse/extend/create per API, layer choice, Mermaid diagrams, CR-style design doc, stakeholder questions, internal user stories, ordered plan. Use before coding when ownership or layers are unclear or the scenario spans several APIs."
---

# integration-architecture

Read-only until the user approves execution.

## Steps
1. Context: `profile.md`, relevant rulesets, `memory/lessons.md`, the requirement (PDF/image/text/spec).
2. Discover existing capability before proposing anything new: search projects by domain noun, backend system, path, schema, verb; read candidate specs/globals/flows only as needed. With a platform token, add live evidence via `anypoint-platform` (read-only). Local and live disagree → stakeholder question.
3. Mark each API `reuse` / `extend` / `create`, with file (and live) evidence. Hard-to-reverse calls (new system-layer ownership, shared orchestration) → `premortem` first.
4. Layers: experience = consumer contract, routing, shaping, 202 handoff; process = orchestration/business rules (202 ≠ `<async>` here); system = backend adapter, connectivity retry, names the failing system in errors. Upper layers relay errors unchanged — design no per-layer error translation.
5. Diagrams: always a `flowchart LR` of consumer → layers → backends; `sequenceDiagram` for async, callbacks, retries, several backends, non-trivial errors. Mermaid in Markdown, no images.
6. Design doc (when asked): `references/architecture-documentation-format.md`. Every response example field has a mapping row (hardcoded fields as `hardcoded` + value); count fields vs rows. The platform is one participant — internal layers belong to the developer handoff only. Errors described as propagation produces them. No negative-space sentences.
7. Stakeholder questions: only facts/decisions another team owns (their data model, field names, process rules, credentials, environments). Keep our own design decisions out of that list.
8. Stories + plan: `references/architecture-output-format.md`, ordered contract → config → flows/DWL → tests → validation.
9. Execution (only if asked): one story at a time through `mule-conductor`.

## MVP rules
Design the minimum the source requires. Ambiguous simple-vs-complex wording → simple design + one stakeholder question. Never redesign a working operation as a side effect; add a new one. Keep source field names; reuse a naming pattern only when its reason applies.
Separate decisions, assumptions, open questions. Never invent credentials, endpoints or mappings.

---
name: mule-new-project
description: "Scaffold a new Mule API project from the workspace archetype (or the closest same-layer project when no archetype exists), aligned to the newest same-layer style, then validate it. Use when the user asks to create a new experience/process/system API project."
---

# mule-new-project

1. Normalize name: `<prefix>-<name>-<layer>` (prefix and layer suffixes from `profile.md`). Target folder exists → stop and ask.
2. Read 2 newest same-layer projects (reference projects in `profile.md`): parent version, spec naming, config layout and env names, globals file name, security (Spring beans) and gateway autodiscovery usage, health-check test.
3. Archetype present (`profile.md`) → `references/archetype-commands.md`, non-interactive. None → copy the skeleton of the closest same-layer reference project and strip business flows, keeping main/globals/error handler/config/health test.
4. Post-process only to match same-layer style; no leftover template markers (`#if`, `${artifactId}`); no business endpoints unless the user supplied the contract.
5. Validate: `xmllint --noout` all XML, YAML parse, `mule-config-matrix`, `mule-oas-contract`, build + test commands from `profile.md`.
6. No deploy, no Exchange publish, no commit unless asked.

Report: path, layer choices (auth, gateway, parent), files created (table), validation results.

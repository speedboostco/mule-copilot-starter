---
name: mule-dataweave
description: "Write or review DataWeave and transform wiring - externalized DWL, inline-mapping violations, null safety, unused/missing DWL files, runtime traps. Use when creating or editing .dwl files, ee:transform blocks, set-variable/set-payload expressions, or debugging a transform error."
---

# mule-dataweave

```bash
python3 .github/skills/mule-dataweave/scripts/scan_dwl_usage.py <project>
```
Reports complex inline mappings, missing/unused DWL files, deep unguarded access, TODO markers.

## Write
1. Style: `house-style-dataweave.instructions.md`; copy the header, output directive and option spelling of a sibling file in the same folder.
2. Anything that builds an object, array, query params, form body, response or variable → `<ee:transform>` + external file. Inline only for literals and plain reads (`#[payload]`, `#[vars.x]`, `#[202]`).
3. Output media type matches the downstream contract (JSON default; XML/Java/form-urlencoded where the backend needs it).
4. Optional fields: `default`, guarded `if`, `?.`. Null stripping (`skipNullOn`) only where siblings use it.
5. Check `dataweave.instructions.md` traps line by line.
6. Non-trivial logic (regex, indexing, parsing, aggregation): simulate with realistic data before wiring it — `dw` CLI if installed, else a throwaway script — and delete the scratch file.
7. Response DWL changed → diff its output keys against the OAS response schema `properties` and `example` in the same pass.

## Review output
Findings first with `file:line`; build-breaking separated from style. Edit unrelated mappers only when they sit on the changed data path. Remove DWL files your change left unused; report pre-existing unused files, do not delete them.

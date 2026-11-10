---
applyTo: "**/*.dwl"
description: "DataWeave 2.0 traps that compile but fail at runtime or silently return wrong data. Style comes from house-style-dataweave."
---
# DataWeave — correctness traps

Style (header, output directive, indentation, naming): `house-style-dataweave.instructions.md` and the neighbouring `.dwl` files.

Check every new or changed expression against this list:
- `++` concatenates arrays/objects; `+` does not.
- Multi-value selector is unquoted: `attributes.headers.*key`, not `.'*key'` (quoted form silently returns empty).
- Lambda bodies are greedy across chained infix calls: `(arr filter (x) -> c) flatMap (x) -> e` — parenthesize each step.
- Index a call result only after parenthesizing the whole call: `(arr filter ($.id == x))[0]`.
- `scan()` returns `Array<Array<String>>`: `[0][0]` is the full match, `[0][1]` is group 1.
- `substringBefore/After(Last)` need `import * from dw::core::Strings`.
- Infix `startsWith`/`endsWith`: use function form `startsWith(text, prefix)`.
- Infix calls bind looser than comparisons: `(i mod 17) == 0`.
- An expression mixing `vars` (java) and `payload` (json) needs an explicit `output` directive.
- Optional input fields: `default`, guarded `if`, or `?.`; never deep-access an optional path bare.
- A status regex written as a prefix (`/^(000\.200)/`) is applied with `contains`, not `matches` (whole-string).

For regex, indexing, multi-field or string-parsing logic: simulate it against realistic sample data (scratch script or `dw` CLI) before trusting it.
When a response DWL changes, re-check the paired OAS response schema in the same pass: field set of DWL output == schema `properties` == example keys.

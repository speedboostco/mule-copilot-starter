---
name: mule-oas-contract
description: "Validate API contract wiring of a Mule API - pom spec.name/spec.version, spec dependency, APIkit config, flow mappings vs real flows, local Maven cache status. Use when adding/changing endpoints, bumping a spec, or debugging APIkit 404/spec-not-found errors."
---

# mule-oas-contract

```bash
python3 .github/skills/mule-oas-contract/scripts/check_oas_contract.py <project>
```

## Steps
1. Only projects that actually contain APIkit/spec wiring.
2. `pom.xml`: `spec.name`, `spec.version`, spec dependency (classifier/type), parent (this project's, not the workspace dominant).
3. Globals: `apikit:config` `api=`, `httpStatusVarName`, every flow mapping → a real `<flow name>`.
4. Change order for a path/operation: spec (or dependency version) → `pom.xml` → mapping → flow → test.
5. Spec version status — local cache first:
   `find ~/.m2/repository -ipath "*<spec.name>*" -iname "*oas*.zip"` — present at the referenced version = resolvable, stop asking.
   A version already referenced in `pom.xml`/ruleset is presumed published.
6. Local `api/*.yaml` may be a scratch copy (gitignored, APIkit pointing to the Exchange zip). Before editing it, diff it against the cached zip (`python3 -c "import zipfile;…read(name)"`, no extraction) and re-baseline if it lags.

## Never
- Web-search whether a private spec is published (not public information). Ask once or use `anypoint-platform` discovery with a token.
- Bump `spec.version` without a resolvable artifact: either a publish the user confirmed or a local `mvn install:install-file` stub — say which, and reinstall the stub after every spec edit (stale stubs cause false 400s).
- Patch zips in `~/.m2` as an implementation path.
- Rename `http:request doc:name` without updating tests.

## Output
spec name/version, `.m2` status, dependency status, mappings checked, missing flows, drift that blocks build/test.

---
applyTo: "**/src/main/resources/**/*.yaml,**/src/main/resources/**/*.properties,**/src/test/resources/**/*.yaml,**/pom.xml"
description: "Mule property files and pom.xml defaults. Key style comes from house-style-config."
---
# Config and POM — defaults

Key layout, casing, quoting, indentation: `house-style-config.instructions.md` and the file being edited.

- Non-secret shared values (paths, ports, timeouts, retry counts, constants) → common config file.
- Per-environment values → every real environment file of the project (env names from `profile.md`; never assume one naming scheme across projects).
- Test values → test config: blank credentials, mock hosts, deterministic stubs.
- Secrets: referenced as `${secure::key}` (or the project's pattern) and stored only as the workspace's encrypted placeholder. Never invent a value; a missing secret is escalated.
- Keep existing key names; normalizing old names is its own task.
- Run `mule-config-matrix` before and after adding keys: no env file may miss a key the others have unless the reply says why.
- `pom.xml`: never bump a parent, connector or `spec.version` speculatively. A spec version bump needs the artifact resolvable (local `~/.m2` or a confirmed publish).
- Unresolved placeholders, missing env keys and missing test stubs are build blockers.

---
name: mule-config-matrix
description: "Check and update Mule property files across common, per-environment and test configs - missing keys per env, placeholders, secure keys. Use when adding a downstream service, property, credential placeholder, host, path, timeout or test stub, or fixing unresolved ${...}/secure:: errors."
---

# mule-config-matrix

```bash
python3 .github/skills/mule-config-matrix/scripts/check_config_matrix.py <project>
```
Run before and after edits.

1. Inspect the project's real layout (`config/` subfolder or root) and env file names; never assume the workspace dominant set (`profile.md` lists variants).
2. Non-secret shared → common file. Env-specific → every real env file. Test → test file (blank credentials, mock hosts, deterministic stubs).
3. Secrets: workspace encrypted placeholder literal only (from `house-style-config`). Never a real or invented value.
4. New downstream connection: every key the local pattern uses (protocol, host, port, basePath, paths, client id/secret, timeouts) in every env file.
5. Keep existing key names and nesting style.
6. After edits: no env file misses a key the others have, unless the reply says why.

Output: files changed, envs covered, intentional gaps, scanner result.

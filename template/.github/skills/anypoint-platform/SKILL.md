---
name: anypoint-platform
description: "Anypoint Platform work - read-only discovery (orgs, environments, Exchange assets, API Manager instances, policies) with a bearer token from the environment, and dry-run-first, idempotent anypoint-cli-v4/curl automation. Mutations need explicit user approval."
---

# anypoint-platform

## Discovery (read-only, GET only)
```bash
export ANYPOINT_TOKEN=…            # user does this; never paste tokens into chat or files
ANYPOINT_BASE_URL=${ANYPOINT_BASE_URL:-https://anypoint.mulesoft.com}   # EU: https://eu1.anypoint.mulesoft.com (see profile.md)
bash .github/skills/anypoint-platform/scripts/anypoint_discover.sh whoami
```
Subcommands and endpoints: `references/anypoint-platform-apis.md` — verify against current MuleSoft docs before relying on a path. Cite evidence as group/asset/version or API instance ID + environment. Redact `Authorization` in anything shown. Never store the token anywhere.

## Automation (scripts that change the platform)
1. Verify CLI v4 / API syntax in official docs first (flags change between versions); `references/anypoint-cli-alerts.md` for alerts.
2. Every script: `--dry-run` default, idempotency check, target summary, explicit flag to mutate, rate-limit backoff, `--output json` + `jq`, `curl --fail-with-body` with timeouts.
3. Credentials from env vars only; no secrets in scripts, logs, README.
4. Validate: `bash -n`, `shellcheck` if installed (say if not), a dry-run example.
5. Any create/update/delete/deploy/promote/enable/disable runs only after the user reviewed the dry-run and approved.

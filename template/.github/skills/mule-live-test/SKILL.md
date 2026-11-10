---
name: mule-live-test
description: "On request only - exercise a Mule app the user deployed themselves (BASE_URL supplied) with real HTTP requests derived from the API contract, and inspect the app log for silent errors. Never deploys, starts or edits anything."
---

# mule-live-test

Inputs from the user: `BASE_URL`, optional `APP_LOG` path, project. Credentials only from environment variables (`AUTH_USER`, `AUTH_PASS`, tokens) — never typed into files or replies.

## Rules
- Request shapes come from the spec, ruleset or requirement only — never invent fields.
- Read-only: no source edits, no deploy/restart.
- Auth-protected projects (ruleset: security filter) → send auth on every non-health call.

## Scenarios per new endpoint
| # | Scenario | Verify |
|---|---|---|
| T1 | happy path, all required fields | status, body shape vs schema, no ERROR in log |
| T2 | missing required field | router 400 |
| T3 | downstream failure (if reproducible) | error shape; retry evidence only for system layer |
| T4 | health endpoint | expected body |
| T5 | a previously working endpoint | unchanged |
| T6 | no/invalid auth (protected projects) | 401/403 |
| T7 | timing of T1 (`curl -w "%{time_total}"`) | under the configured response timeout, else 2 s |

Bug fix: the exact reproduction request first, then T4/T5.

```bash
curl -s -w "\nHTTP:%{http_code} TIME:%{time_total}s" -X POST "$BASE_URL/<base-path>/<resource>" \
  -H "Content-Type: application/json" -H "X-Correlation-Id: live-test-1" -u "$AUTH_USER:$AUTH_PASS" -d @request.json
tail -200 "$APP_LOG" | grep -E "ERROR|WARN|RETRY|at org\.mule"
```
A 2xx with an ERROR in the log is a failure.

Report: table `# | request | expected | actual | pass/fail`, log findings, timing. Redact auth headers in anything shown.

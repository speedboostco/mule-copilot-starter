# Anypoint CLI Alert Reference

Use this when editing alert automation scripts.

## Official Sources

- Anypoint CLI 4 API Manager commands: https://docs.mulesoft.com/anypoint-cli/latest/api-mgr
- Anypoint CLI 4 differences: https://docs.mulesoft.com/anypoint-cli/latest/diff-earlier-ver
- Runtime Manager CLI: https://docs.mulesoft.com/runtime-manager/runtime-manager-cli
- Monitoring alerts: https://docs.mulesoft.com/monitoring/alerts-us-eu

## API Manager Alerts

Command:

```bash
anypoint-cli-v4 api-mgr:alert:add <apiInstanceId> <name> [flags]
anypoint-cli-v4 api-mgr:alert:list <apiInstanceId> --output json
```

Important CLI 4 alert flags:

- `--type`: `request-count`, `response-code`, `policy-violation`, `response-time`
- `--operator`: `gt`, `lt`, `eq`
- `--severity`: `Info`, `Warning`, `Critical`
- `--threshold`: numeric threshold
- `--periods`: number of consecutive periods
- `--duration`: condition occurrence duration
- `--durationUnit`: `days`, `hours`, `minutes`
- `--responseCode`: repeat for each response code
- `--email`: repeat for each email recipient
- `--enabled`: include to enable the alert
- `--output json`: use for automation

Do not assume legacy CLI 3 syntax or values work in CLI 4.

## Runtime Manager Alerts

Use `runtime-mgr:standalone-alert:*` commands only for locally deployed applications managed by Runtime Manager. Do not use API Manager alert commands for runtime alerts.

## Validation Notes

- Alert names are the safest duplicate-detection key available to simple scripts; treat them as stable identifiers.
- If more than one existing alert with the target name exists, skip and report the duplicate state.
- Prefer dry-run output that prints shell-escaped command arrays rather than reconstructing a command string.

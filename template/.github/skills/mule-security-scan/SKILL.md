---
name: mule-security-scan
description: "Ad hoc SCA (OWASP Dependency-Check) and SAST (Semgrep) scan of a Mule project plus a credential/placeholder grep, without editing the POM. Use when a dependency changed, for the \"no new critical/high vulnerabilities\" gate row, or when asked for a security scan."
---

# mule-security-scan

```bash
bash .github/skills/mule-security-scan/scripts/run_security_scan.sh <project> [output-dir]
```
Runs dependency-check as an ad hoc Maven goal (first run downloads the NVD feed — slow, may need an API key), Semgrep `p/secrets` + `p/owasp-top-ten` if installed, and always a placeholder/credential grep.

- Read the report files, not the console tail. Report CVE id, CVSS, artifact.
- CVSS ≥ 7 or a medium/high-confidence OWASP hit → blocking finding.
- A tool that did not run (no network, not installed, non-Maven target) is reported as not run — never as clean.
- Opt-in tooling; not a default gate unless the workspace decides so.

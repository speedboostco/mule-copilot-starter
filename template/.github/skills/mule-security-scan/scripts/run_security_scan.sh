#!/usr/bin/env bash
# Ad hoc SCA + SAST scan for a Mule project.
# Runs entirely from plugin coordinates on the CLI — never edits pom.xml or
# the parent POM, so it is safe to run against any project without approval
# to change shared build config.
#
# Usage: run_security_scan.sh <project-dir> [output-dir]

set -uo pipefail

PROJECT_DIR="${1:?usage: run_security_scan.sh <project-dir> [output-dir]}"
OUT_DIR="${2:-${PROJECT_DIR}/target/security-scan}"
mkdir -p "$OUT_DIR"

PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
echo "== Mule Security Scan =="
echo "Project: $PROJECT_DIR"
echo "Output:  $OUT_DIR"
echo

# 1. SCA: OWASP Dependency-Check as an ad hoc Maven goal.
# Requires network access to the NVD feed on first run (can be slow / needs
# an NVD API key for reasonable speed) - report this rather than retrying
# silently if it times out or fails to download the feed.
echo "-- SCA: OWASP Dependency-Check --"
(
  cd "$PROJECT_DIR" && \
  mvn org.owasp:dependency-check-maven:9.2.0:check \
    -DfailBuildOnCVSS=11 \
    -Dformats=JSON,HTML \
    -DoutputDirectory="$OUT_DIR/dependency-check"
) > "$OUT_DIR/dependency-check.log" 2>&1
SCA_EXIT=$?
if [ $SCA_EXIT -eq 0 ]; then
  echo "dependency-check completed. Report: $OUT_DIR/dependency-check/dependency-check-report.html"
else
  echo "dependency-check FAILED or could not reach the NVD feed (exit $SCA_EXIT)."
  echo "See $OUT_DIR/dependency-check.log — do not report a clean SCA result when this failed."
fi
echo

# 2. SAST: Semgrep, if installed locally. Never phones home (--metrics=off).
echo "-- SAST: Semgrep --"
if command -v semgrep >/dev/null 2>&1; then
  semgrep scan "$PROJECT_DIR" \
    --config p/secrets \
    --config p/owasp-top-ten \
    --metrics=off \
    --exclude target \
    --json --output "$OUT_DIR/semgrep.json" \
    --sarif --sarif-output "$OUT_DIR/semgrep.sarif" \
    2> "$OUT_DIR/semgrep.log"
  SEMGREP_EXIT=$?
  if [ $SEMGREP_EXIT -eq 0 ] || [ $SEMGREP_EXIT -eq 1 ]; then
    FINDINGS=$(python3 -c "import json,sys; d=json.load(open('$OUT_DIR/semgrep.json')); print(len(d.get('results', [])))" 2>/dev/null || echo "unknown")
    echo "semgrep completed. Findings: $FINDINGS. Report: $OUT_DIR/semgrep.json"
  else
    echo "semgrep FAILED (exit $SEMGREP_EXIT). See $OUT_DIR/semgrep.log — do not report a clean SAST result."
  fi
else
  echo "semgrep is not installed locally. Falling back to the manual credential grep below."
  echo "To enable real SAST coverage: https://semgrep.dev/docs/getting-started/ (brew install semgrep)"
fi
echo

# 3. Fallback / always-on: hardcoded credential and placeholder sanity check.
# This is the manual check the quality gate already
# describe as the approximation when no SCA/SAST tool is configured — keep
# it running even when semgrep/dependency-check are available, since it
# catches the specific "![]" placeholder convention this workspace relies on.
echo "-- Fallback: credential / placeholder sanity check --"
CRED_HITS=$(grep -RInE "(password|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"$]{6,}['\"]" \
  --include="*.yaml" --include="*.yml" --include="*.xml" --include="*.dwl" --include="*.properties" \
  --exclude-dir=target "$PROJECT_DIR" 2>/dev/null | grep -v '!\[' || true)
if [ -n "$CRED_HITS" ]; then
  echo "POTENTIAL HARDCODED CREDENTIALS FOUND:"
  echo "$CRED_HITS"
else
  echo "No plaintext-looking credential assignments found outside the '![...]' encrypted placeholder convention."
fi

echo
echo "== Scan complete. Read the individual reports before declaring the Definition of Done security rows clean. =="

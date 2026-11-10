#!/usr/bin/env bash
# Ad hoc fmt/validate/lint/security scan for a *-terraform project.
# Never runs plan/apply/destroy or touches remote state - safe to run
# against any project without approval to change real infrastructure.
#
# Usage: run_terraform_scan.sh <project-dir> [env]

set -uo pipefail

PROJECT_DIR="${1:?usage: run_terraform_scan.sh <project-dir> [env]}"
ENV_NAME="${2:-nprd}"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

echo "== Terraform Quality Gate =="
echo "Project: $PROJECT_DIR"
echo "Env:     $ENV_NAME (informational only - no plan is run by this script)"
echo

cd "$PROJECT_DIR" || exit 1

INIT_LOG="$(mktemp -t terraform-quality-gate-init)"

# 1. Format check - non-mutating, shows the diff instead of writing it.
echo "-- Format: terraform fmt -check --"
if terraform fmt -check -recursive -diff; then
  echo "fmt: no drift."
else
  echo "fmt: DRIFT FOUND (see diff above). Run 'terraform fmt -recursive' to fix, do not hand-edit whitespace."
fi
echo

# 2. Validate - init without touching the remote backend/state.
echo "-- Validate: terraform init -backend=false + terraform validate --"
if terraform init -backend=false -input=false -lockfile=readonly > "$INIT_LOG" 2>&1; then
  if terraform validate; then
    echo "validate: OK."
  else
    echo "validate: FAILED. See output above."
  fi
else
  echo "init -backend=false FAILED (likely missing provider network access, or .terraform.lock.hcl is missing a hash for this platform - never regenerate the lock file to fix that, ask the user). See $INIT_LOG."
  echo "Skipping 'terraform validate' - it requires a successful init first."
fi
echo

# 3. Lint - tflint, if installed.
echo "-- Lint: tflint --"
if command -v tflint >/dev/null 2>&1; then
  tflint --recursive
  TFLINT_EXIT=$?
  if [ $TFLINT_EXIT -eq 0 ]; then
    echo "tflint: no issues."
  else
    echo "tflint: issues found (exit $TFLINT_EXIT) - see output above. Errors are blocking; warnings are not."
  fi
else
  echo "tflint is not installed locally. Falling back to manual Style Guide review for this category."
  echo "To enable: brew install tflint (https://developer.hashicorp.com/terraform/language/style)"
fi
echo

# 4. Security scan - trivy config (current successor to the archived tfsec),
# falling back to checkov if trivy isn't installed either.
echo "-- Security scan: trivy config / checkov --"
if command -v trivy >/dev/null 2>&1; then
  trivy config --severity HIGH,CRITICAL .
  echo "trivy config completed. All former tfsec check IDs (AVD-*) carry over unchanged."
elif command -v checkov >/dev/null 2>&1; then
  checkov -d . --compact
  echo "checkov completed."
else
  echo "Neither trivy nor checkov is installed locally. Falling back to the credential grep below only."
  echo "To enable: brew install trivy (https://aquasecurity.github.io/trivy/) or pip install checkov"
fi
echo

# 5. Fallback / always-on: hardcoded credential and placeholder sanity check.
# Secrets in this codebase should only ever appear as TF_VAR_*/ARM_* variable
# references, never as literal values in .tf/.tfvars.
echo "-- Fallback: credential / placeholder sanity check --"
CRED_HITS=$(grep -RInE "(password|secret|token|client_secret|activation_data|license_base64)\s*=\s*\"[^\"$][^\"]{5,}\"" \
  --include="*.tf" --include="*.tfvars" \
  --exclude-dir=.terraform "$PROJECT_DIR" 2>/dev/null | grep -vE '\$\{?(TF_VAR_|var\.)' || true)
if [ -n "$CRED_HITS" ]; then
  echo "POTENTIAL HARDCODED SECRETS FOUND:"
  echo "$CRED_HITS"
else
  echo "No plaintext-looking secret assignments found outside TF_VAR_*/var.* references."
fi

echo
echo "== Scan complete. This script never ran plan/apply/destroy or touched remote state. =="
echo "== Read the individual tool output above before declaring the Definition of Done rows clean. =="

# Terraform Quality Gate

## Sources

- HashiCorp Terraform style guide: https://developer.hashicorp.com/terraform/language/style
- HashiCorp standard module structure: https://developer.hashicorp.com/terraform/language/modules/develop/structure
- HashiCorp module creation pattern: https://developer.hashicorp.com/terraform/tutorials/modules/pattern-module-creation
- HashiCorp native test framework (`terraform test`, `.tftest.hcl`, GA since 1.6): https://developer.hashicorp.com/terraform/language/tests
- HashiCorp state locking / remote backends: https://developer.hashicorp.com/terraform/language/state/locking
- Terraform Registry (provider docs, e.g. `azurerm`): https://registry.terraform.io
- Trivy IaC/config scanning (current successor to the archived `tfsec` — all `tfsec` check IDs carry over unchanged): https://aquasecurity.github.io/trivy/latest/docs/coverage/iac/terraform/
- OWASP Code Review Guide: https://owasp.org/www-project-code-review-guide/

## Review Checklist

- Scope: changed files belong to the targeted `*-terraform` project. No unrelated formatting or cross-project edits.
- Naming: `<type-abbrev>-${resource_prefix}-<NN>` convention followed exactly for any new resource; `locals` block pattern and `var.tags` propagation match the surrounding module.
- Module boundaries: a new significant piece of infrastructure is its own module under `modules/`, not folded into an unrelated existing one.
- Variables/outputs: every `variable` has `type` + `description`; every `output` has `description`; every secret-carrying one is `sensitive = true`.
- Provider pinning: `required_providers` versions remain exact-pinned; any version bump is deliberate and called out with the `.terraform.lock.hcl` diff reviewed.
- State/backend: no hardcoded backend `key`, no two environments sharing a state key, no hand-edited `.tfstate*`/`.terraform.lock.hcl`.
- Secrets: no plaintext secret in any `.tf`/`.tfvars` file, plan output, or the response itself — only `TF_VAR_*`/`ARM_*` environment-variable references.
- Plan review: every add/change/destroy in the plan diff is accounted for; any destroy or forced replacement is explicitly called out and justified.
- Mutation gate: `apply`/`destroy`/state surgery is never proposed as already-run — only as a withheld command pending the user's explicit approval.
- Comments: no comments added to `.tf`/`.tfvars` files (workspace-wide rule).

## Validation Commands

Run from the target project directory:

```bash
terraform fmt -check -recursive -diff
terraform init -backend=false -input=false
terraform validate
```

Lint/security (only if installed — state explicitly when not):

```bash
tflint --recursive
trivy config .
checkov -d .
```

Plan (only with real Azure credentials available; never run apply without a saved plan the user has reviewed):

```bash
terraform init -upgrade -reconfigure -var-file=envs/<env>/defaults.tfvars -backend-config="key=terraform-state-<env>.tfstate"
terraform plan -input=false -var-file=envs/<env>/defaults.tfvars -out=tfplan
```

## Automated Test Ladder (Terraform Mapping)

Twelve generic automated-test categories mapped onto the workspace Terraform projects. Run this mapping for every infrastructure change before marking the run done. Where no tool exists or credentials aren't available, say so explicitly — do not report a category as passing when it was only approximated or is not applicable.

| # | Category | Terraform equivalent | Command / mechanism | Status |
|---|---|---|---|---|
| 1 | Format check | HCL canonical formatting | `terraform fmt -check -recursive -diff` | Enforced |
| 2 | Lint | Provider-aware static analysis (unused vars, deprecated arguments, `azurerm`-specific rules) | `tflint --recursive` when installed; otherwise manual review against the Style Guide | Enforced when `tflint` installed; Approximated (manual) otherwise |
| 3 | Compile / type-check | HCL parses and resolves against provider schemas | `terraform validate` (after `terraform init -backend=false`) | Enforced |
| 4 | Unit tests | Native HCL test framework (`.tftest.hcl`, `terraform test`) | Check for `*.tftest.hcl`; when none exist this is a real gap, not an approximated pass | N/A — no test files exist; flag as a gap, do not fabricate a pass |
| 5 | Property-based tests | No PBT framework applies to HCL | N/A | N/A |
| 6 | API schema tests | No externally-consumed API contract at this layer | N/A | N/A |
| 7 | Integration tests | Plan against real backend/provider state | `terraform plan` with real `ARM_*` credentials and backend access | Enforced only when credentials are available; N/A otherwise — state which case applies |
| 8 | Contract tests | Root module ↔ child module variable/output contract | Manual review: every module input the root passes matches the module's declared `variables.tf`; every root reference to a module output matches `outputs.tf` | Enforced (manual) |
| 9 | Security scans | Misconfiguration/secret scanning for HCL | `trivy config .` (current successor to the archived `tfsec`) and/or `checkov -d .` when installed; otherwise the credential/placeholder grep fallback | Enforced when a scanner is installed and run; Approximated (grep-only) otherwise — state which case applies |
| 10 | Mutation tests | No mutation-testing tool applies to HCL | N/A | N/A |
| 11 | E2E critical paths | Real `apply` against a live environment, then a smoke check of the provisioned resource | Never run automatically — `apply` always requires the user's explicit, plan-reviewed approval ; N/A for any change that stops at `plan` | N/A by default / Enforced only on explicit user-approved apply |
| 12 | Performance smoke test | Not applicable to infrastructure provisioning in the same sense as a request-latency check | N/A | N/A |

## Definition of Done Gate

Blocks a Terraform change from being marked done until every applicable item below is true. Explicitly mark inapplicable items as `N/A` rather than omitting them.

| Criterion | How it's checked in this pipeline |
|---|---|
| Formatting is canonical | `terraform fmt -check -recursive -diff` produces no diff |
| Configuration is syntactically/semantically valid | `terraform validate` passes after `terraform init -backend=false` |
| No unreviewed destroys | Every `plan` diff was read in full; every destroy/forced-replacement is named and justified in the response |
| No new critical/high misconfigurations | `trivy config`/`checkov` run and reported when installed; grep-only fallback stated explicitly otherwise — never fabricate a scan result |
| No secrets | No plaintext credential/token value in any `.tf`/`.tfvars` file, plan summary, or response; only `TF_VAR_*`/`ARM_*` references |
| Naming/module conventions followed | Resource naming, module boundaries, `variables.tf`/`outputs.tf` documentation match the existing repo pattern |
| Provider pinning intact | No silent provider version bump; any deliberate bump has its `.terraform.lock.hcl` diff reviewed and called out |
| State handled safely | No hardcoded backend key, no shared state key across environments, no hand-edited state/lock files |
| Apply/destroy/state surgery withheld | Not run without the user's explicit approval of a reviewed plan; the command is reported as withheld, not executed, unless approval was actually given |
| Acceptance criteria not weakened by the agent itself | No existing module contract narrowed/broadened, and no `.tftest.hcl` (if any exist) modified to force a pass |

If any enforced (non-`N/A`) criterion fails, report it as a blocking finding. The run is not marked done until it is resolved or the user explicitly accepts the risk in writing.

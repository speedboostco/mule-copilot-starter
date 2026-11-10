---
name: terraform-gate
description: "Terraform/HCL change workflow and quality gate - fmt, validate, tflint/trivy/checkov when installed, secret grep, saved-plan review. apply/destroy/state surgery only after user approval of a reviewed plan. Use for any .tf/.tfvars change or Terraform review."
---

# terraform-gate

```bash
bash .github/skills/terraform-gate/scripts/run_terraform_scan.sh <tf-project> [env]
```
Runs `fmt -check`, `init -backend=false` + `validate`, `tflint`/`trivy config`/`checkov` when installed, and a secret grep. `plan` is separate (needs real credentials and backend):
```bash
terraform plan -input=false -var-file=<env var-file per project layout> -out=tfplan
terraform show -no-color tfplan
```

## Workflow
1. Read the target module and root wiring; follow `terraform.instructions.md`.
2. Implement; run the scan; run `plan` when credentials exist, else say plan is pending.
3. Review every add/change/destroy/replace in the saved plan; name and justify each destroy/replace.
4. `init` must not mutate the committed lock file as a side effect (use `-lockfile=readonly` where supported); a checksum mismatch is surfaced, not silently regenerated.
5. Stop at a clean, reviewed plan. `apply`/`destroy`/state surgery only after explicit user approval of that plan.

Ladder and DoD: `references/terraform-quality-gate.md` (paths there are examples; use the project's layout). A scanner that is not installed is reported as not run, never as clean.

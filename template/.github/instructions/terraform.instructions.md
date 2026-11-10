---
applyTo: "**/*.tf,**/*.tfvars,**/*.tftest.hcl"
description: "Terraform/HCL defaults. Gate and commands in the terraform-gate skill."
---
# Terraform — defaults

- Read the target module first; copy its naming (`locals`, resource name pattern, numbering, tag propagation). No parallel naming scheme.
- New infrastructure → new module unless it is a trivial addition tightly coupled to an existing one.
- Every `variable` has `type` + `description`; secrets `sensitive = true`. Every `output` has `description`; secret-carrying outputs `sensitive = true`.
- Provider versions stay pinned as they are; a bump is a separate, called-out change with the full lock-file diff reviewed.
- Secrets only via environment (`TF_VAR_*`, provider auth vars); never in `.tfvars`, defaults or committed files.
- Never hand-edit `*.tfstate*`, `.terraform/`, or `.terraform.lock.hcl`.
- Always `fmt` → `validate` → `plan -out` before calling a change ready; review every add/change/destroy in the saved plan.
- `apply`, `destroy`, `state rm|mv|push`, `import`, `force-unlock`, `workspace delete`: only after the user approves a reviewed plan.
- Changes to shared core modules or backend/provider config are called out explicitly.
- No comments in `.tf`/`.tfvars` unless house style shows the module uses them.

---
name: premortem
description: "Adversarial stress test of a hard-to-reverse decision or risky change - pre-mortem for architecture/reuse decisions, red-team for security-sensitive or shared-component changes. Optional second pass, not a default."
---

# premortem

Use for: a reuse/extend/create or layer decision that is hard to undo; a change to a shared library, global error handler, auth/PII/secrets flow, or an irreversible backend operation; an explicit "stress-test this". Skip for routine single-endpoint changes and for decisions the user already accepted.

1. **Steelman** the plan: what must be true for it to be right. Confirm it matches the proposal.
2. **Mode**: pre-mortem ("six months later this caused an incident — why?") or red-team ("hostile input/actor — what breaks?").
3. **3–5 concrete challenges**, each naming a mechanism in this workspace: env-name drift between config sets, shared DWL regression across consumers, retry storm on a rate-limited backend, trusted header across layers, inter-layer field casing drift, placeholder secrets reaching runtime.
4. **Mitigation** per surviving challenge: a test, a scoped rollout, a ruleset note, a different call.
5. **Verdict**: proceed / proceed with mitigations / change the call — and what evidence would flip it.

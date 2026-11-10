---
name: verify-before-done
description: "Evidence before claims. Run the command that proves a build, test, fix or behavior claim in this session and read its full output before reporting it. Use before saying done, passing, fixed or working, and before every handoff."
---

# verify-before-done

**No completion claim without fresh evidence from this session.**

1. Name the command that proves the claim.
2. Run it fully (not a subset, not a dry run for a real-result claim).
3. Read exit code, counts, failures — not just the tail.
4. Report the claim with the evidence, or the real status if it does not hold.

| Claim | Evidence | Not evidence |
|---|---|---|
| tests pass | full suite output, 0 failures | earlier run, "assertions look right" |
| builds | build command exit 0, fresh | tests passing |
| XML valid | `xmllint --noout` per changed file | eyeballing |
| bug fixed | original reproduction now passes | code changed |
| coverage held | report % before/after | "new tests must help" |
| subagent done | its diff and tool output | its summary |
| running instance healthy | health call + log without ERROR (only on request) | build success |

Cannot run it (no credential, no runtime) → say so plainly; never assert the claim anyway.
Red flags: "should work now", "probably", satisfaction before running anything, reusing old output after files changed.

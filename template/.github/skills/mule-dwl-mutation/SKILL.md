---
name: mule-dwl-mutation
description: "Mutation-test DataWeave logic - flips comparisons, booleans, defaults and safe navigation one at a time and re-runs the MUnit test to see which mutants survive. Use when changed DWL has conditional logic and a real mutation signal is wanted."
---

# mule-dwl-mutation

```bash
MULE_TEST_KEY=<mule.key from profile.md> python3 .github/skills/mule-dwl-mutation/scripts/mutate_dwl.py <project> src/main/resources/<dwl-dir>/<file>.dwl --munit-test <suite>.xml#<test>
```
Confirms the baseline passes, applies one operator at a time, restores the file after each run, reports killed vs survived.

- Survived mutant = the suite would pass with that logic wrong → one targeted assertion (Test Necessity Gate still applies).
- Skip pure field mappings (nothing to mutate). Real custom Java → PIT as an ad hoc goal instead.
- Never leave a mutated file behind: check `git diff` on the DWL after the run.

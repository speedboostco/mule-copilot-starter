---
name: git-task-branch
description: "On request only - create or reuse a task branch and make a local commit for finished work, named after a resolved task ID, in the workspace commit style. Never pushes. Use when the user explicitly asks for a branch and/or commit."
---

# git-task-branch

Hard gate: **no resolved task ID → no `checkout -b`, `add`, or `commit`.** Read-only git is always fine.

## Task ID
User text → ticket screenshot/PDF (work-item URL, `KEY-123`, numeric ID) → ask once. Never invent. Sanitize: lowercase `[a-z0-9-]`.

## Steps (inside one project repo; never at a non-repo workspace root)
1. `git rev-parse --is-inside-work-tree`; `git status --porcelain` (uncommitted changes are expected — they are the task).
2. `git fetch origin <base>` — base branch and remote host from `profile.md`/`house-style`. Fetch fails → use local base or `HEAD`, report it.
3. Branch `<prefix>/<id>` using the workspace prefixes (house style; default `feature/` for features, `bugfix/` for bugs). Exists locally → check out; only on origin → track it; else create from base. Report name, base, base commit.
4. Commit (only if asked): stage explicit paths of this task only (never `add -A`/`.`). Message in the workspace commit style (house style samples), task ID included. No AI trailers or mentions. No `--amend`, `--no-verify`.
5. `git log -1 --stat`. State: hash, subject, files, **not pushed**.

## Never
`push` (any form), `reset`, `clean`, `rebase`, `checkout -- <path>`/`checkout .`. The remote may not be GitHub (check `git remote -v`); do not assume `gh` works.

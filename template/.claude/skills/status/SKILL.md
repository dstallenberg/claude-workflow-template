---
name: status
description: Show milestone progress, in-flight worktrees, and uncommitted work across parallel sessions.
disable-model-invocation: true
allowed-tools:
  - Bash(git worktree list:*)
  - Bash(git status:*)
  - Bash(git log:*)
  - Bash(git branch:*)
---

# Project Status

Live state, already gathered:

**Worktrees**
```
!`git worktree list`
```

**Working tree (this checkout)**
```
!`git status --short --branch`
```

**Recent commits (all branches)**
```
!`git log --oneline --decorate -15 --all`
```

## What to report

Read `REQUIREMENTS.md` and every file in `milestones/` (plus `TECH_DEBT.md` if it exists), then give the user a compact picture:

1. **Milestones** — for the current milestone: `N/M` subtasks done and the titles of the open ones. One line per remaining milestone after that (name + subtask count).
2. **In flight** — for each worktree other than the main checkout: its path, branch, and which subtask it looks like it's carrying (match the `worktree-<name>` branch against subtask IDs, and check its commits above). Flag any worktree whose branch has commits that aren't on the main branch — those need a `git merge worktree-<name>`.
3. **Uncommitted work** — what's dirty in this checkout, and whether it's code (should have been committed by `/dev` or `/refactor`) or docs (expected to sit uncommitted).
4. **Tech debt** — open item count from `TECH_DEBT.md`, if the file exists.
5. **Next** — the single next action you'd recommend: which subtask to run `/dev` on, a worktree to merge, or a milestone that needs `/requirements` first.

Keep it under ~25 lines. Don't edit any files, don't commit, don't start work.

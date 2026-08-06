---
name: refactor
description: Execute exactly one open item from TECH_DEBT.md — surgical, tested, scoped, committed.
argument-hint: "[item number or short title]"
disable-model-invocation: true
allowed-tools:
  - EnterWorktree
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Bash(git log:*)
  - Bash(git worktree list:*)
---

# Refactor

You are picking exactly **one** open `[ ]` item from `TECH_DEBT.md` at the repo root and doing it. Surgical, tested, scoped strictly to that item.

## Isolation

Before touching code: if this session is not already in a git worktree (`git worktree list`, or a cwd under `.claude/worktrees/`), call `EnterWorktree` with a short kebab-case name for the item (e.g. `extract-hash-util`). Parallel sessions must not share a checkout. A fresh worktree has no build artifacts — install/build as the project requires before running tests.

## Startup

1. Read `TECH_DEBT.md` at the repo root. Parse every `- [ ]` line, preserving its section header.
   - If `TECH_DEBT.md` doesn't exist or has zero open items, stop and tell the user to run `/refactor-investigation` first.
2. Read `CLAUDE.md` for project conventions.

## Selection

If the argument ($ARGUMENTS) already identifies an item unambiguously, use it. Otherwise present the open items to the user as a numbered list grouped by section, and ask with `AskUserQuestion` using the section + a short title per item. If there are more than 4 items in a single section, group sections together in the question and ask the user to identify the item by its number.

Wait for the user to pick exactly one. Don't auto-pick. Don't bundle.

## Scoping

Before touching code:

1. Read every file referenced by the chosen item's `file:line` paths.
2. Read the surrounding context (the whole function, the whole struct/class definition) — not just the cited lines.
3. State a 3–5 line plan: what files change, the rough approach, what tests cover the area.
4. If the item's "Why deferred" note flags a constraint (e.g. "wire format sensitive", "carefully sequenced with M-X"), call it out explicitly in your plan.
5. If the refactor requires a design call you can't make alone (e.g. "should this break be coordinated with milestone X?"), STOP and ask via `AskUserQuestion`. Don't guess.

## Implement

- Minimal, surgical edits. Preserve external behavior.
- Don't expand scope. If the item says "extract module X", don't also rename helpers or tweak nearby imports.
- Follow the conventions in `CLAUDE.md` (code style, naming, error handling, test patterns).
- Don't add features, don't refactor neighboring code, don't introduce abstractions beyond what the item describes.
- Don't add error handling for impossible scenarios. Don't add comments explaining obvious code.
- A `PostToolUse` hook formats each edited file and reports lint failures back to you — fix those as you go.

<!-- INJECT:CODE_STYLE -->

## Verify

Run these in order. Stop and diagnose if any fail — don't suppress failures.

<!-- INJECT:BUILD_COMMANDS -->

After the standard build/test pass:

- If the item touches gameplay / multi-step flows / state machines, run the relevant regression scenarios for the area (project-specific — see `CLAUDE.md` for the runner command if one exists).
- If the item is visual (rendering, UI), generate the relevant preview artifact and inspect it. `CLAUDE.md` lists which script applies to which area.

If the chosen item turns out to be wrong, no longer relevant, or already fixed: edit the bullet with a `~~strikethrough~~` + a `**Status:** <note>` line explaining why, mark it `- [x]`, and exit cleanly. Don't silently delete. In that case no code changed, so don't commit — tell the user `TECH_DEBT.md` is modified and let them fold it into their next commit.

## Close the item

Edit `TECH_DEBT.md` in place:

- Change `- [ ]` → `- [x]`.
- Append `✅ <today's date> — <one-line note about how it was resolved>`.
  - Date format: `YYYY-MM-DD`. Use the date from the environment context.
  - Note should describe the actual change (e.g. "extracted to src/util/hash.ts, callers updated"), not just "done".
- If this empties a section, move the resolved bullet into the `## Resolved` block at the bottom of the file.

## Commit

Once the build/test gate passes and the item is closed:

- `git add` only the files you touched, plus `TECH_DEBT.md`. Never `git add -A`.
- One commit: `refactor: <what changed>` — e.g. `refactor: extract hash helpers into src/util/hash.ts`.
- The code change and the `TECH_DEBT.md` `[x]` line go in the **same** commit.
- **Do not push.** No `git push`, no PR, no `git reset --hard`, no `git checkout` to revert. The user reviews and pushes.

## Report

In 2–3 sentences:
- What changed (key `file:line` or new module).
- What tests/scenarios ran and the count that passed.
- The commit subject, and — if you are in a worktree — the merge-back line: `git merge worktree-<name>` (run from the main checkout).
- What the user should eyeball (e.g. "preview is at `assets/foo_preview.png`").

## Hard rules

- One task per invocation. If the user wants two, they run `/refactor` twice.
- Don't run destructive git commands.
- Don't expand scope mid-implementation. If you find a related issue, note it for `/refactor-investigation` to pick up next time — don't fix it now.
- If verification fails for a reason outside the chosen item's scope (e.g. a pre-existing flaky test), stop and report to the user. Don't paper over it, and don't commit.

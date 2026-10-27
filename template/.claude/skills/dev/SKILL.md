---
name: dev
description: Implement one milestone subtask end to end — isolate, plan, code, test, update the milestone file, commit.
argument-hint: "[subtask-id | free-text description]"
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

# Developer Agent

<!-- INJECT:ROLE -->

## Argument

$ARGUMENTS

The argument is a subtask ID (e.g., `M-FIRST.1`, `M-FIRST.3`) or a free-text description of what to implement. If it is empty, determine the next unfinished subtask from the current milestone.

## Isolation

Do this before reading anything else.

- If this session is already in a git worktree (`git worktree list` shows the current directory as a linked worktree, or the cwd is under `.claude/worktrees/`), stay where you are.
- Otherwise call `EnterWorktree` with a name derived from the subtask — `M-FIRST-1` for subtask `M-FIRST.1`, or a short kebab-case slug for a free-text task. This keeps parallel sessions from editing the same files.
- The worktree lands at `.claude/worktrees/<name>/` on branch `worktree-<name>`, branched from the current `HEAD`. A fresh worktree has no build artifacts or dependencies — install/build as the project requires before running tests.

## Startup

1. Read `REQUIREMENTS.md` — find the target milestone in the index table, note its status
2. Read the milestone file `milestones/M-NAME.md` — find the target subtask, understand its full description, dependencies, and resolved design questions in the same file
3. Read `CLAUDE.md` — internalize project conventions, architecture, and file structure
4. Read the project memory (`MEMORY.md` in the project's memory directory, if one exists) and any linked reference files for implementation context
5. Read the relevant source files you'll be modifying — understand existing code before writing new code
6. Check the `## Open Questions (Resolved)` section in the milestone file — if your subtask has unresolved questions that would affect implementation, **stop and ask the user** before writing code

## Implementation Rules

### Planning
- Before writing code, briefly state your plan: what files you'll modify/create, what structs/systems you'll add, and how they integrate with existing code
- If the subtask is large, break it into steps and implement incrementally, testing between steps
- If you discover a design question not covered in REQUIREMENTS.md or Open Questions, ask before guessing

### Code Style (from CLAUDE.md — do not deviate)
<!-- INJECT:CODE_STYLE -->

### Implementation
- Prefer editing existing files over creating new ones. Only create a new file when the feature is clearly a distinct module
- Follow existing patterns — look at how the last similar feature was built before writing a new one
- Don't add features beyond what the subtask specifies
- Don't add error handling for impossible scenarios, don't add comments explaining obvious code, don't add unused abstractions
- A `PostToolUse` hook formats each file you edit and reports lint failures back to you. Fix what it reports as you go — don't leave it for the end
<!-- INJECT:IMPLEMENTATION_WIRING -->

### Testing
<!-- INJECT:TEST_STYLE -->

## Completion

Run the build/test gate first, and fix any failures before going further:

<!-- INJECT:BUILD_COMMANDS -->

Then:

1. **Always update progress in the milestone file** (`milestones/M-NAME.md`):
   - Mark the completed subtask as done: change `- [ ]` to `- [x]`
   - If this was the last subtask in a milestone, also mark the milestone ✅ in the `REQUIREMENTS.md` index table
   - This is mandatory — never skip this step, even if the user doesn't mention it
2. Update `CLAUDE.md` if the change affects:
   - Project structure (new files/modules)
   - Completed milestones (if this was the last subtask in a milestone): one line in `CLAUDE.md`, the full summary appended to `docs/completed-milestones.md`
   - System execution order or component list
3. Update memory files if the implementation revealed important patterns, architectural decisions, or context for future sessions. If a measurement settled or overturned a claim, add or edit its row in `research/FINDINGS.md`
4. **Commit** — the gate has passed and the bookkeeping is done, so land it:
   - `git add` only the files you touched (source + milestone file + any doc you updated). Never `git add -A`
   - Message: `M-NAME.1: <imperative summary>` — e.g. `M-FIRST.1: Add world grid and chunk loader`
   - Code and the milestone checkbox go in the **same** commit
   - **Do not push.** No `git push`, no PR — the user reviews and pushes
   - If the tests or build did not pass, do not commit. Report the failure instead
5. Report: what was built, which files changed, how many tests were added/pass, and the commit subject. If you are in a worktree, end with the merge-back line for the user:
   `git merge worktree-<name>` (run from the main checkout)

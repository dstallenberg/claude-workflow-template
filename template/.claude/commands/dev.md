# Developer Agent

<!-- INJECT:ROLE -->

## Argument

The user may provide a subtask ID (e.g., `M-FIRST.1`, `M-FIRST.3`) or a free-text description of what to implement. If no argument is given, determine the next unfinished subtask from the current milestone.

**Milestone mode**: the argument may also name a whole milestone (e.g. `all of M-FIRST`, `M-FIRST`). Then:
- Work through its unfinished subtasks **in order, one at a time**, on a single branch `dev/<MILESTONE>` in worktree `.claude/worktrees/<MILESTONE>`. Later subtasks build on earlier ones, so stacked branches would only add merge work.
- For **each** subtask, run the full cycle below: plan, implement, checks, independent review rounds, fixes, mark `[x]`, and **one commit per subtask**. Never batch several subtasks into one review or one commit.
- Give the user a short status after each subtask's commit (what was built, review outcome), then continue to the next without waiting.
- Stop and ask only for a genuine design question the milestone doesn't answer, or a choice that is the user's to make (for example how to install a missing toolchain).

## Worktree (always — the user works in parallel)

Never implement in the main checkout. The user and other dev sessions work there and in other worktrees at the same time.

1. **Pick and claim the subtask.** List `git worktree list` and `git branch --list 'dev/*'`. A subtask with an existing `dev/<SUBTASK-ID>` branch is claimed by another session, so pick the next unfinished, unclaimed one (unless the user named one explicitly).
2. **Create the worktree from local `main`** (not `origin/main`, which may lag behind):
   `git worktree add .claude/worktrees/<SUBTASK-ID> -b dev/<SUBTASK-ID> main`, then switch into it with the `EnterWorktree` tool (`path` = that directory). If the session is already inside a worktree for this subtask, keep using it.
3. **Set it up**: install dependencies with the project's install command (see `CLAUDE.md` Build & Run). Gitignored local data (e.g. a `data/` folder) only exists in the main checkout, so if you need it, symlink it: `ln -s <main-checkout>/data data`. Never copy private data into the worktree or commit it.
4. Everything below (reading, coding, review, milestone updates) happens inside the worktree.
5. **Sandbox notes** for a worktree-isolated session:
   - Keep shell commands simple. Long compound commands, `$HOME`, and absolute paths outside the worktree can be refused. Use relative paths for repo files, or put scripts in the scratchpad and run them with the file path as an argument.
   - If the toolchain isn't on the session's PATH yet (for example right after installing it), prefix commands with `env PATH=<toolchain-bin-dir>:/usr/bin:/bin`.
   - Inspect private/real data only with scripts that print **aggregates**: counts, codes, masked shapes. Never print personal or free-text values.

## Startup

1. Read `REQUIREMENTS.md` — find the target milestone in the index table, note its status
2. Read the milestone file `milestones/M-NAME.md` — find the target subtask, understand its full description, dependencies, and resolved design questions in the same file
3. Read `CLAUDE.md` — internalize project conventions, architecture, and file structure
4. Read the project memory (`MEMORY.md` in the project's memory directory) and any linked reference files for implementation context
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
<!-- INJECT:IMPLEMENTATION_WIRING -->

### Testing
<!-- INJECT:TEST_STYLE -->

## Completion

After implementing:
1. Run tests and build — fix any failures:
   <!-- INJECT:BUILD_COMMANDS -->
   - **Real-data check** when the subtask touches import, parsing or data handling and the project has real data available: run it against the real data with all output paths (databases, caches, generated files) pointing into the scratchpad, never into the real data folder, and print aggregates only. Compare the counts with any findings recorded in the milestone.
   - When a metric looks wrong, check the metric before "fixing" the code.
2. **Independent review (mandatory, automatic — don't ask the user first)**. Spawn a fresh `general-purpose` agent with the Agent tool. Never use `fork`, because a fork inherits your context and reasoning and is not unbiased. Don't pass it your plan, summary, or opinion of the code. Give it only:
   - the subtask ID and the path of the milestone file
   - the list of changed/added files (`git status --porcelain`) and the instruction to read the diff itself (`git diff` plus the new files)

   Prompt it to act as a skeptical reviewer who did not write this code, and to check:
   - **Goal fit**: does the change fully deliver the subtask as described, including the relevant resolved decisions in `## Open Questions (Resolved)`? List anything missing, partial, or beyond scope.
   - **Correctness**: bugs, unhandled edge cases (use the milestone's findings and known quirks), and wrong assumptions. Each finding needs a concrete failing input or scenario.
   - **Tests**: do they actually exercise the subtask's requirements (happy path + edge cases), or only the trivial paths? Are any requirements untested?
   - **Project rules** from `CLAUDE.md`: conventions, architecture rules, no private data in fixtures/logs, named constants, logging, error handling, typing.
   - It may run the test/typecheck/lint/build commands, and throwaway scripts in its own scratchpad subfolder (adversarial inputs, real-data checks with aggregates only), but must not edit, create or delete repo files, or run state-changing git commands.
   - Tell it the tooling constraints from the "Sandbox notes" above (PATH prefix, simple commands), so it doesn't waste its run.
   - Output: verdict `PASS` or `CHANGES NEEDED`, then findings ranked `blocking` / `should-fix` / `nit`, each with file:line, the reason and a concrete scenario.

   **Review cycle (automatic, up to 3 rounds per subtask):**
   - After each round, fix every `blocking` and `should-fix` finding, plus the cheap nits, or record a short justification where you disagree. Rerun step 1, and add a test for each fix.
   - Run a **fresh** reviewer (a new agent, never the previous one) whenever the fixes were substantial: a blocking fix, a behaviour change, or a schema change. Stop after `PASS` with only small follow-ups, or after round 3.
   - **After round 3** you still fix what it found, but you may not run a 4th round. Prove those last fixes with tests, including a mutation check where practical (break the fix and confirm a test fails). In the summary and the milestone notes, state clearly that they weren't re-reviewed. Report any remaining disagreements to the user.
   - A finding that needs a decision the user hasn't made: choose the safest reasonable default, record it as a decision in the milestone file, and mention it in the summary so the user can override it.
   - Write decisions and "as built" behaviour into the milestone file under the subtask, so later subtasks and reviewers see them.
3. **Always update progress in the milestone file** (`milestones/M-NAME.md`):
   - Mark the completed subtask as done: change `- [ ]` to `- [x]`
   - If this was the last subtask in a milestone, also mark the milestone ✅ in the `REQUIREMENTS.md` index table
   - This is mandatory — never skip this step, even if the user doesn't mention it
   - **Before marking the milestone ✅, check `main` for requirement changes.** The user may refine requirements on `main` in parallel. Run `git diff <branch-base> main -- milestones/M-NAME.md REQUIREMENTS.md`. Any requirement added for an already-built subtask is open work: add it as a new unchecked subtask, and don't mark the milestone ✅.
4. Update `CLAUDE.md` if the change affects:
   - Project structure (new files/modules)
   - Completed milestones (if this was the last subtask in a milestone)
   - System execution order or component list
5. Update memory files if the implementation revealed important patterns, architectural decisions, or context for future sessions
6. **Commit on the branch** `dev/<SUBTASK-ID>` (or `dev/<MILESTONE>` in milestone mode) in the worktree: one commit per subtask, message per CLAUDE.md, e.g. "M-FIRST.2: Add the parser". When the work is done (after the last subtask in milestone mode), `git rebase main`. Rerun the tests after a rebase.
   - On a conflict in a **doc file only** (the milestone file is typical, because the user edits requirements in parallel): take the branch's version at each step (`git show <commit>:<file> > <file>`, never `git checkout`/`restore`). Afterwards, restore `main`'s additions in a separate, clearly labelled commit, and treat any new requirement as open work (see step 3).
   - On a conflict in code, resolve it if it's trivial, otherwise stop and report.
   - **Do not merge into `main` and do not push** unless the user says so. The user's main checkout may have work in progress. Leave the worktree in place and give the user the merge commands: `git merge --ff-only dev/<ID>` (from the main checkout), then `git worktree remove .claude/worktrees/<ID> && git branch -d dev/<ID>`.
   - If the user asks you to merge: leave the worktree with `ExitWorktree` (`keep`), check that the main checkout is clean, `git merge --ff-only`, remove the worktree and branch, then reinstall dependencies and run the tests on `main`.
7. Briefly summarize what was built, what files changed, how many tests were added/pass, and the review outcome. Cover the rounds, what was fixed, anything fixed after the last allowed round (not re-reviewed), decisions you made on the user's behalf, and any unresolved disagreements.

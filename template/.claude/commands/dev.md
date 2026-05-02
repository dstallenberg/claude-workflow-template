# Developer Agent

<!-- INJECT:ROLE -->

## Argument

The user may provide a subtask ID (e.g., `M-FIRST.1`, `M-FIRST.3`) or a free-text description of what to implement. If no argument is given, determine the next unfinished subtask from the current milestone.

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
2. **Always update progress in the milestone file** (`milestones/M-NAME.md`):
   - Mark the completed subtask as done: change `- [ ]` to `- [x]`
   - If this was the last subtask in a milestone, also mark the milestone ✅ in the `REQUIREMENTS.md` index table
   - This is mandatory — never skip this step, even if the user doesn't mention it
3. Update `CLAUDE.md` if the change affects:
   - Project structure (new files/modules)
   - Completed milestones (if this was the last subtask in a milestone)
   - System execution order or component list
4. Update memory files if the implementation revealed important patterns, architectural decisions, or context for future sessions
5. Briefly summarize what was built, what files changed, and how many tests were added/pass

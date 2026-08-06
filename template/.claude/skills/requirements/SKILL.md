---
name: requirements
description: Interview the user to resolve design gaps in the next milestone and record the decisions in the milestone file.
argument-hint: "[milestone-id]"
disable-model-invocation: true
---

# Requirements Interviewer

<!-- INJECT:ROLE -->

## Argument

$ARGUMENTS

If a milestone ID is given, focus the interview there. Otherwise use the next unstarted milestone.

## Isolation

This session edits docs only — stay in the main checkout. Don't create a worktree.

## Process

### Phase 1: Analysis
1. Read `REQUIREMENTS.md` — the project vision, milestone index table, NFRs, and technical risks
2. Read the milestone file for the **next unstarted milestone** from `milestones/M-NAME.md` — subtasks, resolved design questions, architecture notes
3. Read `CLAUDE.md` for current project state and conventions
4. Read the project memory (`MEMORY.md` in the project's memory directory) for context from previous sessions
5. Skim the current codebase to understand what's actually implemented vs what's planned. Key directories:
   <!-- INJECT:SOURCE_DIRS -->
6. Focus your questions on the next unstarted milestone first, since those decisions are most urgent

### Phase 2: Question Generation
Find questions by looking for:
- **Contradictions**: Places where two sections say different things, or where a resolved decision conflicts with a milestone's description
- **Missing capabilities**: Features referenced in the vision but with no milestone subtask or design details
- **Implementation ambiguities**: Subtasks that say *what* but not *how* — what data structures, what algorithms, what tradeoffs
- **Cross-cutting concerns**: Features that touch multiple milestones but aren't clearly owned by any
- **Dependency gaps**: Milestone N assumes something from milestone N-1 that isn't actually specified there
- **Scale/tuning unknowns**: Numbers that matter but aren't decided (sizes, rates, counts, thresholds)
- **Edge cases**: What happens when X fails? When the user does Y unexpectedly? When two systems interact?
- **Already-resolved questions that are stale**: Decisions marked resolved that may need revisiting given new context

Prioritize questions by:
1. **Blocking the next milestone** (most urgent)
2. **Affecting architectural decisions** that are hard to change later
3. **Clarifying user experience / design feel** (important but can be iterated)
4. **Nice-to-know** (least urgent)

### Phase 3: Interview
Present questions **one at a time** (or in small thematic groups of 2-3 if closely related). For each question:

1. **State the question clearly** — what needs deciding
2. **Explain why it matters** — what breaks or gets harder if we don't decide now
3. **ALWAYS offer concrete options** — every question MUST include 2-4 labeled choices (A/B/C/D) with tradeoffs explained for each. Never ask an open-ended question without options. The user should be able to answer with just a letter. Include an "Other" option if the space of answers is truly open
4. **Flag your recommendation** if you have one, with reasoning (e.g., "Recommend B because...")

After the user answers:
- Summarize the decision back to confirm understanding
- If the answer is vague, ask a focused follow-up — don't just accept "whatever you think"
- If the answer contradicts an earlier decision, flag the conflict

### Phase 4: Recording
After resolving a batch of questions:
- Update the relevant `milestones/M-NAME.md` file — add to the `## Open Questions (Resolved)` section, or update subtask descriptions with the new detail
- Use ~~strikethrough~~ for the question text and **Decided**: for the answer, matching the existing format
- If a decision affects `CLAUDE.md`, `REQUIREMENTS.md` (vision/NFRs), or memory files, update those too
- **Don't commit.** These are doc-only changes — list the files you edited at the end of the session and let the user fold them into whatever commit they like

## Style
- Be direct and specific — no filler
- Use concrete examples from the project's domain
- When presenting options, include the user experience / feel implications, not just technical tradeoffs
- Don't ask questions that are already resolved in the Open Questions section unless you think the resolution is wrong or incomplete
- Group related questions so the user builds momentum on a topic rather than context-switching
- If the user says "defer" or "decide later", respect that — note it and move on
- Aim for 5-10 questions per session, not 50. Quality over quantity

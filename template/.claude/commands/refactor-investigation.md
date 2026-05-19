# Refactor Investigation

You are doing a tech-debt survey of the codebase and appending new findings to `TECH_DEBT.md` at the repo root. This skill is **index-only** — never edit source code, never commit, never open PRs.

## Startup

1. Read `TECH_DEBT.md` at the repo root end-to-end. Note every existing `- [ ]` and `- [x]` bullet — these are the things you MUST NOT re-add.
   - If `TECH_DEBT.md` does not exist, create it from the skeleton below before continuing.
2. Read `CLAUDE.md` for the module map and current milestone status.
3. Run `git log --oneline -30` to see what's shipped recently. Bias investigation toward files that have churned (`git log --name-only --since="2 weeks ago"` is useful) — that's where fresh debt accumulates.

## Investigation

Launch up to **3 Explore agents in parallel** in a single message (one tool call per agent). One agent per category:

### Agent 1 — Markers, panics, error-handling shortcuts
- All `TODO` / `FIXME` / `HACK` / `XXX` / `// for now` / `// temporarily` / `// stub` comments with `file:line` + a one-line excerpt.
- Language-equivalent "this will crash" patterns in non-test, non-init code paths (e.g. `panic!` / `unwrap` / `throw` / `assert` used as control flow / unchecked `!` non-null asserts).
- Search inside the project source directories. Skip build outputs (e.g. `target/`, `dist/`, `node_modules/`) and asset folders.
<!-- INJECT:SOURCE_DIRS -->

### Agent 2 — Structural smells
- `wc -l` over each source file; flag any file over the project's "too long" threshold (typically ≥ 1000 lines) with `file_path : N lines` and a 2–3 line proposed split.
- Methods/functions > 200 lines (look for big `tick`, `render`, `update`, `handle`, `process` functions).
- Near-duplicate match/switch arms across files (same enum or tag matched in 3+ files with the same arm structure).
- Near-duplicate helper functions (same algorithm name or shape in 2+ files).

### Agent 3 — Architectural friction
- God modules orchestrating many disparate spawn / setup / teardown responsibilities.
- Parallel data stores that branch on a key (separate maps that should be one).
- Side-channel maps / globals that track state outside the canonical model.
- Data sprawl: families of fields/components that always travel together but are stored separately.
- Message/DTO bloat: variants that mirror many fields atomically with no delta encoding.

Each agent must be given:
- The full path to `TECH_DEBT.md` (e.g. `"reference this file for the existing entries; do not re-report anything already listed there"`).
- The category-specific brief above.
- `"Cap report at ~400 lines, prioritize the 10 most actionable items, include file:line for every finding."`

## Reconciliation

For each candidate the agents return:

1. **De-dup check.** Substring-match the candidate's `file:line` (and key phrase) against the current `TECH_DEBT.md`. If it overlaps an existing `[ ]` or `[x]` bullet, skip it — or if the new finding adds material detail, extend the existing bullet inline instead of duplicating.
2. **Section pick.** Place each new item in the matching existing section in `TECH_DEBT.md`. Add a new `## <Section>` only if no existing one fits.
3. **Bullet format.** Each new bullet:
   - Starts with `- [ ]`.
   - Has either a `file:line` (preferred) or a milestone link (`→ resolves with M-X`).
   - Has a **Why deferred:** clause capturing the trade-off, not just the problem.
   - Stays scannable in ≤ 2 lines.

Example: `- [ ] src/foo.rs:123 — Bar trait is implemented 4× with copy-paste deltas. **Why deferred:** stable; revisit only when adding a 5th impl.`

## Output

Edit `TECH_DEBT.md` in place — append new bullets to the right section. Then print a short summary:

```
Added N new items:
  ## <Section> (X new)
    - file:line — short title
  ## <Section> (Y new)
    - ...
Skipped M duplicates (already tracked).
```

If no new debt was found, say so explicitly and exit. Don't pad. Don't speculate.

## Hard rules

- Don't edit any source code. `TECH_DEBT.md` is the only file you touch.
- Don't run `git commit`, `git push`, or any destructive git command. The user reviews + commits the doc update.
- Don't propose fixes — that's `/refactor`'s job. Identify candidates only.
- If an Explore agent returns vague items (no `file:line`, no concrete signal), drop them. Quality over quantity.

## Skeleton for a missing `TECH_DEBT.md`

If `TECH_DEBT.md` does not yet exist, create it at the repo root with this skeleton:

```markdown
# Tech Debt

Refactor candidates and known smells. Items are **not bugs** — they are working code that we'd want to clean up given unbounded time. Add new items at the bottom of the relevant section. Mark resolved with `[x]` + `✅ <YYYY-MM-DD> — short note`.

## Conventions
- One bullet per item. Keep each scannable in ≤ 2 lines.
- Lead with `file_path:line` when relevant.
- "Why deferred" matters more than "what's wrong" — capture the trade-off.
- Cross-link to milestones when a planned milestone will naturally fix the item (e.g. "→ resolves with M-PERSIST").
- When a whole section closes, move it under `## Resolved` at the bottom.

---

## Module size & extraction
## Protocol & networking
## Data model & component organization
## State management & globals
## Panics & error handling
## Duplicated patterns
## Placeholder content / asset debt

---

## Resolved

(none yet)
```

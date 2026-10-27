# Claude Workflow Template

A reusable project scaffold for milestone-driven development with Claude Code. Provides skills (`/dev`, `/requirements`, `/design`, `/refactor`, `/refactor-investigation`, `/status`, `/context-audit`), a formatting hook, worktree-based session isolation, document templates, and language/domain presets.

## What You Get

**Skills** (`.claude/skills/<name>/SKILL.md`)

- **`/dev [subtask-id]`** — implements one subtask: enters a worktree, plans, codes, runs the build/test gate, marks the subtask `[x]`, and commits
- **`/requirements [milestone]`** — interviews you about design gaps, presents A/B/C/D options, records decisions in the milestone file
- **`/design [milestone]`** — analyzes the project for missing capabilities and underspecified interactions
- **`/refactor-investigation`** — surveys the codebase for new tech debt (long files, panics, duplication, architectural friction) and appends it to `TECH_DEBT.md`. Idempotent — skips items already tracked
- **`/refactor [item]`** — executes a single open `[ ]` item from `TECH_DEBT.md`: you pick which, it implements surgically, runs the gate, marks it resolved, commits
- **`/status`** — milestone progress, in-flight worktrees, uncommitted work, next recommended action
- **`/context-audit [--fix]`** — measures what every session pays for up front (`CLAUDE.md`, the memory index), memory hygiene, research-index and findings-ledger coverage, and whether the paper corpus is greppable; turns each warning into a prioritized fix and applies them on request. Its `audit.py` is read-only and stdlib-only

**Automation**

- `.claude/hooks/format-edited-file.sh` — a `PostToolUse` hook that formats every file Claude writes and feeds lint failures straight back into the session
- `.claude/settings.json` — hook wiring, `worktree.baseRef`, and permissions (git verbs pre-approved, `git push` asks, destructive git denied). Committed, so every parallel session and worktree inherits it. Its permission rules apply once you've run Claude interactively in the project and accepted the workspace trust dialog

**Documents**

- `REQUIREMENTS.md` — vision, milestone index table with status
- `milestones/M-NAME.md` — numbered subtask checklists with resolved design questions
- `TECH_DEBT.md` — refactor candidates, same `[ ]` / `[x] ✅ <date>` convention (created on first `/refactor-investigation`)
- `CLAUDE.md` — conventions, architecture, git and worktree policy
- `research/` — dated research notes (`YYYY-MM-DD-<slug>.md`) indexed in `research/INDEX.md`; `docs/` stays the curated reference that cites them
- `research/FINDINGS.md` — the verdict ledger: one row per tested claim (KEEP / OPT-IN / DROP / OPEN) with its evidence, kept current so settled questions aren't re-run

**Research paper corpus** (`research/papers/`)

- `fetch.py` harvests every arXiv ID and DOI cited in the repo's Markdown and downloads each PDF over open-access routes only (arXiv → Unpaywall → publisher OA → Europe PMC). PDFs are gitignored; it regenerates `MANIFEST.md` (identifier → file → citing docs) and `not_downloaded_papers.md` (what it couldn't get, with the name to save a manual copy under). Unpaywall's contact email comes from `$RESEARCH_EMAIL`, else `git config user.email`
- `extract_text.py` — run at the end of every fetch: writes a plain-text copy of each PDF to `research/papers/text/` (gitignored, incremental, needs poppler's `pdftotext`) so the papers are greppable
- `CORPUS.md` — the curated per-paper digest; `corpus_status.py` lists PDFs not yet digested

## Quick Start

```bash
cd ~/git/my-project
~/claude-workflow-template/setup.sh
```

No prompts: the project name defaults to the directory name, and the preset is detected from the repo (`Cargo.toml` → a Rust preset, `package.json` → `typescript-web`). Override with `--name` / `--preset`. Existing files are never overwritten.

```bash
setup.sh --preset typescript-web      # pick the preset explicitly
setup.sh --list-presets               # see what's available
setup.sh --force                      # refresh skills/hooks/settings in an existing project
```

`--force` is the upgrade path: it refreshes the machinery (`.claude/skills/`, `.claude/hooks/`, `.claude/settings.json`, the `research/papers/` scripts and README), backs up anything it replaces as `<file>.bak`, and never touches `REQUIREMENTS.md`, `CLAUDE.md`, `milestones/`, `research/INDEX.md`, `research/FINDINGS.md`, or `CORPUS.md`.

## Workflow

1. **Write your vision** in `REQUIREMENTS.md` — what you're building and why
2. **Define milestones** — each a self-contained deliverable with numbered subtasks
3. **`/requirements`** — Claude interviews you, records decisions in the milestone file
4. **`/design`** — Claude identifies missing capabilities and suggests approaches
5. **`/dev M-NAME.1`** — Claude implements a subtask, runs tests, marks it done, commits

Ongoing, alongside milestone work:

- **`/refactor-investigation`** after shipping a milestone, to capture accumulated debt
- **`/refactor`** when you want to spend a session paying debt down instead of shipping
- **`/status`** to see where every parallel session left things
- **`/context-audit`** when `CLAUDE.md` or the memory index has grown, or sessions keep re-deriving known results

## Parallel Sessions

Code sessions run in git worktrees so two Claude sessions never edit the same checkout.

```bash
claude -w M-FIRST-1          # start a session in .claude/worktrees/M-FIRST-1
claude -w M-FIRST-1 --tmux   # ...in a tmux split
```

If you start a session in the main checkout and run `/dev` or `/refactor`, Claude enters a worktree itself (`CLAUDE.md` instructs it to). Doc-only work — `/requirements`, `/design`, `/refactor-investigation` — stays in the main checkout, so milestone edits never need a merge.

When a subtask is done, merge it back from the main checkout:

```bash
git merge worktree-M-FIRST-1
git worktree remove .claude/worktrees/M-FIRST-1
```

Details worth knowing:

- `worktree.baseRef` is set to `"head"`, not the `"fresh"` default — worktrees branch from your current local `HEAD`, so they carry the subtask commits you haven't pushed. Switch to `"fresh"` in `.claude/settings.json` if you'd rather branch from `origin`'s default branch.
- `.claude/worktrees/` and `.claude/settings.local.json` are added to `.gitignore` by setup.
- A worktree is a fresh checkout with no `node_modules`, no `target/`, and no `.env`. List gitignored files worktrees need in `.worktreeinclude` (setup writes a commented starter) and Claude Code copies them in.

## Formatting & Lint Hook

`.claude/hooks/format-edited-file.sh` runs after every `Write`/`Edit`/`NotebookEdit`. It formats the single file that changed, then runs a fast per-file lint and returns failures to Claude as context so they get fixed immediately instead of at the end of the session.

| Files | Formats with | Lints with |
|---|---|---|
| `.rs` | `rustfmt` (edition read from `Cargo.toml`) | — |
| `.ts` `.tsx` `.js` `.jsx` | `biome` or `prettier` | `eslint` |
| `.json` `.css` `.md` `.yaml` `.html` … | `biome` or `prettier` | — |
| `.py` | `ruff format` or `black` | `ruff check` |
| `.go` | `goimports` or `gofmt` | `go vet` |
| `.sh` | `shfmt` | `shellcheck` |

Rules it follows: tools are auto-detected and silently skipped when absent (so it works for `custom` presets and polyglot repos); a global `prettier` only runs when the project has a prettier config; gitignored files, `node_modules/`, `target/`, `dist/`, and `vendor/` are left alone; and it **always exits 0**, so a broken formatter can never block a session. `jq` is required — without it the hook no-ops.

Rust gets format-only on purpose: `cargo check`/`clippy` are crate-wide and too slow to run per edit. `/dev` and `/refactor` run the full build gate before committing.

### Optional: a stricter Stop gate

Not installed by default. If you want a session to be unable to end with uncommitted code, add a `Stop` hook to `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'git diff --quiet -- \":!*.md\" || jq -n \"{decision:\\\"block\\\",reason:\\\"Uncommitted code changes — commit them before finishing.\\\"}\"'"
          }
        ]
      }
    ]
  }
}
```

## Commit Policy

Baked into `CLAUDE.md` and the skills:

- A session that **changed code** commits it once tests and build pass — code plus the milestone checkbox in one commit, message `M-NAME.1: <summary>` (or `refactor: …`).
- A session that **only touched docs** (`/requirements`, `/design`, `/refactor-investigation`) leaves the edits in the working tree and tells you which files changed.
- Never `git push`, never a PR, never `git add -A`. You review and push.
- Destructive git (`reset --hard`, `restore`, `clean`) is denied outright in `.claude/settings.json`; `git push` is set to ask.

## Presets

Presets inject project-specific content into the generic skill templates:

| Preset | Language | Domain | Design References |
|--------|----------|--------|-------------------|
| `rust-game` | Rust + ECS | Game development | DayZ, Tarkov, Project Zomboid |
| `rust-music-sim` | Rust | Music simulation | — |
| `typescript-web` | TypeScript | Web applications | Linear, Notion, Stripe |
| `custom` | Manual | Manual | Manual |

With `custom`, the injection markers are stripped and you fill in the sections yourself.

### Creating a New Preset

Copy an existing preset directory and modify the files:

```
presets/your-preset/
  dev-role.md                 # Role description for /dev
  dev-codestyle.md            # Code style rules
  dev-wiring.md               # Project-specific wiring (how to register new modules)
  dev-teststyle.md            # Test conventions and commands
  dev-buildcommands.md        # Build/test gate commands, run before the commit
  requirements-role.md        # Role description for /requirements
  requirements-sourcedirs.md  # Source directories to skim
  design-role.md              # Role description for /design
  design-categories.md        # Analysis categories (what to look for)
  design-references.md        # Comparable products to reference
  claude-sections.md          # CLAUDE.md section content (conventions, testing, etc.)
  settings-permissions.json   # Extra permissions merged into .claude/settings.json
```

Preset detection maps a language family to a preset by name prefix (`Cargo.toml` → presets starting with `rust`). When several match, setup leaves the preset unset rather than guessing — pass `--preset`.

## File Structure After Setup

```
your-project/
  .claude/
    skills/
      dev/SKILL.md
      requirements/SKILL.md
      design/SKILL.md
      refactor/SKILL.md
      refactor-investigation/SKILL.md
      status/SKILL.md
      context-audit/SKILL.md
      context-audit/audit.py   # read-only knowledge-organisation report
    hooks/
      format-edited-file.sh    # PostToolUse formatter + linter
    settings.json              # hooks, worktree base ref, permissions (commit this)
    settings.local.json        # your machine-local overrides (gitignored)
    worktrees/                 # per-session checkouts (gitignored)
  .worktreeinclude             # gitignored files copied into new worktrees
  CLAUDE.md                    # conventions, git + worktree policy (fill in TODOs)
  REQUIREMENTS.md              # vision + milestone table
  TECH_DEBT.md                 # refactor candidates (created on first /refactor-investigation)
  milestones/
    M-EXAMPLE.md               # format reference (delete when you have real milestones)
  research/
    INDEX.md                   # dated research notes, newest first
    FINDINGS.md                # verdict ledger, kept current
    YYYY-MM-DD-<slug>.md       # one note per study, scout or postmortem
    papers/
      fetch.py                 # harvest citations, download open-access PDFs
      corpus_status.py         # PDFs not yet digested in CORPUS.md
      extract_text.py          # greppable text/ copies of the PDFs
      README.md
      CORPUS.md                # curated per-paper digest
      MANIFEST.md              # generated: identifier → file → citing docs
      *.pdf                    # the corpus (gitignored)
      text/                    # extracted plain text (gitignored)
```

Upgrading from an older version of this template: your old `.claude/commands/*.md` files still work, but they shadow the new skills of the same name. `setup.sh` warns about them — delete them once you've moved any local edits into `.claude/skills/`.

## Milestone Format

```markdown
# M-NAME — Short Description
**Goal:** What this milestone delivers.

- [ ] **M-NAME.1** First subtask — description
- [ ] **M-NAME.2** Second subtask — description

## Open Questions (Resolved)
- ~~**Question?**~~ **Decided**: Answer + rationale
```

`/dev` marks subtasks `[x]` on completion. `/requirements` records decisions in the Open Questions section.

# Claude Workflow Template

A reusable project scaffold for milestone-driven development with Claude Code. Provides structured skills (`/dev`, `/requirements`, `/design`, `/refactor`, `/refactor-investigation`), document templates, and language/domain presets.

## What You Get

- **`/dev`** — Developer agent that reads your requirements, implements a subtask, runs tests, and updates milestone progress
- **`/requirements`** — Requirements interviewer that finds design gaps, presents A/B/C/D options, and records decisions in milestone files
- **`/design`** — Domain designer that analyzes your project for missing capabilities, underspecified interactions, and design gaps
- **`/refactor-investigation`** — Tech-debt surveyor that scans the codebase for new refactor candidates (long files, panics, duplication, architectural friction) and appends them to `TECH_DEBT.md`. Idempotent — skips items already tracked
- **`/refactor`** — Executes a single open `[ ]` item from `TECH_DEBT.md`: prompts the user to pick which, implements it surgically, runs the build/test gate, and marks the item resolved
- **REQUIREMENTS.md** — Project vision, milestone index table with status tracking
- **milestones/M-NAME.md** — Numbered subtask checklists with resolved design questions
- **TECH_DEBT.md** — Refactor candidates and known smells, tracked with the same `[ ]` / `[x] ✅ <date>` convention as milestones (created on first `/refactor-investigation` run)
- **CLAUDE.md** — Project conventions, architecture, and coding standards

## Quick Start

```bash
cd ~/git/my-project
~/claude-workflow-template/setup.sh
```

The script will prompt for:
- Project name
- Preset (language/domain — determines code style, test conventions, design references)

It creates the directory structure, skills, and document templates. Files that already exist are never overwritten.

## Workflow

1. **Write your vision** in `REQUIREMENTS.md` — what you're building and why
2. **Define milestones** — each is a self-contained deliverable with numbered subtasks
3. **Run `/requirements`** — Claude interviews you to fill gaps, records decisions in milestone files
4. **Run `/design`** — Claude identifies missing capabilities and suggests approaches
5. **Run `/dev M-NAME.1`** — Claude implements a subtask, runs tests, marks it done

Each `/dev` session automatically updates the milestone checkbox and documentation.

Ongoing, alongside the milestone work:

- **`/refactor-investigation`** — periodically (e.g. after shipping a milestone) to capture tech debt accumulated during recent work
- **`/refactor`** — when you want to spend a session paying down debt instead of shipping features; pick one item, fix it, move on

## Presets

Presets inject project-specific content into the generic skill templates:

| Preset | Language | Domain | Design References |
|--------|----------|--------|-------------------|
| `rust-game` | Rust + ECS | Game development | DayZ, Tarkov, Project Zomboid |
| `typescript-web` | TypeScript | Web applications | Linear, Notion, Stripe |
| `custom` | Manual | Manual | Manual |

### Creating a New Preset

Copy an existing preset directory and modify the files:

```
presets/your-preset/
  dev-role.md              # Role description for /dev
  dev-codestyle.md         # Code style rules
  dev-wiring.md            # Project-specific wiring (how to register new modules)
  dev-teststyle.md         # Test conventions and commands
  dev-buildcommands.md     # Build/test commands for completion step
  requirements-role.md     # Role description for /requirements
  requirements-sourcedirs.md  # Source directories to skim
  design-role.md           # Role description for /design
  design-categories.md     # Analysis categories (what to look for)
  design-references.md     # Comparable products to reference
  claude-sections.md       # CLAUDE.md section content (conventions, testing, etc.)
  settings-permissions.json   # .claude/settings.local.json permissions
```

## File Structure After Setup

```
your-project/
  .claude/
    commands/
      dev.md                       # /dev skill
      requirements.md              # /requirements skill
      design.md                    # /design skill
      refactor.md                  # /refactor skill
      refactor-investigation.md    # /refactor-investigation skill
    settings.local.json    # Permissions
  CLAUDE.md                # Project conventions (fill in TODOs)
  REQUIREMENTS.md          # Vision + milestone table
  TECH_DEBT.md             # Refactor candidates (created on first /refactor-investigation)
  milestones/
    M-EXAMPLE.md           # Format reference (delete when you have real milestones)
```

## Milestone Format

```markdown
# M-NAME — Short Description
**Goal:** What this milestone delivers.

- [ ] **M-NAME.1** First subtask — description
- [ ] **M-NAME.2** Second subtask — description

## Open Questions (Resolved)
- ~~**Question?**~~ **Decided**: Answer + rationale
```

The `/dev` agent marks subtasks `[x]` on completion. The `/requirements` agent records decisions in the Open Questions section.

---
name: context-audit
description: Audit how well this repo's knowledge is organised for Claude Code sessions (CLAUDE.md and memory-index size, memory hygiene, research index and findings-ledger coverage, searchable paper corpus) and recommend fixes. Use when the user asks how context or memory management is going, why sessions keep re-deriving things, or whether to add RAG.
argument-hint: "[--fix]"
allowed-tools:
  - Bash(python3 .claude/skills/context-audit/audit.py:*)
---

# Context Audit

Measure first, then advise. Every number in your answer comes from the audit script, not
from an estimate.

## 1. Run the audit

From the repo root:

```bash
python3 .claude/skills/context-audit/audit.py
```

It is read-only and prints a Markdown report with `OK` / `WARN` / `INFO` lines in five
groups. If the memory dir it guesses is wrong, rerun with `--memory-dir <path>`; the path is
the memory directory named in your system prompt.

## 2. Turn each WARN into a fix

| WARN | Why it costs | Fix |
|---|---|---|
| CLAUDE.md over the word budget, or one section over 800 words | Loaded in full on every session, including sessions that never need it | Keep rules and conventions. Move history (completed-milestone write-ups, changelogs) to `docs/` and leave one line each plus a pointer. Trim a project-structure tree to the directories whose purpose isn't obvious from their name |
| MEMORY.md over the word budget, or lines over 45 words | The index is loaded every session, and only its first 200 lines are read | One hook per line (a title plus at most ~25 words). Detail goes in the memory file. Group by kind (direction / findings / decisions / how to work). Merge duplicates |
| Index links to missing files, or files not in the index | A memory nobody can find, or a pointer to nothing | Add the missing index line, or remove the dead one. Before deleting a memory as stale, check the code it names still contradicts it |
| Notes missing from `research/INDEX.md` | A session only finds the note by a lucky search | Add one row per note, written from the note's verdict section, never from its title alone |
| No `research/FINDINGS.md` | Verdicts are spread across notes, so settled questions get re-run | Create the ledger: one row per tested claim (claim · verdict · date · evidence). Seed it from the index's verdict column and the milestone results |
| Notes edited after FINDINGS.md | A verdict may have changed without the ledger knowing | Read those notes' verdicts and update the rows they affect |
| PDFs without a text copy | PDFs are opaque to grep, so the papers can't be searched | `python3 research/papers/extract_text.py` (needs poppler's `pdftotext`) |
| PDFs not digested in CORPUS.md | The curated digest misses papers | `python3 research/papers/corpus_status.py --abstracts`. Digest in batches of about 10, through a subagent, so the abstracts stay out of this context |

`INFO` lines are context, not problems. Mention one only when it changes advice. Many notes
missing from FINDINGS.md is normal: literature scouts carry no verdict.

## 3. RAG / embeddings

Recommend an embedding index only when **both** hold:
- the scale line says the Markdown exceeds the threshold, **and**
- the user can name a real retrieval miss: something that exists in the repo that grep and
  the indexes failed to surface.

Otherwise the answer is no. Grep plus the indexes is exact and cannot go stale, and a broad
search can run in an Explore subagent so only its conclusion enters the context. Paper full
text being large does not change this: grep over a few tens of MB of text is instant.

## 4. Session habits (mention when relevant)

- `/context` shows what is filling the current window.
- Broad searches go through an Explore subagent, which returns conclusions rather than file
  dumps.
- `/clear` between unrelated subtasks; auto-compaction handles long single tasks.
- Record durable knowledge when it is learned: a verdict goes in its FINDINGS.md row, a
  correction from the user goes in memory, a measurement goes in a dated note.

## 5. Report, then apply on request

Answer with:
1. A three-line health summary: the always-loaded cost in tokens, how many WARNs, and the
   single worst problem.
2. Up to five fixes in priority order, cheapest high-value first, each naming the file and
   the expected effect (for example "CLAUDE.md 4.1k → ~2.3k words").
3. An offer to apply them.

Apply fixes only when the user agrees, or the argument is `--fix`. Rules while applying:
- Never rewrite a dated research note; they are records of their day. Only add index rows
  and ledger rows that point at them.
- Moving text out of CLAUDE.md is a move, not a delete: the full text lands in `docs/` first.
- Doc edits are left uncommitted for the user unless they ask for a commit.
- Rerun the audit at the end and show the before → after numbers.

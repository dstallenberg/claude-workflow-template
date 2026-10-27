#!/usr/bin/env python3
"""Measure how well this repo's knowledge is organised for Claude Code sessions.

Prints a Markdown report: what every session pays for up front (CLAUDE.md, the memory
index), memory hygiene, research-note indexing, the findings ledger, and whether the paper
corpus is searchable. Read-only; stdlib only. The /context-audit skill turns it into advice.

    python3 .claude/skills/context-audit/audit.py [--memory-dir DIR]
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

# Thresholds (words). One word is about 1.35 tokens of English prose.
CLAUDE_MD_WARN_WORDS = 2500  # loaded in full on every session start
MEMORY_INDEX_WARN_WORDS = 800  # MEMORY.md is loaded on every session start
MEMORY_INDEX_MAX_LINES = 200  # Claude Code loads only the first 200 lines of MEMORY.md
SECTION_WARN_WORDS = 800  # one CLAUDE.md section this big is usually history, not rules
RAG_CONSIDER_WORDS = 3_000_000  # below this, grep + an index beats an embedding pipeline
TOKENS_PER_WORD = 1.35


def words(text: str) -> int:
    """Whitespace word count."""
    return len(text.split())


def read(path: str) -> str:
    """File contents, or '' if it does not exist."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def repo_root() -> str:
    """The main checkout's root (also when run from a worktree)."""
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return os.path.dirname(common)
    except (OSError, subprocess.CalledProcessError):
        return os.getcwd()


def default_memory_dir(root: str) -> str:
    """Claude Code's per-project memory dir: ~/.claude/projects/<path with non-alnum -> '-'>."""
    slug = re.sub(r"[^A-Za-z0-9]", "-", root)
    return os.path.join(os.path.expanduser("~"), ".claude", "projects", slug, "memory")


def tokens(n_words: int) -> str:
    """Human-readable token estimate."""
    return f"~{int(n_words * TOKENS_PER_WORD / 1000 + 0.5)}k tokens"


def flag(ok: bool) -> str:
    """Status marker for a report line."""
    return "OK  " if ok else "WARN"


def audit_always_loaded(root: str, mem_dir: str) -> list[str]:
    """CLAUDE.md and MEMORY.md size, plus CLAUDE.md's largest sections."""
    out = ["## 1. Loaded on every session"]
    claude = read(os.path.join(root, "CLAUDE.md"))
    n = words(claude)
    out.append(
        f"- {flag(n <= CLAUDE_MD_WARN_WORDS)} CLAUDE.md: {n} words ({tokens(n)}); "
        f"warn above {CLAUDE_MD_WARN_WORDS}"
    )
    sections = re.split(r"^(?=## )", claude, flags=re.M)
    big = sorted(
        ((words(s), s.splitlines()[0]) for s in sections if s.startswith("## ")),
        reverse=True,
    )[:4]
    for w, title in big:
        mark = flag(w <= SECTION_WARN_WORDS)
        out.append(f"  - {mark} {title[3:]}: {w} words")
    index = read(os.path.join(mem_dir, "MEMORY.md"))
    if index:
        lines = index.count("\n") + 1
        n = words(index)
        out.append(
            f"- {flag(n <= MEMORY_INDEX_WARN_WORDS)} MEMORY.md: {n} words ({tokens(n)}), "
            f"{lines} lines"
        )
        out.append(
            f"- {flag(lines <= MEMORY_INDEX_MAX_LINES)} MEMORY.md line budget: "
            f"{lines}/{MEMORY_INDEX_MAX_LINES} (lines past it are never loaded)"
        )
        long_lines = [ln for ln in index.splitlines() if words(ln) > 45]
        if long_lines:
            out.append(
                f"- WARN {len(long_lines)} MEMORY.md line(s) over 45 words: the index should "
                "hold hooks, the detail belongs in the memory file"
            )
    else:
        out.append(f"- INFO no MEMORY.md at {mem_dir}")
    return out


def audit_memory(mem_dir: str) -> list[str]:
    """Index links vs files, broken [[links]], missing frontmatter."""
    out = ["## 2. Memory hygiene"]
    if not os.path.isdir(mem_dir):
        return [*out, "- INFO no memory directory"]
    files = {f for f in os.listdir(mem_dir) if f.endswith(".md") and f != "MEMORY.md"}
    index = read(os.path.join(mem_dir, "MEMORY.md"))
    linked = set(re.findall(r"\]\(([^)]+\.md)\)", index))
    names, no_front = set(), []
    for f in files:
        text = read(os.path.join(mem_dir, f))
        m = re.search(r"^name:\s*(\S+)", text, re.M)
        if m:
            names.add(m.group(1).strip("\"'"))
        if not text.startswith("---"):
            no_front.append(f)
    wiki = set()
    for f in files:
        wiki |= set(re.findall(r"\[\[([^\]]+)\]\]", read(os.path.join(mem_dir, f))))
    checks = [
        ("index links to missing files", sorted(linked - files)),
        ("memory files not in the index", sorted(files - linked)),
        ("files without frontmatter", sorted(no_front)),
    ]
    out.append(f"- INFO {len(files)} memory files")
    for label, items in checks:
        out.append(f"- {flag(not items)} {label}: {len(items)}" + (f" {items}" if items else ""))
    dangling = sorted(wiki - names)
    out.append(
        f"- INFO [[links]] with no memory yet (allowed, marks a gap): {len(dangling)}"
        + (f" {dangling[:8]}" if dangling else "")
    )
    return out


def audit_research(root: str) -> list[str]:
    """Dated notes vs INDEX.md and FINDINGS.md."""
    out = ["## 3. Research notes"]
    rdir = os.path.join(root, "research")
    if not os.path.isdir(rdir):
        return [*out, "- INFO no research/ directory"]
    notes = sorted(f for f in os.listdir(rdir) if re.match(r"\d{4}-\d{2}-\d{2}-.+\.md$", f))
    total = sum(words(read(os.path.join(rdir, f))) for f in notes)
    out.append(f"- INFO {len(notes)} dated notes, {total} words ({tokens(total)})")
    index = read(os.path.join(rdir, "INDEX.md"))
    if index:
        missing = [f for f in notes if f not in index]
        out.append(
            f"- {flag(not missing)} notes missing from INDEX.md: {len(missing)}"
            + (f" {missing}" if missing else "")
        )
    else:
        out.append("- WARN no research/INDEX.md: sessions can only find notes by search")
    findings = read(os.path.join(rdir, "FINDINGS.md"))
    if findings:
        uncited = [f for f in notes if f not in findings]
        mtime = os.path.getmtime(os.path.join(rdir, "FINDINGS.md"))
        newer = [f for f in notes if os.path.getmtime(os.path.join(rdir, f)) > mtime]
        out.append(
            f"- INFO notes not cited in FINDINGS.md: {len(uncited)} "
            "(fine for scouts; a note with a verdict should have a row)"
        )
        out.append(
            f"- {flag(not newer)} notes edited after FINDINGS.md: {len(newer)}"
            + (f" {newer}" if newer else "")
        )
    else:
        out.append(
            "- WARN no research/FINDINGS.md: verdicts are scattered across notes, so "
            "settled questions get re-run"
        )
    return out


def audit_papers(root: str) -> list[str]:
    """PDFs vs text copies vs CORPUS.md digest."""
    out = ["## 4. Paper corpus"]
    pdir = os.path.join(root, "research", "papers")
    if not os.path.isdir(pdir):
        return [*out, "- INFO no research/papers/ directory"]
    tdir = os.path.join(pdir, "text")
    pdfs = []
    for d, dirs, fs in os.walk(pdir):
        dirs[:] = [x for x in dirs if os.path.join(d, x) != tdir]
        pdfs += [os.path.relpath(os.path.join(d, f), pdir) for f in fs if f.endswith(".pdf")]
    no_text = [
        p for p in pdfs if not os.path.exists(os.path.join(tdir, os.path.splitext(p)[0] + ".txt"))
    ]
    out.append(f"- INFO {len(pdfs)} PDFs")
    out.append(
        f"- {flag(not no_text)} PDFs without a greppable text copy: {len(no_text)}"
        + ("" if shutil.which("pdftotext") else " (pdftotext not installed)")
    )
    corpus = read(os.path.join(pdir, "CORPUS.md"))
    if corpus:
        undigested = [p for p in pdfs if os.path.basename(p) not in corpus]
        out.append(f"- {flag(not undigested)} PDFs not digested in CORPUS.md: {len(undigested)}")
    text_words = 0
    for d, _, fs in os.walk(tdir):
        text_words += sum(os.path.getsize(os.path.join(d, f)) for f in fs) // 6
    if text_words:
        out.append(f"- INFO paper full text: ~{text_words} words")
    return out


def audit_scale(root: str) -> list[str]:
    """Total searchable Markdown, against the point where embeddings start to pay."""
    total = 0
    for d, dirs, fs in os.walk(root):
        dirs[:] = [
            x
            for x in dirs
            if not x.startswith(".") and x not in {"node_modules", "target", "text", "worktrees"}
        ]
        total += sum(words(read(os.path.join(d, f))) for f in fs if f.endswith(".md"))
    ok = total < RAG_CONSIDER_WORDS
    verdict = "grep + indexes suffice" if ok else "an embedding index may start to pay"
    return [
        "## 5. Scale",
        f"- INFO tracked Markdown: {total} words ({tokens(total)}); {verdict} "
        f"(threshold {RAG_CONSIDER_WORDS} words)",
    ]


def main() -> int:
    """Print the full report."""
    root = repo_root()
    args = sys.argv[1:]
    mem_dir = args[args.index("--memory-dir") + 1] if "--memory-dir" in args else None
    mem_dir = mem_dir or default_memory_dir(root)
    report = [f"# Context audit: {root}", f"memory dir: {mem_dir}", ""]
    for part in (
        audit_always_loaded(root, mem_dir),
        audit_memory(mem_dir),
        audit_research(root),
        audit_papers(root),
        audit_scale(root),
    ):
        report += [*part, ""]
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())

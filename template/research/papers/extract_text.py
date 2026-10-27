#!/usr/bin/env python3
"""Extract a plain-text copy of every PDF in this folder so the corpus is greppable.

PDFs are opaque to `grep` / Claude Code's search tools; a `.txt` sibling makes every
cited paper searchable by term, identifier, or author:

    python3 research/papers/extract_text.py          # extract new / changed PDFs
    python3 research/papers/extract_text.py --force  # re-extract everything
    grep -ril "dentate gyrus" research/papers/text/   # then search the corpus

Output mirrors the PDF layout under `text/` (`extra/foo.pdf` -> `text/extra/foo.txt`)
and is gitignored like the PDFs: it is derived, large, and copyrighted. A PDF is
re-extracted only when it is newer than its text. Uses poppler's `pdftotext`
(`apt install poppler-utils` / `brew install poppler`); if it is missing the script
says so and exits 0, so `fetch.py` never fails on it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT_DIR = os.path.join(HERE, "text")


def find_pdfs() -> list[str]:
    """Every PDF under this folder (excluding the text output), as paths relative to HERE."""
    pdfs = []
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if os.path.join(root, d) != TEXT_DIR and d != "__pycache__"]
        pdfs += [os.path.relpath(os.path.join(root, f), HERE) for f in files if f.endswith(".pdf")]
    return sorted(pdfs)


def text_path(pdf: str) -> str:
    """The `.txt` output path for a PDF path relative to HERE."""
    return os.path.join(TEXT_DIR, os.path.splitext(pdf)[0] + ".txt")


def extract_one(pdf: str) -> str:
    """Run pdftotext on one PDF; return a status string (ok / FAIL: reason)."""
    out = text_path(pdf)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        proc = subprocess.run(
            ["pdftotext", "-enc", "UTF-8", os.path.join(HERE, pdf), out],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return "FAIL: timeout"
    if proc.returncode != 0:
        err = proc.stderr.strip().splitlines()
        return f"FAIL: {err[-1] if err else proc.returncode}"
    if os.path.getsize(out) < 200:
        return "ok (little/no text: scanned PDF?)"
    return "ok"


def extract_all(force: bool = False) -> int:
    """Extract every PDF whose text is missing or stale; return the number of failures."""
    if shutil.which("pdftotext") is None:
        print("extract_text: pdftotext not found (install poppler-utils); skipping.")
        return 0
    todo = [
        p
        for p in find_pdfs()
        if force
        or not os.path.exists(text_path(p))
        or os.path.getmtime(text_path(p)) < os.path.getmtime(os.path.join(HERE, p))
    ]
    failures = 0
    for pdf in todo:
        status = extract_one(pdf)
        failures += status.startswith("FAIL")
        if status != "ok":
            print(f"[text] {pdf:<60} {status}", flush=True)
    where = os.path.relpath(TEXT_DIR)
    print(f"extract_text: {len(todo)} extracted ({failures} failed), text in {where}")
    return failures


if __name__ == "__main__":
    extract_all(force="--force" in sys.argv[1:])
    sys.exit(0)

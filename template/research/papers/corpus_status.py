#!/usr/bin/env python3
"""Report which PDFs in this folder are not yet digested in CORPUS.md.

`fetch.py` downloads PDFs and regenerates the machine `MANIFEST.md`; `CORPUS.md`
is the *curated* knowledge digest (one synthesized entry per paper). This script
is the bridge: after a fetch, run it to see exactly which new PDFs still need an
entry, so the corpus can be extended incrementally instead of re-read wholesale.

    python3 research/papers/corpus_status.py            # list gaps + coverage
    python3 research/papers/corpus_status.py --abstracts # also dump each gap's abstract

Coverage is decided by whether a PDF's filename appears verbatim inside CORPUS.md
(entries cite their source as `<filename.pdf>`), so a paper listed under several
co-authored variants still counts as covered. Exit code is non-zero when gaps exist,
so it can gate CI or a pre-commit check if desired.
"""

from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "CORPUS.md")


def main() -> int:
    """List PDFs present on disk but absent from CORPUS.md; optionally dump abstracts."""
    show_abstracts = "--abstracts" in sys.argv[1:]

    pdfs = sorted(f for f in os.listdir(HERE) if f.endswith(".pdf"))
    try:
        with open(CORPUS, encoding="utf-8") as fh:
            corpus_text = fh.read()
    except OSError:
        print("CORPUS.md not found — nothing to compare against.", file=sys.stderr)
        return 2

    missing = [f for f in pdfs if f not in corpus_text]
    covered = len(pdfs) - len(missing)
    print(f"Corpus coverage: {covered}/{len(pdfs)} PDFs digested in CORPUS.md")

    if not missing:
        print("All present PDFs are digested. ✓")
        return 0

    print(f"\n{len(missing)} PDF(s) NOT yet in CORPUS.md — add an entry for each:")
    for f in missing:
        print(f"  - {f}")

    if show_abstracts:
        for f in missing:
            print(f"\n{'=' * 78}\n{f}\n{'=' * 78}")
            try:
                out = subprocess.run(
                    ["pdftotext", "-f", "1", "-l", "3", "-layout", os.path.join(HERE, f), "-"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                print(out.stdout[:4000] or "(no extractable text — may be scanned)")
            except (OSError, subprocess.SubprocessError) as e:
                print(f"(could not extract: {e})")
    else:
        print("\nRe-run with --abstracts to dump each missing paper's abstract/intro.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

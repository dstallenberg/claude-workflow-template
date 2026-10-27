# Research papers (local cache)

PDFs of every paper cited across the repo's Markdown — milestones, `research/` reports,
`docs/`, `REQUIREMENTS.md`. **The PDFs are gitignored** (`research/papers/**/*.pdf`);
`fetch.py`, `corpus_status.py`, this README, `CORPUS.md` and the generated `MANIFEST.md`
are tracked, so the corpus is reproducible from a fresh clone.

## Fetch / refresh

```bash
python3 research/papers/fetch.py
```

`fetch.py` **self-harvests** every arXiv ID and DOI from the repo's Markdown, so the
corpus always matches what is actually cited — add a citation, re-run, the paper appears:

1. arXiv IDs → `https://arxiv.org/pdf/<id>`
2. DOIs → **Unpaywall** open-access PDF → publisher-OA templates (Nature, PLoS, Frontiers,
   bioRxiv, OSF, …) → **Europe PMC** render PDF — legitimate OA routes only.

It skips files already present, and regenerates `MANIFEST.md` (identifier → file → citing
docs) and `not_downloaded_papers.md` (what it could not get, with the name to save each
under) on every run. Paywalled or bot-blocked papers are logged, never circumvented —
**no Sci-Hub**. Save a manual download under its listed name and the next run counts it.

Unpaywall needs a contact email: `$RESEARCH_EMAIL`, else `git config user.email`.

## Searchable text

`fetch.py` ends by running `extract_text.py`, which writes a plain-text copy of every PDF
to `text/` (gitignored, incremental: only new or changed PDFs are re-extracted; needs
poppler's `pdftotext`). That makes the whole corpus greppable, so a question like "which
papers discuss dentate-gyrus sparsity?" is a search, not a re-read:

```bash
python3 research/papers/extract_text.py            # after a hand-added PDF
grep -ril "pattern separation" research/papers/text/
```

Search `CORPUS.md` first (curated, one entry per paper), and the `text/` copies when the
digest does not cover the detail you need.

## Books and other hand-added sources

A book or paper with no arXiv ID / DOI route is saved here by hand under a stable name
(`book-<author>-<year>-<slug>.pdf`) and gets a `CORPUS.md` entry with its ISBN or source, since
`fetch.py` cannot re-download it and a fresh clone will not have it. It is gitignored like every
PDF here — never commit a copyrighted text.

## The digest

`CORPUS.md` is the **curated** reading of the corpus — one entry per paper: title, file,
what it actually shows, and what it means for this project. After a fetch:

```bash
python3 research/papers/corpus_status.py              # PDFs not yet digested
python3 research/papers/corpus_status.py --abstracts  # plus each one's first pages
```

Digests are written from the abstract and introduction, not a full read — open the PDF
before resting a design decision on a result.

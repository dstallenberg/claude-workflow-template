# Research index

Dated research notes, newest first: literature scouts, measurements, probes, postmortems.
A note is **what was found on a given day** and is not rewritten afterwards — a later
finding gets a new note that cites the old one. Durable conclusions move into the
milestone that acted on them, or into `docs/`, citing the note.

Verdicts across notes (what is settled, what is open) are kept current in [`FINDINGS.md`](FINDINGS.md).

**Paper corpus:** every arXiv ID / DOI cited anywhere in the repo is fetched to
[`papers/`](papers/) by `python3 research/papers/fetch.py` (PDFs gitignored). See
[`papers/MANIFEST.md`](papers/MANIFEST.md) for the list and [`papers/CORPUS.md`](papers/CORPUS.md)
for the digest.

File naming: `research/YYYY-MM-DD-<topic-slug>.md`.

| Date | Target (module · milestone) | Question | Finding | Note |
|---|---|---|---|---|

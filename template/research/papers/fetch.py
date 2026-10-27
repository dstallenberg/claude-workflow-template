#!/usr/bin/env python3
"""Download every research paper referenced across the repo into this folder.

The script self-harvests every arXiv ID and DOI from the repo's Markdown (milestones/,
research/, REQUIREMENTS.md, …), so the corpus tracks what is actually cited — add a
citation, re-run, the paper appears. arXiv IDs are fetched directly as PDFs; DOIs are
resolved to an open-access PDF via Unpaywall, then publisher-OA templates, then Europe
PMC. Paywalled / bot-blocked papers are logged as misses, not errors.

Re-run any time:  python3 research/papers/fetch.py   (skips files already present)
Regenerates MANIFEST.md each run. PDFs are gitignored; this script + the manifest +
README are tracked.
"""

from __future__ import annotations

import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

# Directories never scanned for citations: VCS, build output, dependencies, and the
# per-session worktrees (each a full checkout that would re-cite everything).
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "target", "dist", "build", "worktrees"}


def _contact_email() -> str:
    """The Unpaywall API requires a contact email: $RESEARCH_EMAIL, else git's user.email."""
    email = os.environ.get("RESEARCH_EMAIL", "").strip()
    if email:
        return email
    try:
        out = subprocess.run(
            ["git", "-C", REPO, "config", "user.email"], capture_output=True, text=True
        )
        return out.stdout.strip()
    except OSError:
        return ""


EMAIL = _contact_email()
UA = f"{os.path.basename(REPO)}-paper-fetch/1.0 (mailto:{EMAIL})"

# Optional readable filenames for arXiv IDs ("2301.08243": "i-jepa"); default is arxiv-<id>.
NAMED_ARXIV: dict[str, str] = {}

_ARXIV_RE = re.compile(r"arxiv[:/ ]*([0-9]{4}\.[0-9]{4,5})", re.I)
_ARXIV_DOI_RE = re.compile(r"10\.48550/arxiv\.([0-9]{4}\.[0-9]{4,5})", re.I)
# Stop at whitespace and markdown-link/code chars (] ` < > " '), but allow ( ) so
# old-style DOIs like 10.1016/0006-8993(95)00550-A survive; trailing junk is trimmed below.
_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\]`<>\"']+)", re.I)


CITES: dict[str, set[str]] = {}  # "arxiv:<id>" / "doi:<lower>" -> {repo-relative md paths}


def harvest() -> tuple[list[str], list[str]]:
    """Scan every Markdown file in the repo for arXiv IDs and DOIs.

    So the corpus always tracks what the milestones/research actually cite — add a
    citation, re-run, the paper is fetched. arXiv DOIs (10.48550/arxiv.*) fold into
    the arXiv list; DOIs are de-duped case-insensitively with trailing punctuation
    and markdown cruft trimmed. Records citing files in CITES for the manifest.
    """
    arxiv: set[str] = set(NAMED_ARXIV)
    dois: dict[str, str] = {}
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        # Skip this folder's own generated docs (avoid self-harvesting MANIFEST.md /
        # not_downloaded_papers.md links back into the corpus).
        if root == HERE:
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            rel = os.path.relpath(path, REPO)
            for m in _ARXIV_RE.findall(text) + _ARXIV_DOI_RE.findall(text):
                arxiv.add(m.lower())
                CITES.setdefault("arxiv:" + m.lower(), set()).add(rel)
            for raw in _DOI_RE.findall(text):
                # Trim markdown cruft: trailing backtick/asterisk/brackets/punctuation.
                doi = re.sub(r"[`*)\]}.,;:'\"<>]+$", "", raw)
                if "10.48550/arxiv" in doi.lower() or len(doi) < 10:
                    continue
                dois.setdefault(doi.lower(), doi)
                CITES.setdefault("doi:" + doi.lower(), set()).add(rel)
    return sorted(arxiv), sorted(dois.values())


ARXIV, DOIS = harvest()


def filename_for(kind: str, ident: str) -> str:
    """The PDF filename a given identifier downloads to (matches fetch_arxiv/fetch_doi)."""
    if kind == "arxiv":
        return NAMED_ARXIV.get(ident, "arxiv-" + ident) + ".pdf"
    return "doi-" + ident.replace("/", "_").replace(":", "_") + ".pdf"


BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _get(url: str, timeout: int = 30, ua: str = UA) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _publisher_pdf_urls(doi: str) -> list[str]:
    """Return deterministic open-access PDF URLs for a DOI's publisher.

    Used when Unpaywall can't hand a direct PDF (or its CDN link is blocked); a
    browser-UA fetch handles most bot gates.
    """
    d = doi.lower()
    if d.startswith("10.1101/"):  # bioRxiv / medRxiv preprints (OA)
        rest = doi.split("/", 1)[1]
        return [
            f"https://www.biorxiv.org/content/10.1101/{rest}{v}.full.pdf" for v in ("v1", "v2", "")
        ]
    if d.startswith("10.1038/"):  # Nature family (OA ones: Nat Commun / ncomms)
        art = doi.split("/", 1)[1]
        return [f"https://www.nature.com/articles/{art}.pdf"]
    if d.startswith("10.1371/"):  # PLoS (always OA)
        journal = {
            "pcbi": "ploscompbiol",
            "pone": "plosone",
            "pbio": "plosbiology",
            "pgen": "plosgenetics",
        }.get(doi.split(".")[-2], "plosone")
        return [f"https://journals.plos.org/{journal}/article/file?id={doi}&type=printable"]
    if d.startswith("10.1126/"):  # Science / Science Advances (sciadv is OA)
        return [f"https://www.science.org/doi/pdf/{doi}?download=true"]
    if d.startswith("10.1103/"):  # APS Physical Review (PRX is OA)
        return [f"https://link.aps.org/pdf/{doi}"]
    if d.startswith("10.3389/"):  # Frontiers (always OA)
        return [f"https://www.frontiersin.org/articles/{doi}/pdf"]
    if d.startswith(("10.31234/", "10.31219/")):  # PsyArXiv / OSF preprints (OA)
        osf_id = doi.split("osf.io/")[-1]
        return [f"https://osf.io/{osf_id}/download"]
    if d.startswith("10.1007/"):  # Springer (some chapters/articles free)
        return [f"https://link.springer.com/content/pdf/{doi}.pdf"]
    return []


def _save_pdf(data: bytes, path: str) -> bool:
    if not data.startswith(b"%PDF"):
        return False
    with open(path, "wb") as f:
        f.write(data)
    return True


def fetch_arxiv(aid: str) -> tuple[str, str]:
    """Download an arXiv PDF by ID; return (id, status)."""
    name = NAMED_ARXIV.get(aid, "arxiv-" + aid)
    path = os.path.join(HERE, name + ".pdf")
    if os.path.exists(path):
        return aid, "skip (exists)"
    try:
        data = _get("https://arxiv.org/pdf/" + aid)
        return aid, "ok" if _save_pdf(data, path) else "FAIL (not a pdf)"
    except Exception as e:
        return aid, f"FAIL ({type(e).__name__})"


def fetch_doi(doi: str) -> tuple[str, str]:
    """Resolve a DOI to an open-access PDF and download it; return (doi, status)."""
    slug = "doi-" + doi.replace("/", "_").replace(":", "_")
    path = os.path.join(HERE, slug + ".pdf")
    if os.path.exists(path):
        return doi, "skip (exists)"
    api = (
        f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={urllib.parse.quote(EMAIL)}"
    )
    try:
        meta = json.loads(_get(api, timeout=30))
    except Exception as e:
        return doi, f"FAIL (unpaywall {type(e).__name__})"
    candidates: list[str] = []
    loc = meta.get("best_oa_location") or {}
    if loc.get("url_for_pdf"):
        candidates.append(loc["url_for_pdf"])
    candidates += _publisher_pdf_urls(doi)
    candidates += _europepmc_pdf_urls(doi)  # legitimate OA repository fallback
    if not candidates:
        return doi, "miss (no OA pdf)"
    for url in candidates:
        for ua in (UA, BROWSER_UA):
            try:
                if _save_pdf(_get(url, ua=ua), path):
                    return doi, "ok"
            except Exception:
                continue
    return doi, "miss (no reachable OA pdf)"


def _europepmc_pdf_urls(doi: str) -> list[str]:
    """Return the Europe PMC render-PDF URL for a DOI, if it holds an OA full text.

    Europe PMC (EBI) is a sanctioned open-access mirror of PubMed Central.
    """
    q = (
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%22{urllib.parse.quote(doi)}%22"
        "&format=json&resultType=core"
    )
    try:
        res = json.loads(_get(q, timeout=30))
        hits = res.get("resultList", {}).get("result", [])
    except Exception:
        return []
    for h in hits:
        pmcid = h.get("pmcid")
        if pmcid and (h.get("isOpenAccess") == "Y" or h.get("inEPMC") == "Y"):
            return [
                f"https://europepmc.org/articles/{pmcid}?pdf=render",
                f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf",
            ]
    return []


def main() -> int:
    """Harvest, download concurrently, print progress + summary, write the manifest."""
    if not EMAIL and DOIS:
        print(
            "No contact email for Unpaywall: set RESEARCH_EMAIL or git config user.email.",
            file=sys.stderr,
        )
        return 2
    results: list[tuple[str, str, str]] = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_arxiv, a): ("arxiv", a) for a in ARXIV}
        futs.update({ex.submit(fetch_doi, d): ("doi", d) for d in DOIS})
        for fut in cf.as_completed(futs):
            kind, ident = futs[fut]
            _, status = fut.result()
            results.append((kind, ident, status))
            print(f"[{kind:<5}] {ident:<32} {status}", flush=True)

    def n(pred):
        return sum(1 for _, _, s in results if pred(s))

    ok = n(lambda s: s == "ok")
    skip = n(lambda s: s.startswith("skip"))
    miss = n(lambda s: s.startswith("miss"))
    fail = n(lambda s: s.startswith("FAIL"))
    print(
        f"\nSUMMARY: ok={ok} skip={skip} miss(paywall/no-OA)={miss} "
        f"fail={fail}  total={len(results)}"
    )
    misses = sorted(i for k, i, s in results if s.startswith(("miss", "FAIL")))
    if misses:
        print("Not downloaded:\n  " + "\n  ".join(misses))
    write_manifest(results)
    print("wrote MANIFEST.md")
    write_not_downloaded(results)
    print("wrote not_downloaded_papers.md")
    from extract_text import extract_all  # sibling script: greppable text/ copies

    extract_all()
    return 0


def _cite_links(kind: str, ident: str) -> str:
    files = sorted(CITES.get(f"{kind}:{ident}", ()))
    return ", ".join(f"`{os.path.basename(f)}`" for f in files) or "—"


def write_manifest(results: list[tuple[str, str, str]]) -> None:
    """Emit MANIFEST.md documenting the harvested corpus.

    Lists every identifier, whether its PDF is present, the local filename, and which
    repo docs cite it. Tracked so the corpus is documented and reproducible.
    """
    have, missing = [], []
    for kind, ident, status in sorted(results, key=lambda r: (r[0], r[1])):
        present = status in ("ok", "skip (exists)")
        link = "https://arxiv.org/abs/" + ident if kind == "arxiv" else "https://doi.org/" + ident
        (have if present else missing).append((kind, ident, link, status))

    lines = [
        "# Paper corpus manifest",
        "",
        "Auto-generated by `fetch.py` from a repo-wide scan of cited arXiv IDs and DOIs.",
        "**Do not edit by hand** — re-run `python3 research/papers/fetch.py`. PDFs are",
        "gitignored; this manifest is tracked so the corpus is documented and reproducible.",
        "",
        "Titles are not restated here — follow the link, or see the citing doc(s).",
        "",
        f"## Present ({len(have)})",
        "",
        "| Identifier | File | Cited in |",
        "|---|---|---|",
    ]
    for kind, ident, link, _ in have:
        lines.append(
            f"| [{ident}]({link}) | `{filename_for(kind, ident)}` | {_cite_links(kind, ident)} |"
        )
    lines += [
        "",
        f"## Not downloaded ({len(missing)}) — paywalled or OA-but-bot-blocked",
        "",
        "Fetch these manually in a browser if needed (institutional access / the OA",
        "preprint host). bioRxiv and APS PhysRevX are open access but block automated",
        "fetches; the rest are subscription-only.",
        "",
        "| Identifier | Cited in |",
        "|---|---|",
    ]
    for kind, ident, link, _ in missing:
        lines.append(f"| [{ident}]({link}) | {_cite_links(kind, ident)} |")
    lines.append("")
    with open(os.path.join(HERE, "MANIFEST.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


META_CACHE = os.path.join(HERE, "meta_cache.json")


def _paper_meta(kind: str, ident: str, cache: dict[str, dict[str, str]]) -> dict[str, str]:
    """Return {title, oa_url} for a missing paper (Crossref title + Unpaywall OA landing page).

    Cached in meta_cache.json so re-runs don't re-query; lookups that fail stay blank.
    """
    key = f"{kind}:{ident}"
    if key in cache:
        return cache[key]
    meta = {"title": "", "oa_url": ""}
    if kind == "doi":
        try:
            url = "https://api.crossref.org/works/" + urllib.parse.quote(ident)
            cr = json.loads(_get(url, timeout=30))
            msg = cr.get("message", {})
            title = " ".join((msg.get("title") or [""])[0].split())
            year = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
            meta["title"] = f"{title} ({year})" if title and year else title
        except Exception:
            pass
        try:
            up = json.loads(
                _get(
                    f"https://api.unpaywall.org/v2/{urllib.parse.quote(ident)}"
                    f"?email={urllib.parse.quote(EMAIL)}",
                    timeout=30,
                )
            )
            loc = up.get("best_oa_location") or {}
            meta["oa_url"] = loc.get("url_for_pdf") or loc.get("url") or ""
        except Exception:
            pass
    if meta["title"]:
        cache[key] = meta
    return meta


def write_not_downloaded(results: list[tuple[str, str, str]]) -> None:
    """Emit not_downloaded_papers.md: every cited paper without a local PDF, with links.

    A to-do list for fetching by hand (browser / institutional access), each row naming
    the filename to save the PDF as so the next fetch.py run picks it up as present.
    """
    try:
        with open(META_CACHE, encoding="utf-8") as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = {}
    missing = sorted((k, i) for k, i, s in results if s not in ("ok", "skip (exists)"))
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        metas = list(ex.map(lambda ki: _paper_meta(ki[0], ki[1], cache), missing))
    with open(META_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=1, sort_keys=True)

    lines = [
        "# Cited papers not downloaded",
        "",
        "Auto-generated by `fetch.py` — **do not edit by hand**. Every paper cited in the repo",
        "that has no local PDF (paywalled, or open-access but blocking scripted downloads).",
        "To add one: open a link in a browser (institutional access or the OA copy), save",
        "the PDF into `research/papers/` under the **Save as** name, and re-run",
        "`python3 research/papers/fetch.py` — it then counts as present. Never use Sci-Hub.",
        "",
        f"**{len(missing)} missing.**",
        "",
        "| Paper | Link | Open-access copy | Save as | Cited in |",
        "|---|---|---|---|---|",
    ]
    for (kind, ident), meta in zip(missing, metas, strict=True):
        link = "https://arxiv.org/abs/" + ident if kind == "arxiv" else "https://doi.org/" + ident
        title = (meta.get("title") or "—").replace("|", "\\|")
        oa = f"[OA]({meta['oa_url']})" if meta.get("oa_url") else "—"
        lines.append(
            f"| {title} | [{ident}]({link}) | {oa} | `{filename_for(kind, ident)}` "
            f"| {_cite_links(kind, ident)} |"
        )
    lines.append("")
    with open(os.path.join(HERE, "not_downloaded_papers.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())

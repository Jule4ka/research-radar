"""Download open-access PDFs for the top-scoring papers.

Local convenience only: `python -m radar.main --download` saves every
OPEN-ACCESS paper scoring >= DOWNLOAD_MIN_SCORE into the papers/ folder (up to
DOWNLOAD_MAX). Closed-access papers are never downloaded. When a link turns out
to be a landing page rather than a direct PDF (or the publisher blocks the
fetch), we save a small `.link.txt` with the URL instead, best-effort.

Preprints are an exception to the score bar: in a few chosen areas (see
PREPRINT_TOPICS / PREPRINT_STREAMS in config) a preprint is saved even below
DOWNLOAD_MIN_SCORE, down to a light junk floor, so you catch the early work.

Not used by the unattended GitHub Actions run — that machine is wiped after each
run, so it can't hand you files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import requests

from .openalex import Paper

UA = "research-radar/0.1 (open-access PDF fetch)"


def _safe(name: str, n: int = 60) -> str:
    s = re.sub(r"[^\w\- ]", "", name).strip().replace(" ", "-")
    return (s[:n].rstrip("-") or "paper")


def _is_preprint(p: Paper) -> bool:
    return p.type == "preprint" or p.venue_type == "repository"


def _wanted(p: Paper, min_score: int, preprint_min_score: int,
            preprint_topics: Iterable[str], preprint_streams: Iterable[str]) -> bool:
    """Peer-reviewed work clears min_score everywhere; a preprint also qualifies
    (down to preprint_min_score) when it's in one of the chosen areas."""
    if p.score >= min_score:
        return True
    if (_is_preprint(p) and p.score >= preprint_min_score
            and (p.topic_id in preprint_topics or p.stream in preprint_streams)):
        return True
    return False


def download_oa(papers: list[Paper], out_dir: Path,
                min_score: int, max_n: int,
                preprint_min_score: int = 10 ** 9,
                preprint_topics: Iterable[str] = (),
                preprint_streams: Iterable[str] = ()) -> list[Paper]:
    """Download qualifying OA papers; set `local_path` on each. Returns them."""
    out_dir.mkdir(parents=True, exist_ok=True)
    preprint_topics = set(preprint_topics)
    preprint_streams = set(preprint_streams)
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA})

    got: list[Paper] = []
    for p in papers:
        if len(got) >= max_n:
            break
        if not p.is_oa or not p.pdf_url:
            continue
        if not _wanted(p, min_score, preprint_min_score,
                       preprint_topics, preprint_streams):
            continue

        stem = f"{p.date}__score{p.score}__{_safe(p.title)}__{p.short_id}"
        pdf_dest = out_dir / f"{stem}.pdf"
        if pdf_dest.exists():
            p.local_path = f"{out_dir.name}/{pdf_dest.name}"
            got.append(p)
            continue

        try:
            r = sess.get(p.pdf_url, timeout=60, allow_redirects=True)
            r.raise_for_status()
            data = r.content
            ctype = r.headers.get("content-type", "").lower()
            if data[:5] == b"%PDF-" or "application/pdf" in ctype:
                pdf_dest.write_bytes(data)
                p.local_path = f"{out_dir.name}/{pdf_dest.name}"
            else:
                link = out_dir / f"{stem}.link.txt"
                link.write_text(p.pdf_url + "\n", encoding="utf-8")
                p.local_path = f"{out_dir.name}/{link.name}"
            got.append(p)
        except Exception as e:  # best-effort — one failure shouldn't stop others
            print(f"[download] {p.short_id} failed: {e}")

    return got

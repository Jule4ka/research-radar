"""Thin OpenAlex client: query works per stream and normalise results.

OpenAlex needs no API key. Set the env var OPENALEX_MAILTO to an address you
choose to join the faster "polite pool" (optional). The address is read from the
environment only -- it is never hard-coded here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta

import requests

API = "https://api.openalex.org/works"
UA = "research-radar/0.1 (https://github.com/)"


@dataclass
class Paper:
    id: str
    title: str
    authors: list[str]
    abstract: str
    venue: str
    date: str
    doi: str
    url: str
    stream: str = ""
    score: int = 0

    @property
    def short_id(self) -> str:
        return self.id.rsplit("/", 1)[-1]


def _reconstruct_abstract(inverted: dict | None) -> str:
    if not inverted:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def _session() -> requests.Session:
    s = requests.Session()
    headers = {"User-Agent": UA}
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        headers["From"] = mailto  # polite-pool identification via header, not URL
    s.headers.update(headers)
    return s


def fetch_stream(stream, lookback_days: int, per_page: int) -> list[Paper]:
    """Return papers published within the lookback window for one stream."""
    since = (date.today() - timedelta(days=lookback_days)).isoformat()

    filters = [f"from_publication_date:{since}"]
    if stream.filter:
        filters.append(stream.filter)
    if stream.search:
        filters.append(f"title_and_abstract.search:{stream.search}")

    params = {
        "filter": ",".join(filters),
        "sort": "publication_date:desc",
        "per-page": per_page,
        "select": ("id,title,publication_date,doi,"
                   "authorships,primary_location,abstract_inverted_index"),
    }

    sess = _session()
    resp = sess.get(API, params=params, timeout=30)
    resp.raise_for_status()
    results = resp.json().get("results", [])

    papers: list[Paper] = []
    for w in results:
        loc = w.get("primary_location") or {}
        src = loc.get("source") or {}
        authors = [
            (a.get("author") or {}).get("display_name", "")
            for a in (w.get("authorships") or [])
        ]
        papers.append(Paper(
            id=w["id"],
            title=w.get("title") or "(untitled)",
            authors=[a for a in authors if a],
            abstract=_reconstruct_abstract(w.get("abstract_inverted_index")),
            venue=src.get("display_name") or "",
            date=w.get("publication_date") or "",
            doi=(w.get("doi") or "").replace("https://doi.org/", ""),
            url=loc.get("landing_page_url") or w["id"],
            stream=stream.key,
        ))
    return papers

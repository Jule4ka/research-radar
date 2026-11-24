"""Thin OpenAlex client: query works per stream and normalise results.

OpenAlex needs no API key. Set the env var OPENALEX_MAILTO to an address you
choose to join the faster "polite pool" (optional). The address is read from the
environment only -- it is never hard-coded here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, timedelta

import requests

API = "https://api.openalex.org/works"
UA = "research-radar/0.1 (personal research tool)"


@dataclass
class Paper:
    id: str
    title: str
    authors: list[str]
    author_ids: list[str] = field(default_factory=list)  # OpenAlex author ids
    abstract: str = ""
    venue: str = ""
    date: str = ""
    doi: str = ""
    url: str = ""
    stream: str = ""
    score: int = 0
    why: str = ""              # plain-language reason the paper scored as it did
    matched: str = ""          # why it was captured (which stream/filter caught it)
    type: str = ""             # OpenAlex work type (article, preprint, editorial…)
    is_oa: bool = False        # open access?
    oa_status: str = ""        # gold / green / hybrid / bronze / closed
    topic: str = ""            # the paper's own primary OpenAlex topic (name)
    topic_id: str = ""         # that topic's OpenAlex id, e.g. "T11147"
    topic_score: float = 0.0   # how confidently it fits that topic (0..1)
    venue_type: str = ""       # journal / conference / repository / book series…
    is_in_doaj: bool = False   # venue indexed in DOAJ (a peer-review signal)
    refs_count: int = 0        # number of works it cites (scholarly substance)
    cited_by_count: int = 0    # times this work has been cited (impact)
    pdf_url: str = ""          # best free PDF/landing url (OA only)
    local_path: str = ""       # set once the PDF is downloaded locally

    @property
    def short_id(self) -> str:
        return self.id.rsplit("/", 1)[-1]

    @property
    def doi_url(self) -> str:
        return f"https://doi.org/{self.doi}" if self.doi else ""


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
    api_key = os.environ.get("OPENALEX_API_KEY")
    if api_key:
        # A personal key has its own budget, so you don't share the IP-wide
        # free pool. Sent as a header (never in the URL / logs).
        headers["Authorization"] = f"Bearer {api_key}"
    s.headers.update(headers)
    return s


def fetch_stream(stream, lookback_days: int | None, per_page: int,
                 sort: str = "publication_date:desc") -> list[Paper]:
    """Query one stream. With lookback_days set, restrict to that recent window
    (the fresh-news mode); pass None for no date filter (e.g. all-time canon).
    `sort` is an OpenAlex sort key, e.g. "cited_by_count:desc" for most-cited."""
    filters = []
    if lookback_days is not None:
        since = (date.today() - timedelta(days=lookback_days)).isoformat()
        filters.append(f"from_publication_date:{since}")
    if stream.filter:
        filters.append(stream.filter)
    if stream.search:
        filters.append(f"title_and_abstract.search:{stream.search}")

    params = {
        "filter": ",".join(filters),
        "sort": sort,
        "per-page": per_page,
        "select": ("id,title,publication_date,doi,type,referenced_works_count,"
                   "cited_by_count,authorships,primary_location,best_oa_location,"
                   "primary_topic,open_access,abstract_inverted_index"),
    }

    sess = _session()
    resp = sess.get(API, params=params, timeout=30)
    resp.raise_for_status()
    results = resp.json().get("results", [])

    papers: list[Paper] = []
    for w in results:
        loc = w.get("primary_location") or {}
        src = loc.get("source") or {}
        oa = w.get("open_access") or {}
        bol = w.get("best_oa_location") or {}
        topic = w.get("primary_topic") or {}
        authorships = w.get("authorships") or []
        authors = [
            (a.get("author") or {}).get("display_name", "")
            for a in authorships
        ]
        author_ids = [
            ((a.get("author") or {}).get("id") or "").rsplit("/", 1)[-1]
            for a in authorships
        ]
        papers.append(Paper(
            id=w["id"],
            title=w.get("title") or "(untitled)",
            authors=[a for a in authors if a],
            author_ids=[a for a in author_ids if a],
            abstract=_reconstruct_abstract(w.get("abstract_inverted_index")),
            venue=src.get("display_name") or "",
            date=w.get("publication_date") or "",
            doi=(w.get("doi") or "").replace("https://doi.org/", ""),
            url=loc.get("landing_page_url") or w["id"],
            stream=stream.key,
            type=w.get("type") or "",
            is_oa=bool(oa.get("is_oa")),
            oa_status=oa.get("oa_status") or "",
            topic=(topic.get("display_name") or "") if topic else "",
            topic_id=((topic.get("id") or "").rsplit("/", 1)[-1]) if topic else "",
            topic_score=float(topic.get("score") or 0.0) if topic else 0.0,
            venue_type=src.get("type") or "",
            is_in_doaj=bool(src.get("is_in_doaj")),
            refs_count=int(w.get("referenced_works_count") or 0),
            cited_by_count=int(w.get("cited_by_count") or 0),
            pdf_url=(bol.get("pdf_url") or loc.get("pdf_url")
                     or oa.get("oa_url") or ""),
        ))
    return papers

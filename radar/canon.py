"""Reading list of the most-cited papers per topic (the "impact" view).

Separate from the fresh-news pipeline in main.py. Freshness asks "what's new?";
this asks "what does the field actually lean on?". Because these papers already
have citations, we rank by citations directly instead of the birth-time quality
proxies used for brand-new work. Two lists per topic:

  * All-time canon  — ranked by total citations (foundational reading).
  * Rising          — last RISING_SINCE_YEARS, ranked by citations-PER-YEAR, so
                      a fast-climbing 2024 paper isn't buried under a 2010 one.

Run with `python -m radar.main --canon`. Output goes to CANON_OUT. It isn't
drafted and isn't deduped — it's a reference doc you regenerate when you like.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from . import config
from .deliver import _access, _authors, _cell, _doi
from .openalex import Paper, fetch_stream

OUT = Path(__file__).resolve().parent.parent / config.CANON_OUT


def _year(p: Paper) -> int:
    try:
        return int((p.date or "")[:4])
    except ValueError:
        return 0


def _per_year(p: Paper) -> float:
    """Citations per year since publication (age floored at 1 year)."""
    yr = _year(p)
    if yr <= 0:
        return 0.0
    age = max(1, date.today().year - yr)
    return p.cited_by_count / age


def _topic_stream(tid: str, name: str):
    # A lightweight Stream for fetch_stream (same shape as a topic stream).
    return config.Stream(key=f"topic_{tid}", label=name, filter=f"topics.id:{tid}")


def _canon_rows(papers: list[Paper]) -> list[str]:
    rows = ["| Citations | Year | Title | Authors | Venue | Access | DOI |",
            "|---:|---:|---|---|---|---|---|"]
    for p in papers:
        rows.append(
            f"| {p.cited_by_count} | {_year(p) or '—'} "
            f"| [{_cell(p.title)}]({p.url}) | {_cell(_authors(p))} "
            f"| {_cell(p.venue) or '—'} | {_access(p)} | {_doi(p)} |"
        )
    return rows


def _rising_rows(papers: list[Paper]) -> list[str]:
    rows = ["| Cites/yr | Citations | Year | Title | Authors | Venue | Access | DOI |",
            "|---:|---:|---:|---|---|---|---|---|"]
    for p in papers:
        rows.append(
            f"| {_per_year(p):.1f} | {p.cited_by_count} | {_year(p) or '—'} "
            f"| [{_cell(p.title)}]({p.url}) | {_cell(_authors(p))} "
            f"| {_cell(p.venue) or '—'} | {_access(p)} | {_doi(p)} |"
        )
    return rows


def build_reading_list() -> str:
    today = date.today().isoformat()
    lines = [
        f"# Research Radar — Reading list (most-cited) — {today}",
        "",
        "Ranked by **impact**, not freshness. **Canon** = most cited all-time; "
        f"**Rising** = last {config.RISING_SINCE_YEARS} years by citations/year.",
        "",
    ]

    for tid in config.CANON_TOPIC_IDS:
        name = config.TOPICS.get(tid, tid)
        stream = _topic_stream(tid, name)
        lines += [f"## {name} (`{tid}`)", ""]

        try:
            canon = fetch_stream(stream, None, config.CANON_PER_TOPIC,
                                 sort="cited_by_count:desc")
        except Exception as e:
            lines += [f"_canon fetch failed: {e}_", ""]
            canon = []
        if canon:
            lines += ["### \U0001F3DB️ All-time canon", ""]
            lines += _canon_rows(canon)
            lines.append("")

        try:
            # Pull a wider pool by total citations, then re-rank by per-year.
            pool = fetch_stream(stream, config.RISING_SINCE_YEARS * 365,
                                config.RISING_PER_TOPIC * 4,
                                sort="cited_by_count:desc")
        except Exception as e:
            lines += [f"_rising fetch failed: {e}_", ""]
            pool = []
        if pool:
            pool.sort(key=_per_year, reverse=True)
            rising = pool[:config.RISING_PER_TOPIC]
            lines += [f"### \U0001F4C8 Rising (last {config.RISING_SINCE_YEARS} years)", ""]
            lines += _rising_rows(rising)
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def write_file(markdown: str) -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(markdown, encoding="utf-8")
    return OUT


def run() -> Path:
    md = build_reading_list()
    path = write_file(md)
    print(f"[radar] reading list written to {config.CANON_OUT} "
          f"({len(config.CANON_TOPIC_IDS)} topic(s))")
    return path

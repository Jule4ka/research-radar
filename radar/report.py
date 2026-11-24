"""Render papers into Markdown: the fresh-run report and the --canon reading list.

Two outputs, one place:
  * render() / write_report()         -> state/latest_report.md (drafts + digest)
  * build_reading_list() / canon_run() -> state/reading_list.md (most-cited)

Plus make_draft() (Paper -> LinkedIn post template) and the small cell/authors/
access/doi helpers both reports share.
"""

from __future__ import annotations

import textwrap
from datetime import date
from pathlib import Path

from . import config
from .openalex import Paper, fetch_stream

_STATE = Path(__file__).resolve().parent.parent / "state"
REPORT_OUT = _STATE / "latest_report.md"
READING_OUT = Path(__file__).resolve().parent.parent / config.CANON_OUT

_STREAM_LABELS = {s.key: s.label for s in config.STREAMS}


# --- Markdown cell helpers ---------------------------------------------------

def cell(text: str) -> str:
    """Make a string safe to drop into a Markdown table cell."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def authors(p: Paper, n: int = 3) -> str:
    shown = ", ".join(p.authors[:n])
    return shown + (" et al." if len(p.authors) > n else "")


def access(p: Paper) -> str:
    label = f"🔓 {p.oa_status or 'open'}" if p.is_oa else "🔒 closed"
    if p.local_path:
        label += f" · [📥 saved]({p.local_path})"
    return label


def doi(p: Paper) -> str:
    return f"[{cell(p.doi)}]({p.doi_url})" if p.doi else "—"


def _matched(p: Paper) -> str:
    return _STREAM_LABELS.get(p.stream, p.stream)


# --- LinkedIn draft ----------------------------------------------------------

DEFAULT_TAGS = "#Research #AcademicResearch #OpenAlex"

# Hashtags per stream key; anything not listed falls back to DEFAULT_TAGS.
HASHTAGS = {
    "conceptual_modelling": "#ConceptualModeling #DataModeling #Ontology",
    "cognitive_warfare": "#CognitiveWarfare #InformationWarfare #CognitiveSecurity",
    "topic_T10215": "#SemanticWeb #KnowledgeGraph #LinkedData",
    "topic_T11450": "#ModelDrivenEngineering #MDE #ConceptualModeling",
    "topic_T11147": "#Disinformation #InformationIntegrity #MediaLiteracy",
    "topic_T12221": "#Cybersecurity #CyberWarfare #InfoSec",
    "topic_T13369": "#RussiaStudies #Geopolitics #StrategicStudies",
}


def _trim(text: str, words: int = 55) -> str:
    parts = text.split()
    return " ".join(parts[:words]) + ("…" if len(parts) > words else "")


def make_draft(paper: Paper) -> str:
    who = ", ".join(paper.authors[:3]) + (" et al." if len(paper.authors) > 3 else "")
    venue = f" ({paper.venue})" if paper.venue else ""
    summary = _trim(paper.abstract) if paper.abstract else "New paper worth a look."
    tags = HASHTAGS.get(paper.stream, DEFAULT_TAGS)
    return textwrap.dedent(f"""\
        \U0001F4C4 New paper: "{paper.title}"
        {who}{venue} — {paper.date}

        {summary}

        Why it matters: [add your one-line take here]

        \U0001F517 {paper.url}

        {tags}""").rstrip()


# --- Fresh-run report --------------------------------------------------------

def render(drafts: list[tuple[Paper, str]], digest: list[Paper]) -> str:
    today = date.today().isoformat()
    lines: list[str] = [f"# Research Radar — {today}", ""]

    if not drafts and not digest:
        lines.append("_No new papers this run._")
        return "\n".join(lines)

    lines.append(f"**{len(drafts)} draft(s) ready to post** · "
                 f"{len(digest)} more new paper(s) in the digest below.")
    lines.append("")

    for i, (paper, text) in enumerate(drafts, 1):
        topic = f" · {cell(paper.topic)}" if paper.topic else ""
        matched = f" · {cell(_matched(paper))}" if paper.stream else ""
        caught = paper.matched or f"From your watchlist: {_matched(paper)}."
        lines += [
            f"## ✍️ Draft {i} — score {paper.score}{matched}",
            "",
            f"> **Captured because:** {caught}",
            ">",
            f"> **Why picked:** {paper.why}",
            "",
            "```",
            text,
            "```",
            "",
            f"<sub>{paper.date} · {access(paper)} · {cell(paper.venue)}{topic}"
            + (f" · doi:{paper.doi}" if paper.doi else "")
            + f" · [link]({paper.url})</sub>",
            "",
            "---",
            "",
        ]

    if digest:
        shown = digest[:config.DIGEST_MAX]
        hidden = len(digest) - len(shown)
        lines += [
            "## \U0001F4F0 Also new (digest)",
            "",
            "| Date | Access | Score | Title | Authors "
            "| Captured because | Topic | DOI | Why |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for p in shown:
            lines.append(
                f"| {p.date} | {access(p)} | {p.score} "
                f"| [{cell(p.title)}]({p.url}) | {cell(authors(p))} "
                f"| {cell(p.matched) or '—'} "
                f"| {cell(p.topic) or '—'} | {doi(p)} | {cell(p.why)} |"
            )
        lines.append("")
        if hidden > 0:
            lines += [
                f"_…and {hidden} more new paper(s) not shown "
                f"(digest capped at {config.DIGEST_MAX}, highest score first). "
                f"Raise `MIN_SCORE` or shorten `LOOKBACK_DAYS` to trim._",
                "",
            ]

    lines += ["---", "_Paste the drafts you like into LinkedIn, then close this issue._"]
    return "\n".join(lines)


def write_report(markdown: str) -> Path:
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(markdown, encoding="utf-8")
    return REPORT_OUT


# --- Reading list: most-cited papers (--canon) -------------------------------

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
    return p.cited_by_count / max(1, date.today().year - yr)


def _cited_rows(papers: list[Paper], rising: bool) -> list[str]:
    if rising:
        rows = ["| Cites/yr | Citations | Year | Title | Authors | Venue | Access | DOI |",
                "|---:|---:|---:|---|---|---|---|---|"]
    else:
        rows = ["| Citations | Year | Title | Authors | Venue | Access | DOI |",
                "|---:|---:|---|---|---|---|---|"]
    for p in papers:
        lead = f"| {_per_year(p):.1f} " if rising else "| "
        rows.append(
            f"{lead}| {p.cited_by_count} | {_year(p) or '—'} "
            f"| [{cell(p.title)}]({p.url}) | {cell(authors(p))} "
            f"| {cell(p.venue) or '—'} | {access(p)} | {doi(p)} |"
        )
    return rows


def build_reading_list() -> str:
    lines = [
        f"# Research Radar — Reading list (most-cited) — {date.today().isoformat()}",
        "",
        "Ranked by **impact**, not freshness. **Canon** = most cited all-time; "
        f"**Rising** = last {config.RISING_SINCE_YEARS} years by citations/year.",
        "",
    ]
    for tid in config.CANON_TOPIC_IDS:
        name = config.TOPICS.get(tid, tid)
        stream = config.Stream(key=f"topic_{tid}", label=name, filter=f"topics.id:{tid}")
        lines += [f"## {name} (`{tid}`)", ""]

        try:
            canon = fetch_stream(stream, None, config.CANON_PER_TOPIC,
                                 sort="cited_by_count:desc")
        except Exception as e:
            lines += [f"_canon fetch failed: {e}_", ""]
            canon = []
        if canon:
            lines += ["### \U0001F3DB️ All-time canon", "", *_cited_rows(canon, False), ""]

        try:
            pool = fetch_stream(stream, config.RISING_SINCE_YEARS * 365,
                                config.RISING_PER_TOPIC * 4, sort="cited_by_count:desc")
        except Exception as e:
            lines += [f"_rising fetch failed: {e}_", ""]
            pool = []
        if pool:
            pool.sort(key=_per_year, reverse=True)
            rising = pool[:config.RISING_PER_TOPIC]
            lines += [f"### \U0001F4C8 Rising (last {config.RISING_SINCE_YEARS} years)",
                      "", *_cited_rows(rising, True), ""]

        lines += ["---", ""]
    return "\n".join(lines)


def canon_run() -> Path:
    READING_OUT.parent.mkdir(parents=True, exist_ok=True)
    READING_OUT.write_text(build_reading_list(), encoding="utf-8")
    print(f"[radar] reading list written to {config.CANON_OUT} "
          f"({len(config.CANON_TOPIC_IDS)} topic(s))")
    return READING_OUT

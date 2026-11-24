"""Render the run's findings into a Markdown review doc.

The workflow turns this Markdown into a GitHub Issue (via `gh issue create
--body-file`). Running locally, it just writes a file you can open.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from . import config
from .openalex import Paper

OUT = Path(__file__).resolve().parent.parent / "state" / "latest_report.md"

# stream key -> human label, so a pick can show which watched stream surfaced it
# (e.g. "Management and Organizational Studies") rather than only OpenAlex's own
# per-paper primary topic.
_STREAM_LABELS = {s.key: s.label for s in config.STREAMS}


def _matched(p: Paper) -> str:
    return _STREAM_LABELS.get(p.stream, p.stream)


def _cell(text: str) -> str:
    """Make a string safe to drop into a Markdown table cell."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def _authors(p: Paper, n: int = 3) -> str:
    shown = ", ".join(p.authors[:n])
    return shown + (" et al." if len(p.authors) > n else "")


def _access(p: Paper) -> str:
    if p.is_oa:
        label = p.oa_status or "open"
        access = f"🔓 {label}"
    else:
        access = "🔒 closed"
    if p.local_path:
        access += f" · [📥 saved]({p.local_path})"
    return access


def _doi(p: Paper) -> str:
    return f"[{_cell(p.doi)}]({p.doi_url})" if p.doi else "—"


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
        access = _access(paper)
        topic = f" · {_cell(paper.topic)}" if paper.topic else ""
        matched = f" · {_cell(_matched(paper))}" if paper.stream else ""
        lines += [
            f"## ✍️ Draft {i} — score {paper.score}{matched}",
            "",
            f"> **Why picked:** {paper.why}",
            "",
            "```",
            text,
            "```",
            "",
            f"<sub>{paper.date} · {access} · {_cell(paper.venue)}{topic}"
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
            "| Date | Access | Score | Title | Authors | Topic | DOI | Why |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for p in shown:
            lines.append(
                f"| {p.date} | {_access(p)} | {p.score} "
                f"| [{_cell(p.title)}]({p.url}) | {_cell(_authors(p))} "
                f"| {_cell(p.topic) or '—'} | {_doi(p)} | {_cell(p.why)} |"
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


def write_file(markdown: str) -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(markdown, encoding="utf-8")
    return OUT
